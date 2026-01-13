import streamlit as st
import json
import os
from backend.feedback_service import process_feedback

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Feedback Portal", layout="centered")
st.title("📝 Feedback Portal")

# ---------------- LOAD TN DATA ----------------
@st.cache_data
def load_tn_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "TN_Assembly_Constituencies_FULL.json")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

TN_DATA = load_tn_data()
districts = sorted(TN_DATA.keys())

# ---------------- LOCATION (OUTSIDE FORM - IMPORTANT) ----------------

st.subheader("📍 Location")

district = st.selectbox(
    "District *",
    districts,
    index=None,
    placeholder="Select District"
)

if district:
    constituency_list = [c["en"] for c in TN_DATA[district]["constituencies"]]
else:
    constituency_list = []

constituency = st.selectbox(
    "Assembly Constituency *",
    constituency_list,
    index=None,
    placeholder="Select Constituency"
)

# ---------------- FORM START ----------------
with st.form("feedback_form"):

    # ---------- PERSONAL DETAILS ----------
    st.subheader("👤 Personal Details")

    name = st.text_input("Name (optional)")
    age = st.number_input("Age", min_value=1, max_value=120, value=18)
    booth_no = st.text_input("Booth Number *")

    # ---------- FEEDBACK DETAILS ----------
    st.subheader("🗂️ Feedback Details")

    feedback_type = st.selectbox(
        "Type of Feedback *",
        ["General feedback", "State policy", "Services", "Complaint"]
    )

    email = st.text_input("Email (optional)")
    rating = st.slider("Rating (1–5)", 1, 5, 3)
    feedback_text = st.text_area("Your Feedback *", height=140)
    solution = st.text_area("Suggested Solution (optional)", height=100)

    submitted = st.form_submit_button("Submit Feedback")

# ---------------- SUBMIT HANDLER ----------------
if submitted:
    if not district:
        st.warning("⚠️ Please select District")
    elif not constituency:
        st.warning("⚠️ Please select Assembly Constituency")
    elif not booth_no.strip():
        st.warning("⚠️ Please enter Booth Number")
    elif not feedback_text.strip():
        st.warning("⚠️ Please enter your Feedback")
    else:
        with st.spinner("Processing feedback..."):
            process_feedback({
                "district": district,
                "constituency": constituency,
                "name": name,
                "age": age,
                "booth_no": booth_no,
                "email": email,
                "type_of_feedback": feedback_type,
                "rating": rating,
                "feedback_text": feedback_text,
                "solution": solution
            })

        st.success("✅ Feedback submitted successfully!")
