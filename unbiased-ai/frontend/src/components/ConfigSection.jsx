export default function ConfigSection({ controller }) {
  const { updateConfig, runAudit, reset, canRun, state } = controller;

  return (
    <div className="card">

      <h2>Configuration</h2>

      <input
        placeholder="Target column"
        value={state.config.target}
        onChange={(e) => updateConfig("target", e.target.value)}
      />

      <input
        placeholder="Sensitive columns"
        value={state.config.sensitive}
        onChange={(e) => updateConfig("sensitive", e.target.value)}
      />

      <input
        placeholder="Prediction column (optional)"
        value={state.config.yPred}
        onChange={(e) => updateConfig("yPred", e.target.value)}
      />

      <br /><br />

      <div style={{ display: "flex", gap: "10px" }}>

        <button
          className="btn btn-primary"
          onClick={runAudit}
          disabled={!canRun()}
        >
          🚀 Run Audit
        </button>

        <button className="btn" onClick={reset}>
          🔄 Reset
        </button>

      </div>
    </div>
  );
}