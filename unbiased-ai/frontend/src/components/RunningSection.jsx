export default function RunningSection({ controller }) {
  const { state } = controller;

  return (
    <div className="card">

      <h2>Running Audit...</h2>

      <div className="spinner"></div>

      <p>Status: {state.auditState}</p>

      <div style={{ marginTop: "10px" }}>
        {state.logs.map((log, i) => (
          <div key={i} className="mono">{log}</div>
        ))}
      </div>

    </div>
  );
}