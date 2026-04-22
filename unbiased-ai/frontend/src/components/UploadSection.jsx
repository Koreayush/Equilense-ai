export default function UploadSection({ controller }) {
  const { setFile, runAudit, state } = controller;

  return (
    <div className="card">

      <input
        type="file"
        onChange={(e) => setFile(e.target.files[0])}
      />

      <button className="btn btn-primary" onClick={runAudit}>
        🚀 Run Audit
      </button>

      {state.loading && <p>Running... ⏳</p>}
      {state.error && <p style={{ color: "red" }}>{state.error}</p>}

    </div>
  );
}