from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import re
import string
import random
import hashlib

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

COMMON_PASSWORDS = {
    "password", "123456", "123456789", "qwerty",
    "abc123", "password1", "111111", "12345678",
    "letmein", "iloveyou", "admin", "welcome", "monkey", "dragon", "sunshine"
}

password_history: dict[str, set[str]] = {}

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def check_length(password: str) -> tuple[bool, str]:
    length = len(password)
    if length >= 12:
        return True, f"Good length ({length} characters)."
    elif length >= 8:
        return False, f"Length is okay ({length}) but 12+ is safer."
    else:
        return False, f"Too short ({length} characters). Use at least 8."

def check_complexity(password: str) -> tuple[int, str]:
    categories = {
        "lowercase letters": any(c.islower() for c in password),
        "uppercase letters": any(c.isupper() for c in password),
        "digits": any(c.isdigit() for c in password),
        "special characters": any(c in string.punctuation for c in password),
    }
    score = sum(categories.values())
    missing = [name for name, present in categories.items() if not present]

    if score == 4:
        return score, "Great mix of character types."
    else:
        return score, f"Missing: {', '.join(missing)}."

def check_common_password(password: str) -> tuple[bool, str]:
    if password.lower() in COMMON_PASSWORDS:
        return False, "This is a widely-used common password. Avoid it entirely."
    return True, "Not found in common password list."

def check_repetition_and_sequences(password: str) -> tuple[bool, str]:
    if re.search(r"(.)\1{2,}", password):
        return False, "Contains repeated characters (e.g. 'aaa')."

    sequences = "0123456789" + string.ascii_lowercase
    lowered = password.lower()
    for i in range(len(lowered) - 3):
        chunk = lowered[i:i + 4]
        if chunk in sequences:
            return False, f"Contains a predictable sequence ('{chunk}')."
    return True, "No obvious repetition or sequences found."

def evaluate_password(password: str) -> dict:
    length_ok, length_msg = check_length(password)
    complexity_score, complexity_msg = check_complexity(password)
    common_ok, common_msg = check_common_password(password)
    pattern_ok, pattern_msg = check_repetition_and_sequences(password)

    score = 0
    score += 30 if length_ok else 10
    score += complexity_score * 15
    score += 10 if common_ok else 0

    if not common_ok:
        score = min(score, 30)
    if not pattern_ok:
        score -= 15

    score = max(0, min(100, score))
    if score >= 80:
        label = "Very Strong"
    elif score >= 60:
        label = "Strong"
    elif score >= 40:
        label = "Moderate"
    else:
        label = "Weak"

    return {
        "score": score,
        "label": label,
        "details": [length_msg, complexity_msg, common_msg, pattern_msg],
    }

def suggest_stronger_password(password: str) -> str:
    pool = string.ascii_letters + string.digits + "!@#$%^&*"
    base = password if password else "Pass"
    extra_needed = max(0, 14 - len(base))
    padding = "".join(random.choice(pool) for _ in range(extra_needed if extra_needed else 4))

    suggestion = base + padding
    if not any(c.isupper() for c in suggestion):
        suggestion += random.choice(string.ascii_uppercase)
    if not any(c.isdigit() for c in suggestion):
        suggestion += random.choice(string.digits)
    if not any(c in string.punctuation for c in suggestion):
        suggestion += random.choice("!@#$%^&*")

    return suggestion

@app.get("/")
def home():
    return FileResponse("index.html")

@app.get("/style.css")
def styles():
    return FileResponse("style.css")

class PasswordCheck(BaseModel):
    username:str
    password: str
    

@app.post("/check-password")
def check_password(data: PasswordCheck):
    pw_hash = hash_password(data.password)
    user_history = password_history.setdefault(data.username, set())

    if pw_hash in user_history:
        return {
            "reused": True,
            "message": "This password has been used before by this user. Choose a different one."
        }

    result = evaluate_password(data.password)
    user_history.add(pw_hash)
    
    response = {
        "reused": False,
        "score": result["score"],
        "label": result["label"],
        "details": result["details"],
    }
    if result["score"] < 80:
        response["suggestion"] = suggest_stronger_password(data.password)
    return response