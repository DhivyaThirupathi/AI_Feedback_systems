from datetime import datetime, timezone
from uuid import uuid4
from pymongo import ReturnDocument

from backend.db import feedbacks, batches, analysis_results, global_issues
from backend.ai_engine import analyze_feedback_batch


# --------------------------------------------------
# Batch Handling (Hidden)
# --------------------------------------------------
def get_or_create_batch(district, constituency, limit=1): # SET TO 15
    batch = batches.find_one_and_update(
        {
            "district": district,
            "constituency": constituency,
            "status": "collecting"
        },
        {"$inc": {"count": 1}},
        return_document=ReturnDocument.AFTER
    )

    if not batch:
        batch = {
            "batch_id": str(uuid4()),
            "district": district,
            "constituency": constituency,
            "count": 1,
            "limit": limit,
            "status": "collecting",
            "created_at": datetime.now(timezone.utc)
        }
        batches.insert_one(batch)

    return batch


# --------------------------------------------------
# Main Entry Point
# --------------------------------------------------
def process_feedback(form_data):

    # 1. Add to Batch
    batch = get_or_create_batch(
        form_data["district"],
        form_data["constituency"]
    )

    # 2. Save Feedback
    feedbacks.insert_one({
        "location": {
            "district": form_data["district"],
            "constituency": form_data["constituency"]
        },
        "user": {
            "name": form_data.get("name"),
            "age": form_data.get("age"),
            "booth_no": form_data.get("booth_no"),
            "email": form_data.get("email")
        },
        "feedback": {
            "type": form_data["type_of_feedback"],
            "original_text": form_data["feedback_text"],
            "rating": form_data.get("rating")
        },
        "batch_id": batch["batch_id"],
        "created_at": datetime.now(timezone.utc)
    })

    # 3. Check Limit (Run AI if full)
    if batch["count"] >= batch["limit"]:
        batches.update_one(
            {"batch_id": batch["batch_id"]},
            {"$set": {"status": "processing"}}
        )
        analyze_and_store_batch(batch["batch_id"])
        return {"message": "Batch Full (15/15) - AI Analysis Started!"}

    remaining = batch["limit"] - batch["count"]
    return {"message": f"Feedback stored. Waiting for {remaining} more users."}


# --------------------------------------------------
# AI Processing
# --------------------------------------------------
def analyze_and_store_batch(batch_id):
    print(f"🚀 Analyzing Batch: {batch_id}")
    
    docs = list(feedbacks.find({"batch_id": batch_id}))
    texts = [d["feedback"]["original_text"] for d in docs]

    try:
        results = analyze_feedback_batch(texts)
    except Exception as e:
        print(f"❌ AI Failed: {e}")
        return

    # Update Feedback Docs
    for doc, res in zip(docs, results):
        feedbacks.update_one(
            {"_id": doc["_id"]},
            {"$set": {"ai": res}}
        )

    # Update Global Issues (Smart Merging)
    update_global_issues(docs, batch_id)

    # Mark Batch Complete
    batches.update_one(
        {"batch_id": batch_id},
        {"$set": {"status": "completed"}}
    )
    print(f"✅ Batch {batch_id} Completed.")


# --------------------------------------------------
# Global Issue Merging (Smart Logic)
# --------------------------------------------------
def calculate_priority(count):
    if count >= 20: return "CRITICAL"
    elif count >= 10: return "HIGH"
    elif count >= 5: return "MEDIUM"
    return "LOW"

def update_global_issues(docs, batch_id):
    for fb in docs:
        if "ai" not in fb: continue
        
        category = fb["ai"].get("category", "Other")
        main_issue = fb["ai"].get("main_issue", "General Issue")
        
        # UNIQUE KEY: Merges same issues across different batches
        issue_key = f"{category}_{main_issue}".replace(" ", "_").lower()
        
        user_info = {
            "name": fb["user"]["name"],
            "booth": fb["user"]["booth_no"],
            "batch_id": batch_id
        }

        existing = global_issues.find_one({"issue_key": issue_key})

        if existing:
            # Add to existing Global Issue
            new_total = existing["total_reports"] + 1
            global_issues.update_one(
                {"issue_key": issue_key},
                {
                    "$inc": {"total_reports": 1},
                    "$push": {"users": user_info},
                    "$addToSet": {"batches": batch_id},
                    "$set": {
                        "priority": calculate_priority(new_total),
                        "last_updated": datetime.now(timezone.utc)
                    }
                }
            )
        else:
            # Create New Global Issue
            global_issues.insert_one({
                "issue_key": issue_key,
                "category": category,
                "issue_text": main_issue,
                "total_reports": 1,
                "priority": "LOW",
                "batches": [batch_id],
                "users": [user_info],
                "last_updated": datetime.now(timezone.utc)
            })