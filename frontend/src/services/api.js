import axios from 'axios';

const API_URL =  "https://early-heart-attack-detection-system.onrender.com";
const api = axios.create({
  baseURL: API_URL,
});

// Add a request interceptor to add the JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add a response interceptor to handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const login = async (username, password) => {
  const params = new URLSearchParams();
  params.append('username', username);
  params.append('password', password);
  
  const response = await api.post('/login', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  });
  return response.data;
};

export const signup = async (username, password) => {
  const response = await api.post('/signup', { username, password });
  return response.data;
};

export const predictRisk = async (data) => {
  const response = await api.post('/predict', data);
  return response.data;
};

export const getHistory = async () => {
  const response = await api.get('/history');
  return response.data;
};

export const findHealthcare = async (lat, lng) => {
  const response = await api.post('/find-healthcare', { lat, lng });
  return response.data;
};

export const downloadReport = async (data) => {
  const response = await api.post('/generate-report', data, {
    responseType: 'blob', // Important for handling binary data
  });
  return response.data;
};

export default api;
