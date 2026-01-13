import streamlit as st
import pandas as pd
from io import BytesIO
from backend.db import feedbacks, global_issues, db
from backend.auth import authenticate_user, create_user, users_collection

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Admin Dashboard", page_icon="🔒", layout="wide")

# Custom CSS (Your existing style)
st.markdown("""
    <style>
    .stButton>button {width: 100%;}
    div[data-testid="stExpander"] {border: 1px solid #ddd; border-radius: 5px;}
    .stMetric {background-color: #f0f2f6; padding: 15px; border-radius: 10px;}
    </style>
    """, unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user_info"] = {}

# =====================================================
# 🔐 LOGIN SCREEN
# =====================================================
if not st.session_state["authenticated"]:
    st.title("🔐 Admin Login Portal")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.subheader("Please Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                user = authenticate_user(username, password)
                if user:
                    st.session_state["authenticated"] = True
                    st.session_state["user_info"] = user
                    st.rerun()
                else:
                    st.error("❌ Invalid Username or Password")
    st.stop()

# =====================================================
# 👤 LOGGED IN DASHBOARD
# =====================================================
user = st.session_state["user_info"]
role = user["role"]
access_districts = user["access"]
user_category = user.get("role_category", "All Categories") # <--- NEW: Get User Dept

# --- SIDEBAR ---
with st.sidebar:
    st.write(f"👤 **{user['username']}**")
    st.caption(f"Role: {role.upper()}")
    st.caption(f"Dept: {user_category}") # Show Dept
    if role == "admin":
        st.caption(f"Access: {', '.join(access_districts)}")
    
    if st.button("🚪 Logout"):
        st.session_state["authenticated"] = False
        st.rerun()

st.title(f"📊 Dashboard ({user_category})")

# =====================================================
# 👮 SUPER ADMIN PANEL (With New Role Feature)
# =====================================================
if role == "super_admin":
    st.markdown("### 👮 Super Admin Controls")
    
    with st.container(border=True):
        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.subheader("➕ Create New Sub-Admin")
            
            new_user = st.text_input("Username", key="new_user_input")
            new_pass = st.text_input("Password", type="password", key="new_pass_input")
            new_email = st.text_input("Email ID", key="new_email_input")
            
            # 1. District Selection
            all_locs = feedbacks.distinct("location.district")
            all_districts = sorted([d for d in all_locs if d])
            selected_access = st.multiselect("Assign Districts", all_districts, key="new_access_input")

            # 2. Role/Department Selection (NEW)
            categories = ["All Categories", "Water", "Sanitation", "Road", "Electricity", "Health", "Transport", "Safety"]
            selected_category = st.selectbox("Assign Department", categories, key="new_role_input")
            
            if st.button("Create Admin & Send Email", key="create_admin_btn"):
                if new_user and new_pass and selected_access and new_email:
                    # Pass Role Category here
                    success, msg = create_user(
                        new_user, new_pass, new_email, 
                        role="admin", 
                        assigned_districts=selected_access,
                        role_category=selected_category
                    )
                    
                    if "Email sent" in msg:
                        st.success(msg)
                    else:
                        st.warning(msg)
                else:
                    st.error("⚠️ Please fill all details.")

        # admin.py inside 'if role == "super_admin":' block

        # --- RIGHT SIDE: MANAGE EXISTING ADMINS ---
        with c2:
            st.subheader("📋 Manage Admins")
            
            # 1. Import new functions
            from backend.auth import update_admin_access, delete_admin
            
            # 2. Fetch Admins
            admins = list(users_collection.find({"role": "admin"}))
            
            if not admins:
                st.info("No sub-admins found.")
            else:
                # 3. List each admin with controls
                for i, admin in enumerate(admins):
                    u_name = admin['username']
                    u_role = admin.get('role_category', 'All')
                    u_access = admin.get('access', [])
                    
                    # Create an Expander for each user
                    with st.expander(f"👤 {u_name} ({u_role})"):
                        
                        # --- EDIT SECTION ---
                        st.write("#### ✏️ Update Access")
                        
                        # District Selector (Pre-filled with current access)
                        all_locs = feedbacks.distinct("location.district")
                        all_districts = sorted([d for d in all_locs if d])
                        
                        new_districts = st.multiselect(
                            "Update Districts", 
                            options=all_districts, 
                            default=[d for d in u_access if d in all_districts],
                            key=f"dist_{u_name}"
                        )
                        
                        # Role Selector (Pre-filled)
                        categories = ["All Categories", "Water", "Sanitation", "Road", "Electricity", "Health", "Transport", "Safety"]
                        current_index = categories.index(u_role) if u_role in categories else 0
                        
                        new_role = st.selectbox(
                            "Update Dept", 
                            options=categories, 
                            index=current_index,
                            key=f"role_{u_name}"
                        )
                        
                        # Update Button
                        if st.button("💾 Save Changes", key=f"save_{u_name}"):
                            success, msg = update_admin_access(u_name, new_districts, new_role)
                            if success:
                                st.success(msg)
                                st.rerun() # Reload page to show changes
                            else:
                                st.error(msg)
                        
                        st.markdown("---")
                        
                        # --- DELETE SECTION ---
                        st.write("#### 🗑️ Delete User")
                        if st.button(f"Delete {u_name}?", key=f"del_{u_name}", type="primary"):
                            success, msg = delete_admin(u_name)
                            if success:
                                st.success(msg)
                                st.rerun() # Reload page
                            else:
                                st.error(msg)
st.markdown("---")

# =====================================================
# 🌍 DATA FILTERING LOGIC
# =====================================================
raw_data = list(feedbacks.find().sort("created_at", -1))

# 1. Filter by District
if role == "super_admin":
    all_data = raw_data
else:
    all_data = [d for d in raw_data if d.get("location", {}).get("district") in access_districts]

# 2. Filter by Department Role (NEW)
# If user is "Water", only show Water issues.
if role != "super_admin" and user_category != "All Categories":
    all_data = [d for d in all_data if d.get("ai", {}).get("category") == user_category]

# Analyzed vs Pending
analyzed_feedbacks = [fb for fb in all_data if fb.get("ai")]

total_received = len(all_data)
total_analyzed = len(analyzed_feedbacks)
pending_count = total_received - total_analyzed

# =====================================================
# DASHBOARD UI (UNCHANGED)
# =====================================================

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="📢 Total Reports", value=total_received)
with col2:
    st.metric(label="✅ Verified & Processed", value=total_analyzed)
with col3:
    st.metric(label="⏳ Pending", value=pending_count)

st.markdown("---")

st.subheader("🔥 Top Critical Issues (AI Merged)")

all_issues = list(global_issues.find())
filtered_issues = []

# Filter Global Issues visually based on access
relevant_keys = set([f"{fb['ai']['category']}_{fb['ai']['main_issue']}".replace(" ", "_").lower() for fb in analyzed_feedbacks])

for issue in all_issues:
    if issue["issue_key"] in relevant_keys:
        filtered_issues.append(issue)

if not filtered_issues:
    st.info("✅ No critical issues found in your jurisdiction.")
else:
    priority_map = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    filtered_issues.sort(key=lambda x: (priority_map.get(x.get("priority", "LOW"), 1), x.get("total_reports", 0)), reverse=True)

    for issue in filtered_issues:
        name = issue.get("issue_text", "Unknown")
        count = issue.get("total_reports", 0)
        prio = issue.get("priority", "LOW")

        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                icon = "🚨" if prio == "CRITICAL" else "🟠" if prio == "HIGH" else "🔵"
                st.markdown(f"### {icon} {name}")
                users = issue.get("users", [])
                user_names = ", ".join([u.get('name', 'Unknown') for u in users[-3:]])
                st.caption(f"Affected Users: {user_names} ...")
            with c2:
                st.metric("Reports", count)
                st.caption(f"Priority: {prio}")

st.markdown("---")

if st.checkbox("📂 Click to Show Detailed Data & Download"):
    st.subheader("📋 District-wise Feedback Data")

    if not analyzed_feedbacks:
        st.warning("No verified data available yet.")
    else:
        rows = []
        for fb in analyzed_feedbacks:
            user = fb.get("user", {})
            location = fb.get("location", {})
            ai = fb.get("ai", {})

            rows.append({
                "Name": user.get("name", "N/A"),
                "District": location.get("district", "N/A"),
                "Category": ai.get("category", "N/A"),
                "Priority": ai.get("priority", "N/A"),
                "Issue": ai.get("main_issue", "N/A"),
                "Feedback": fb.get("feedback", {}).get("original_text", ""),
                "Date": fb.get("created_at", "")
            })

        df = pd.DataFrame(rows)

        col_f1, col_f2 = st.columns([3, 1])
        with col_f1:
            districts = sorted(df["District"].unique().tolist())
            selected_district = st.selectbox("Filter by District:", ["All Districts"] + districts)

        if selected_district != "All Districts":
            filtered_df = df[df["District"] == selected_district]
        else:
            filtered_df = df

        def convert_df_to_excel(dataframe):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                dataframe.to_excel(writer, index=False, sheet_name="Feedbacks")
            return output.getvalue()
        
        excel_data = convert_df_to_excel(filtered_df)

        with col_f2:
            st.write("")
            st.write("")
            st.download_button(
                label="⬇️ Download Excel",
                data=excel_data,
                file_name=f"report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        
        st.write("### 🗂️ Individual Feedback Analysis")
        for fb in analyzed_feedbacks:
            if selected_district != "All Districts" and fb.get("location", {}).get("district") != selected_district:
                continue
                
            ai = fb.get("ai", {})
            p_emoji = "🔴" if ai.get("priority") == "CRITICAL" else "🟠" if ai.get("priority") == "HIGH" else "🔵"
            
            with st.expander(f"{p_emoji} {fb.get('location', {}).get('district')} - {ai.get('main_issue', 'Issue')}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**User:** {fb.get('user', {}).get('name')}")
                    st.info(fb.get("feedback", {}).get("original_text"))
                with c2:
                    st.success(f"**Issue:** {ai.get('main_issue')}")
                    st.write(f"**Summary:** {ai.get('summary')}")