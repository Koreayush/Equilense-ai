import axios from 'axios';

// In a unified Docker setup, use relative paths to route through the Nginx reverse proxy.
// For local development (without Docker), fallback to port 8000.
const API_BASE_URL =
  window.location.hostname === "localhost" && window.location.port !== ""
    ? "http://localhost:8000/api/v1"
    : "/api/v1";

const client = axios.create({
  baseURL: API_BASE_URL,
});
export const auditApi = {
  runDatasetAudit: async (formData) => {
    const response = await client.post('/audit/run', formData);
    return response.data;
  },
  runModelAudit: async (formData) => {
    const response = await client.post('/model_audit/run', formData);
    return response.data;
  },
};

export default client;
