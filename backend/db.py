from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get MongoDB URI
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")

# Debug print (you can remove later)
print("DEBUG: MONGODB_URI =", MONGODB_URI)

# Connect to MongoDB
client = MongoClient(MONGODB_URI)

db = client["feedback_ai_db"]
collection = db["feedbacks"]

from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get MongoDB URI
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")

print("DEBUG: MONGODB_URI =", MONGODB_URI)

# Connect to MongoDB
client = MongoClient(MONGODB_URI)

db = client["feedback_ai_db"]


# Collections
feedbacks = db["feedbacks"]              # user submitted feedback
batches = db["batches"]                  # batch tracking (15 limit)
analysis_results = db["analysis_results"]# AI analysis output
global_issues = db["global_issues"]
