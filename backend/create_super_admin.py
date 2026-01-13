# File: create_super_admin.py
from backend.auth import create_user

# Create Super Admin
success, msg = create_user("superadmin", "admin123", role="super_admin", assigned_districts=["ALL"])
print(msg)