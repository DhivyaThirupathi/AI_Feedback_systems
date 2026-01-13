import streamlit as st
from dotenv import load_dotenv
import os
import json
from openai import OpenAI
from pymongo import MongoClient
from datetime import datetime, timezone
import hashlib

# ---------------- LOAD ENV ----------------
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

mongo_client = MongoClient(os.getenv("MONGODB_URI"))
db = mongo_client["feedback_db"]
collection = db["feedback_logs"]

# ---------------- TEXT CLEANING ----------------
def normalize_input(text):
    return " ".join(text.lower().strip().split())

# ---------------- PRIORITY MAPPING ----------------
def map_priority(confidence):
    return {
        "high": "High",
        "medium": "Medium",
        "low": "Low"
    }.get(confidence, "Low")

# ---------------- TEAM ROUTING ----------------
def assign_team(area):
    area = area.lower()
    if "frontend" in area or "ui" in area:
        return "UI Team"
    elif "backend" in area or "server" in area:
        return "Backend Team"
    elif "security" in area or "privacy" in area:
        return "Security Team"
    elif "political" in area or "policy" in area:
        return "Compliance Team"
    else:
        return "Support Team"

# ---------------- SYSTEM MESSAGE ----------------
def get_default_message(priority):
    if priority == "High":
        return "Thank you for your feedback. This issue has been marked as high priority."
    elif priority == "Medium":
        return "We received your feedback and will review it shortly."
    else:
        return "Thanks for reporting. Please provide more details if possible."

def get_followup_question(priority):
    if priority == "Low":
        return (
            "Could you please provide more details such as "
            "what exactly is not working, when the issue occurs, "
            "or any error message you see?"
        )
    return None

# ---------------- DUPLICATE CHECK ----------------
def generate_hash(text):
    return hashlib.md5(text.encode()).hexdigest()

def is_duplicate(feedback_hash):
    return collection.find_one({"feedback_hash": feedback_hash}) is not None

# ---------------- AI ANALYSIS ----------------
def analyze_feedback(feedback_text):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
You are an AI feedback analysis system.
Return ONLY valid JSON.
Classify emotion as one of:
frustration, anger, confusion, concern, neutral, satisfaction.
"""
            },
            {
                "role": "user",
                "content": f"""
{{
  "summary": "...",
  "main_issue": "...",
  "category": "Technical / Political / Privacy / Payment / Security / Policy / Other",
  "issues": [
    {{
      "problem": "...",
      "area": "Frontend / Backend / Security / Policy / Network"
    }}
  ],
  "emotion": "...",
  "confidence": "high / medium / low"
}}

Message:
{feedback_text}
"""
            }
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)

# ---------------- SAVE TO DB ----------------
def save_to_mongodb(user_input, cleaned_input, analysis):
    feedback_hash = generate_hash(cleaned_input)

    duplicate = is_duplicate(feedback_hash)
    priority = map_priority(analysis["confidence"])
    followup = get_followup_question(priority)
    system_message = get_default_message(priority)

    assigned_teams = list(
        {assign_team(issue["area"]) for issue in analysis["issues"]}
    )

    document = {
        "user_input": user_input,
        "cleaned_input": cleaned_input,
        "summary": analysis["summary"],
        "main_issue": analysis["main_issue"],
        "category": analysis["category"],
        "issues": analysis["issues"],
        "emotion": analysis["emotion"],
        "confidence": analysis["confidence"],
        "priority": priority,
        "assigned_teams": assigned_teams,
        "system_message": system_message,
        "followup_question": followup,
        "is_duplicate": duplicate,
        "feedback_hash": feedback_hash,
        "created_at": datetime.now(timezone.utc)
    }

    if not duplicate:
        collection.insert_one(document)

    return document

# ---------------- STREAMLIT UI ----------------
st.set_page_config(page_title="AI Feedback Analyzer", layout="centered")

st.title("🤖 AI Feedback Analysis System")
st.write("AI-powered feedback understanding, prioritization & routing")

feedback = st.text_area("📝 Enter your feedback", height=140)

if st.button("Analyze Feedback"):
    if not feedback.strip():
        st.warning("Please enter feedback.")
    else:
        with st.spinner("Analyzing feedback..."):
            try:
                cleaned_input = normalize_input(feedback)
                analysis = analyze_feedback(cleaned_input)
                result = save_to_mongodb(feedback, cleaned_input, analysis)

                st.success("Analysis Complete ✅")

                st.subheader("🧠 Summary")
                st.write(result["summary"])

                st.subheader("🔥 Main Issue")
                st.write(result["main_issue"])

                st.subheader("📂 Category")
                st.write(result["category"])

                st.subheader("🧩 Issues Found")
                for issue in result["issues"]:
                    st.markdown(f"- **{issue['problem']}** ({issue['area']})")

                st.subheader("😊 Emotion")
                st.write(result["emotion"].upper())

                st.subheader("⚡ Priority")
                st.write(result["priority"])

                st.subheader("👥 Assigned Teams")
                st.write(", ".join(result["assigned_teams"]))

                st.subheader("🤖 System Message")
                st.info(result["system_message"])

                if result["followup_question"]:
                    st.subheader("❓ Follow-up Question")
                    st.warning(result["followup_question"])

                if result["is_duplicate"]:
                    st.warning("⚠️ Duplicate feedback detected. Not stored again.")

            except Exception as e:
                st.error(f"Error: {str(e)}")
