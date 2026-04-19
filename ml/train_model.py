import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
import pickle
import os

def create_dataset():
    np.random.seed(42)
    n_samples = 1000
    
    # Generate synthetic data following a realistic distribution for heart disease
    age = np.random.randint(29, 80, n_samples)
    gender = np.random.choice([0, 1], n_samples, p=[0.3, 0.7]) # 1: Male, 0: Female
    cp = np.random.randint(0, 4, n_samples) # Chest pain type
    trestbps = np.random.randint(94, 200, n_samples) # Blood pressure
    chol = np.random.randint(126, 564, n_samples) # Cholesterol
    fbs = np.random.choice([0, 1], n_samples, p=[0.85, 0.15]) # Fasting blood sugar
    bmi = np.random.uniform(18.5, 40.0, n_samples) # BMI
    exercise_level = np.random.choice([0, 1], n_samples, p=[0.67, 0.33]) # Exercise induced angina
    smoking = np.random.choice(['yes', 'no'], n_samples, p=[0.4, 0.6])
    alcohol = np.random.choice(['yes', 'no'], n_samples, p=[0.5, 0.5])
    
    # Simple logic to determine target (1: heart disease risk, 0: less risk) to make the model learn something
    risk_score = (age / 80) + (trestbps / 200) + (chol / 500) + (bmi / 40) + \
                 (cp * 0.3) + exercise_level + \
                 (np.where(smoking == 'yes', 1, 0) * 0.5) + \
                 (np.where(alcohol == 'yes', 1, 0) * 0.3)
    
    target = np.where(risk_score > np.median(risk_score), 1, 0)
    
    df = pd.DataFrame({
        'age': age,
        'gender': gender,
        'cp': cp,
        'trestbps': trestbps,
        'chol': chol,
        'fbs': fbs,
        'bmi': bmi,
        'exercise_level': exercise_level,
        'smoking': smoking,
        'alcohol': alcohol,
        'target': target
    })
    
    df.to_csv('dataset.csv', index=False)
    print("Dataset created successfully at dataset.csv")
    return df

def train_model():
    df = pd.read_csv('dataset.csv')
    
    # Preprocessing
    # Convert categorical: smoking, alcohol
    df['smoking'] = df['smoking'].map({'yes': 1, 'no': 0})
    df['alcohol'] = df['alcohol'].map({'yes': 1, 'no': 0})
    
    X = df.drop('target', axis=1)
    y = df['target']
    
    # Train RandomForest model
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X, y)
    
    # Train XGBoost model (optional, will primary use rf_model or xgb)
    xgb_model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
    xgb_model.fit(X, y)
    
    # Save models
    # We will use RF backend model as primary
    os.makedirs('../backend', exist_ok=True)
    with open('../backend/model.pkl', 'wb') as f:
        pickle.dump(rf_model, f)
        
    print("Model trained and saved successfully to ../backend/model.pkl")

if __name__ == '__main__':
    create_dataset()
    train_model()
