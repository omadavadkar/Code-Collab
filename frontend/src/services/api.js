import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

export async function runCode(language, code) {
  const response = await axios.post(`${API_BASE}/run`, { language, code });
  return response.data;
}
