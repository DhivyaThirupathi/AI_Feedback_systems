import bcrypt
from backend.db import db, feedbacks # Import feedbacks collection
from backend.email_sender import send_credentials_email 

users_collection = db["users"]

def create_user(username, password, email, role="admin", assigned_districts=[], role_category="All"):
    
    if users_collection.find_one({"username": username}):
        return False, "User already exists"

    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    user_doc = {
        "username": username,
        "password": hashed_pw,
        "email": email,
        "role": role,
        "access": assigned_districts,
        "role_category": role_category  # <--- SAVE CATEGORY (e.g. "Water")
    }
    users_collection.insert_one(user_doc)
    
    # 🔥 FETCH EXISTING ISSUES FOR THIS ROLE TO SEND IN EMAIL
    query = {}
    
    # Filter by District
    if "All" not in assigned_districts:
        query["location.district"] = {"$in": assigned_districts}
    
    # Filter by Category (e.g., Water)
    if role_category != "All Categories":
        query["ai.category"] = role_category

    # Get top 5 critical issues
    existing_issues = list(feedbacks.find(query).sort("ai.priority", -1).limit(5))
    
    # SEND EMAIL WITH ISSUES
    email_success, email_msg = send_credentials_email(email, username, password, assigned_districts, role_category, existing_issues)
    
    if email_success:
        return True, f"User created & {len(existing_issues)} issues sent to email ✅"
    else:
        return True, f"User created but Email Failed ⚠️: {email_msg}"

def authenticate_user(username, password):
    user = users_collection.find_one({"username": username})
    if user and bcrypt.checkpw(password.encode('utf-8'), user["password"]):
        return user
    return None
# backend/auth.py

# ... (Mela ulla create_user, authenticate_user code apdiye irukkattum)

# 👇 NEW: UPDATE ADMIN ACCESS
def update_admin_access(username, new_districts, new_role_category):
    try:
        users_collection.update_one(
            {"username": username},
            {"$set": {"access": new_districts, "role_category": new_role_category}}
        )
        return True, "✅ Access updated successfully!"
    except Exception as e:
        return False, f"⚠️ Error updating: {str(e)}"

# 👇 NEW: DELETE ADMIN
def delete_admin(username):
    try:
        users_collection.delete_one({"username": username})
        return True, "🗑️ Admin deleted successfully!"
    except Exception as e:
        return False, f"⚠️ Error deleting: {str(e)}"