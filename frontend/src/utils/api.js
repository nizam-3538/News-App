import axios from "axios";

// Create an Axios instance with the base URL of our FastAPI backend
// Determine base URL dynamically (Production vs. Localhost)
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add a request interceptor to attach the JWT token if one exists
api.interceptors.request.use(
  (config) => {
    // 1. Fetch token from localStorage
    const token = localStorage.getItem("access_token");

    // 2. If it exists, append it to the Authorization header
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Optional: Response interceptor for catching global 401 Unauthorized errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Logic to clear token and redirect could go here
      // localStorage.removeItem("access_token");
      // window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
