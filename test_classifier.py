from app.models.spam_classifier import ScamClassifier

try:
    print("Initializing ScamClassifier...")
    classifier = ScamClassifier()
    print("ScamClassifier initialized.")
    
    text = "URGENT: Your account is locked!"
    result = classifier.predict(text)
    print(f"Prediction result: {result}")
    
except Exception as e:
    print(f"Error: {e}")
