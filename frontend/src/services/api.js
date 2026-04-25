import axios from "axios";

// ⚠️ IMPORTANT: अपना backend URL डालो
const API_URL = import.meta.env.VITE_API_URL || "https://your-backend.onrender.com";

const api = axios.create({
  baseURL: API_URL,
});

// Token interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Signup API
export const signup = async (userData) => {
  const response = await api.post("/signup", userData);
  return response.data;
};

// Login API
export const login = async (username, password) => {
  const params = new URLSearchParams();
  params.append("username", username);
  params.append("password", password);

  const response = await api.post("/login", params, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });

  return response.data;
};

export default api;