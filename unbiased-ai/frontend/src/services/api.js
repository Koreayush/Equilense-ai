const CONFIG = {
  API_BASE: "http://localhost:8000",
  ENDPOINTS: {
    fairnessAudit: "/api/v1/audit/run",
    modelAudit: "/api/v1/model_audit/run",
  },
};

export async function runAuditRequest({ mode, formData }) {
  const endpoint =
    mode === "model"
      ? CONFIG.API_BASE + CONFIG.ENDPOINTS.modelAudit
      : CONFIG.API_BASE + CONFIG.ENDPOINTS.fairnessAudit;

  const response = await fetch(endpoint, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}