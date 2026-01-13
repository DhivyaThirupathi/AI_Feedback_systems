import re

# =========================
# 1. LANGUAGE DETECTION
# =========================
TAMIL_KEYWORDS = [
    "thanni", "romba", "kastam", "iruku", "irukku", "illa", "varala", "naal",
    "kuppai", "sutham", "mosam", "saalai", "arasu", "thappu", "velai", "office",
    "current", "cut", "seri illa", "neraya", "konjam", "problem", "varudhu"
]

def detect_language(text):
    text_lower = text.lower()
    tamil_count = 0
    for word in TAMIL_KEYWORDS:
        if word in text_lower:
            tamil_count += 1
    return "ta" if tamil_count >= 1 else "en"


# =========================
# 2. OFFLINE TRANSLATION
# =========================
TAMIL_TO_ENGLISH = {
    "thanni": "water", "varala": "not coming", "varudhu": "is coming",
    "romba": "very", "kastam": "difficult", "iruku": "is", "illa": "no",
    "kuppai": "garbage", "sutham": "cleanliness", "mosam": "bad",
    "road": "road", "current": "power", "cut": "cut", "velai": "work",
    "office": "office", "neraya": "a lot", "konjam": "little",
    "problem": "problem", "seri": "okay", "worst": "worst",
    "danger": "danger", "school": "school", "hospital": "hospital"
}

COMMON_PHRASES = {
    "thanni varala": "water is not coming",
    "romba kastama iruku": "it is very difficult",
    "sutham illa": "there is no cleanliness",
    "current cut": "power cut",
    "velai illa": "no work"
}

def translate_to_english(text):
    text_lower = text.lower()
    for phrase, meaning in COMMON_PHRASES.items():
        text_lower = text_lower.replace(phrase, meaning)
    
    words = text_lower.split()
    translated_words = []
    for word in words:
        clean_word = re.sub(r"[^\w\s]", "", word)
        translated_word = TAMIL_TO_ENGLISH.get(clean_word, clean_word)
        translated_words.append(translated_word)
    
    return " ".join(translated_words).capitalize()


# =========================
# 3. CATEGORY KEYWORDS
# =========================
CATEGORY_KEYWORDS = {
    "Water": ["water", "thanni", "pipe", "tap", "supply", "leak", "varala"],
    "Sanitation": ["garbage", "trash", "waste", "dirty", "smell", "drain", "kuppai"],
    "Road": ["road", "pothole", "street", "saalai", "traffic", "damaged"],
    "Electricity": ["current", "power", "electric", "light", "cut", "voltage"],
    "Services": ["service", "office", "staff", "delay", "response", "rude", "delivery"],
    "Health": ["hospital", "doctor", "medicine", "sick", "clinic"],
    "Education": ["school", "college", "teacher", "student", "fees"],
    "Transport": ["bus", "train", "transport", "driver", "ticket"],
    "Safety": ["danger", "accident", "risk", "theft", "police", "dark"]
}

def detect_category(text):
    text_lower = text.lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for word in keywords if word in text_lower)
        scores[category] = score
    
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Other"


# =========================
# 4. PRIORITY DETECTION
# =========================
HIGH_PRIORITY_WORDS = ["urgent", "danger", "accident", "risk", "critical", "worst", "life threat"]
MEDIUM_PRIORITY_WORDS = ["problem", "issue", "bad", "delay", "ignored", "kastam"]

def detect_priority(text):
    text_lower = text.lower()
    if re.search(r"\b\d+\s*(day|days|week|weeks)\b", text_lower):
        return "High"
    if any(w in text_lower for w in HIGH_PRIORITY_WORDS): return "High"
    if any(w in text_lower for w in MEDIUM_PRIORITY_WORDS): return "Medium"
    return "Low"


# =========================
# 5. MAIN ISSUE MAPPING
# =========================
def extract_main_issue(category):
    mapping = {
        "Water": "Water supply issue in the area",
        "Sanitation": "Poor cleanliness and waste management",
        "Road": "Bad road condition causing inconvenience",
        "Electricity": "Power supply disruption in the area",
        "Services": "Poor response from public services",
        "Health": "Healthcare service issue",
        "Education": "Education related issue",
        "Transport": "Public transport issue",
        "Safety": "Public safety concern",
        "Other": "General issue reported"
    }
    return mapping.get(category, "General issue reported")

def generate_summary(text):
    words = text.split()
    return " ".join(words[:15]) + "..." if len(words) > 15 else text


# =========================
# 6. MAIN FUNCTION (CONNECTED)
# =========================
def analyze_feedback_batch(feedback_list):
    """
    Processes a list of feedbacks and returns analysis results.
    """
    results = []
    for text in feedback_list:
        eng_text = translate_to_english(text)
        category = detect_category(eng_text)
        priority = detect_priority(eng_text)
        main_issue = extract_main_issue(category)
        summary = generate_summary(eng_text)
        
        results.append({
            "category": category,
            "priority": priority,
            "main_issue": main_issue,
            "summary": summary
        })
    return results