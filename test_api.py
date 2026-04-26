import requests

# 1. Signup
res = requests.post("http://localhost:8000/signup", json={"username": "testuser", "password": "testpassword", "age": 30})
print("Signup:", res.text)

# 2. Login
res = requests.post("http://localhost:8000/login", data={"username": "testuser", "password": "testpassword"})
print("Login:", res.text)
token = res.json().get("access_token")

# 3. Predict
data = {
    "name": "Test",
    "email": "test@test.com",
    "phone": "123",
    "age": 45,
    "gender": 1,
    "cp": 1,
    "trestbps": 120,
    "chol": 200,
    "fbs": 0,
    "bmi": 25,
    "exercise_level": 0,
    "smoking": "no",
    "alcohol": "no"
}
headers = {"Authorization": f"Bearer {token}"}
res = requests.post("http://localhost:8000/predict", json=data, headers=headers)
print("Predict:", res.status_code, res.text)
