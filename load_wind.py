import json
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")  # replace with your key
firebase_admin.initialize_app(cred)

# Firestore client
db = firestore.client()

# Fetch wind_data collection
collection_ref = db.collection('wind_data')
docs = collection_ref.stream()


# Helper function to convert Firestore data to JSON-serializable
def serialize(obj):
    if isinstance(obj, Timestamp):
        return obj.ToDatetime().isoformat()
    if hasattr(obj, "isoformat"):  # handle datetime objects
        return obj.isoformat()
    return obj


data = {}
for doc in docs:
    # recursively convert nested dicts
    def convert(d):
        for k, v in d.items():
            if isinstance(v, dict):
                convert(v)
            elif isinstance(v, list):
                for i in range(len(v)):
                    if hasattr(v[i], "isoformat"):
                        v[i] = v[i].isoformat()
            elif hasattr(v, "isoformat"):
                d[k] = v.isoformat()
        return d

    data[doc.id] = convert(doc.to_dict())

# Save as JSON
with open("wind_data.json", "w") as f:
    json.dump(data, f, indent=2)

print("Data saved to wind_data.json")