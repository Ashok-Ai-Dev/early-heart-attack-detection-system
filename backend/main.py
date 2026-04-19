from fastapi import FastAPI, Depends, HTTPException, status
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
from passlib.context import CryptContext

# Auth Configuration
SECRET_KEY = "supersecretkey" # Use env variables in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# In-Memory DB
users_db = {}
history_db = {}

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserCreate(BaseModel):
    username: str
    password: str

class PredictionRequest(BaseModel):
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
        "password": get_password_hash(user.password)
    }
    history_db[user.username] = []
    return {"message": "User created successfully"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user['password']):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user["username"]}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/predict")
def predict_risk(request: PredictionRequest, username: str = Depends(get_current_user)):
    if model is None:
        return {"error": "Model not loaded. Try restarting server."}

    req_data = request.dict()
    df_processed = preprocess_input(req_data)
    
    # Predict
    probability = model.predict_proba(df_processed)[0][1] * 100
    risk_level = "Low"
    if probability > 66:
        risk_level = "High"
    elif probability > 33:
        risk_level = "Medium"
        
    # Recommendations Logic
    suggestions = []
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
        "risk": risk_level,
        "probability": round(probability, 2),
        "suggestion": " | ".join(suggestions) if suggestions else "Maintain a healthy lifestyle.",
        "diet": diet,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Save history
    if username in history_db:
        history_db[username].append(result)

    return result

@app.get("/history")
def get_history(username: str = Depends(get_current_user)):
    return {"history": history_db.get(username, [])}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
