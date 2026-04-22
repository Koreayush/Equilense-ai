import { useState } from "react";

export default function useAuditController() {
  const [state, setState] = useState({
    dataset: null,
    result: null,
    loading: false,
    error: null,
  });

  const setFile = (file) => {
    setState((prev) => ({ ...prev, dataset: file }));
  };

  const runAudit = async () => {
    if (!state.dataset) {
      alert("Upload file first 😭");
      return;
    }

    try {
      setState((prev) => ({ ...prev, loading: true }));

      const formData = new FormData();
      formData.append("file", state.dataset);
      formData.append("target_column", "approved");
      formData.append("sensitive_columns", "gender,race");

      const res = await fetch("http://localhost:8000/api/v1/audit/run", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Backend error");

      const data = await res.json();

      setState((prev) => ({
        ...prev,
        result: data,
        loading: false,
      }));

    } catch (err) {
      console.error(err);
      setState((prev) => ({
        ...prev,
        loading: false,
        error: err.message,
      }));
    }
  };

  const reset = () => {
    setState({
      dataset: null,
      result: null,
      loading: false,
      error: null,
    });
  };

  return {
    state,
    setFile,
    runAudit,
    reset,
  };
}