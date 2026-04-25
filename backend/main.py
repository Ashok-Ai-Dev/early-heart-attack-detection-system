from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import pickle
import numpy as np
from preprocessing import preprocess_input
from fastapi.middleware.cors import CORSMiddleware
import os
import contextlib
import jwt
from datetime import datetime, timedelta
import hashlib
import json
import urllib.request
from fastapi import BackgroundTasks
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.append(os.path.dirname(__file__))

from utils.alert import send_alert
from services.pdf_service import generate_risk_report_pdf
# Auth Configuration
SECRET_KEY = "supersecretkey" # Use env variables in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# JSON DB Persistence
DB_FILE = os.path.join(os.path.dirname(__file__), "database.json")

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                return data.get("users", {}), data.get("history", {})
        except Exception:
            pass
    return {}, {}

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump({"users": users_db, "history": history_db}, f)

users_db, history_db = load_db()

def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username not in users_db:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")


# App Lifecycle
model = None

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    model_path = os.path.join(os.path.dirname(__file__), "model.pkl")
    if os.path.exists(model_path):
        with open(model_path, "rb") as f:
            model = pickle.load(f)
    print("Model loaded")
    yield
    model = None

app = FastAPI(title="Heart Attack Prediction API", lifespan=lifespan)

# Setup CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://0.0.0.0:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserCreate(BaseModel):
    username: str
    password: str
    name: str = ""
    email: str = ""
    phone: str = ""
    age: float = 0
    gender: int = 1

class PredictionRequest(BaseModel):
    name: str = "Unknown Patient"
    email: str = ""
    phone: str = ""
    age: float
    gender: int
    cp: int
    trestbps: float
    chol: float
    fbs: int
    bmi: float
    exercise_level: int
    smoking: str
    alcohol: str

@app.post("/signup")
def signup(user: UserCreate):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    users_db[user.username] = {
        "username": user.username,
        "password": get_password_hash(user.password),
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "age": user.age,
        "gender": user.gender
    }
    history_db[user.username] = []
    save_db()
    return {"message": "User created successfully"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user['password']):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user["username"]}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/predict")
def predict_risk(request: PredictionRequest, background_tasks: BackgroundTasks, username: str = Depends(get_current_user)):
    if model is None:
        return {"error": "Model not loaded. Try restarting server."}

    req_data = request.dict()
    df_processed = preprocess_input(req_data)
    
    # Predict
    probability = model.predict_proba(df_processed)[0][1] * 100
    risk_level = "Low"
    if probability > 70:
        risk_level = "High"
    elif probability > 50:
        risk_level = "Medium"
        
    if risk_level == "High":
        if req_data.get("email"):
            background_tasks.add_task(
                send_alert,
                user_email=req_data["email"],
                risk_score=round(probability, 2),
                risk_level=risk_level,
                user_name=req_data.get("name", "User"),
                user_phone=req_data.get("phone", "")
            )
        
    # Recommendations Logic
    suggestions = []
    
    if risk_level == "High":
        suggestions.append("🚨 URGENT: Your risk level is HIGH. Please consult a Cardiologist or healthcare professional immediately.")
    elif risk_level == "Medium":
        suggestions.append("⚠️ NOTICE: Your risk level is elevated. Consider scheduling a checkup with your doctor soon.")

    if req_data.get('smoking', '').lower() == 'yes' or req_data.get('alcohol', '').lower() == 'yes':
        suggestions.append("Quitting smoking and alcohol can reduce heart attack risk by up to 20%.")
    if req_data.get('bmi', 0) > 25:
        suggestions.append("Consider weight control and exercise to reduce BMI.")
    if req_data.get('trestbps', 0) > 130:
        suggestions.append("Your blood pressure is high. Suggest a low salt diet and regular checkups.")
    if req_data.get('chol', 0) > 200:
        suggestions.append("Your cholesterol is elevated. Reduce intake of oily and high cholesterol food.")

    diet = "Eat fruits (apple, banana), green vegetables, fiber-rich food. Avoid oily and high cholesterol food."

    result = {
        "name": req_data.get('name', 'Unknown Patient'),
        "risk": risk_level,
        "probability": round(probability, 2),
        "suggestion": " | ".join(suggestions) if suggestions else "Maintain a healthy lifestyle.",
        "diet": diet,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Save history
    if username in history_db:
        history_db[username].append(result)
        save_db()

    return result

@app.get("/history")
def get_history(username: str = Depends(get_current_user)):
    return {"history": history_db.get(username, [])}

@app.get("/profile")
def get_profile(username: str = Depends(get_current_user)):
    user = users_db.get(username, {})
    return {
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "phone": user.get("phone", ""),
        "age": user.get("age", 0) if user.get("age") else "",
        "gender": user.get("gender", 1)
    }

class LocationRequest(BaseModel):
    lat: float
    lng: float

@app.post("/find-healthcare")
def find_healthcare(location: LocationRequest):
    # Using Overpass API to find hospitals and cardiologists near latitude/longitude
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    query_hospitals = f'[out:json];node["amenity"="hospital"](around:10000,{location.lat},{location.lng});out 5;'
    query_doctors = f'[out:json];node["amenity"="clinic"](around:10000,{location.lat},{location.lng});out 5;'
    
    def fetch_osm(query, default_name, search_query):
        try:
            req = urllib.request.Request(f"{overpass_url}?data={urllib.parse.quote(query)}")
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                results = []
                for node in data.get('elements', []):
                    tags = node.get('tags', {})
                    name = tags.get('name', default_name)
                    if name == default_name: continue
                    results.append({
                        "name": name,
                        "address": tags.get('addr:full', tags.get('addr:street', 'Local Area')),
                        "rating": round(4.0 + (node['id'] % 10) / 10, 1), # Mock rating for demo
                        "map_link": f"https://www.google.com/maps/search/?api=1&query={node['lat']},{node['lon']}"
                    })
                return results
        except Exception:
            return []

    import urllib.parse
    top_hospitals = [
        {"name": "All India Institute of Medical Sciences (AIIMS)", "address": "New Delhi, India", "rating": 4.9, "map_link": "https://www.google.com/maps/search/?api=1&query=AIIMS+Hospital"},
        {"name": "Fortis Escorts Heart Institute", "address": "Okhla, New Delhi", "rating": 4.8, "map_link": "https://www.google.com/maps/search/?api=1&query=Fortis+Escorts+Heart+Institute"},
        {"name": "Apollo Hospitals", "address": "Multi-city (Delhi, Chennai, etc)", "rating": 4.7, "map_link": "https://www.google.com/maps/search/?api=1&query=Apollo+Hospitals"},
        {"name": "Narayana Institute of Cardiac Sciences", "address": "Bengaluru, Karnataka", "rating": 4.8, "map_link": "https://www.google.com/maps/search/?api=1&query=Narayana+Institute+of+Cardiac+Sciences"},
        {"name": "Medanta – The Medicity", "address": "Gurugram, Haryana", "rating": 4.7, "map_link": "https://www.google.com/maps/search/?api=1&query=Medanta+The+Medicity"},
        {"name": "Asian Heart Institute", "address": "Bandra Kurla Complex, Mumbai", "rating": 4.9, "map_link": "https://www.google.com/maps/search/?api=1&query=Asian+Heart+Institute"},
        {"name": "Max Super Speciality Hospital", "address": "Saket, New Delhi", "rating": 4.6, "map_link": "https://www.google.com/maps/search/?api=1&query=Max+Super+Speciality+Hospital"}
    ]
    
    top_cardiologists = [
        {"name": "Dr. Naresh Trehan", "address": "Medanta – The Medicity", "rating": 4.9, "map_link": "https://www.google.com/maps/search/?api=1&query=Dr+Naresh+Trehan+Medanta"},
        {"name": "Dr. Ashok Seth", "address": "Fortis Escorts Heart Institute", "rating": 4.9, "map_link": "https://www.google.com/maps/search/?api=1&query=Dr+Ashok+Seth+Fortis"},
        {"name": "Dr. Devi Shetty", "address": "Narayana Health", "rating": 5.0, "map_link": "https://www.google.com/maps/search/?api=1&query=Dr+Devi+Shetty+Narayana"},
        {"name": "Dr. Ramakanta Panda", "address": "Asian Heart Institute", "rating": 4.8, "map_link": "https://www.google.com/maps/search/?api=1&query=Dr+Ramakanta+Panda+Asian+Heart"},
        {"name": "Dr. K. M. Cherian", "address": "Frontier Lifeline Hospital", "rating": 4.8, "map_link": "https://www.google.com/maps/search/?api=1&query=Dr+KM+Cherian"}
    ]
        
    return {
        "cardiologists": top_cardiologists,
        "hospitals": top_hospitals
    }


class ReportRequest(BaseModel):
    name: str
    age: float
    gender: int
    email: str
    risk_percentage: float
    risk_level: str
    suggestions: list[str]

@app.post("/generate-report")
def generate_report(request: ReportRequest):
    try:
        pdf_buffer = generate_risk_report_pdf(request.dict())
        return StreamingResponse(
            pdf_buffer, 
            media_type="application/pdf", 
            headers={"Content-Disposition": f"attachment; filename=Heart_Risk_Report_{request.name}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
