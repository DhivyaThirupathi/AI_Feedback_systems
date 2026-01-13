import pandas as pd
import json
import requests
from io import StringIO

URL = "https://en.wikipedia.org/wiki/List_of_constituencies_of_the_Tamil_Nadu_Legislative_Assembly"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

response = requests.get(URL, headers=headers)
response.raise_for_status()

# Read tables from HTML
tables = pd.read_html(StringIO(response.text))

df = tables[0]

df = df[["District", "Constituency"]]
df.columns = ["district_en", "constituency_en"]

# Tamil district names (extendable)
district_ta = {
    "Chennai": "சென்னை",
    "Coimbatore": "கோயம்புத்தூர்",
    "Madurai": "மதுரை",
    "Salem": "சேலம்",
    "Tiruchirappalli": "திருச்சிராப்பள்ளி"
}

result = {}

for _, row in df.iterrows():
    d = row["district_en"]
    c = row["constituency_en"]

    if d not in result:
        result[d] = {
            "ta": district_ta.get(d, d),
            "constituencies": []
        }

    result[d]["constituencies"].append({
        "en": c,
        "ta": c   # Tamil refinement later
    })

# Save Excel
df.to_excel("TN_Assembly_Constituencies_FULL.xlsx", index=False)

# Save JSON
with open("TN_Assembly_Constituencies_FULL.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("✅ FULL DATA GENERATED SUCCESSFULLY")
