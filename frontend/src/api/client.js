import axios from "axios";

// One place for all calls to the Flask backend.
// withCredentials sends the login session cookie with every request.
const api = axios.create({
  baseURL: "/api",
  withCredentials: true,
});

// Flask rejects any POST/PUT/DELETE without a CSRF token (protection against forged requests).
// Before each such request, fetch a fresh token and send it in the X-CSRFToken header.
api.interceptors.request.use(async (config) => {
  const method = (config.method || "get").toLowerCase();
  if (method !== "get") {
    const { data } = await axios.get("/api/auth/csrf", { withCredentials: true });
    config.headers["X-CSRFToken"] = data.csrf_token;
  }
  return config;
});

export async function getHealth() {
  const response = await api.get("/health");
  return response.data;
}

// Who is logged in? Returns the user, or null if nobody is.
export async function getMe() {
  try {
    const response = await api.get("/auth/me");
    return response.data.user;
  } catch (error) {
    if (error.response && error.response.status === 401) return null;
    throw error;
  }
}

export async function login(email, password) {
  const response = await api.post("/auth/login", { email, password });
  return response.data.user;
}

export async function logout() {
  await api.post("/auth/logout");
}

export default api;
