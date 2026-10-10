import axios from "axios";

// One place for all calls to the Flask backend.
// withCredentials sends the login session cookie with every request.
const api = axios.create({
  baseURL: "/api",
  withCredentials: true,
});

export async function getHealth() {
  const response = await api.get("/health");
  return response.data;
}

export default api;
