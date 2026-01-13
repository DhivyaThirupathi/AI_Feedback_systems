from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.feedback_service import process_feedback

app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- REQUEST MODEL ----------------
class FeedbackRequest(BaseModel):
    district: str
    constituency: str
    name: str | None = None
    age: int | None = None
    booth_no: str | None = None
    email: str | None = None
    type_of_feedback: str
    feedback_text: str
    rating: int | None = None
    solution: str | None = None

# ---------------- API ENDPOINT ----------------
@app.post("/api/feedback")
def submit_feedback(req: FeedbackRequest):
    return process_feedback(req.dict())
