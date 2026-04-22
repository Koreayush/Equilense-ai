export default function Topbar() {
  return (
    <div className="topbar">
      <div>
        <div className="title">Decision Auditor</div>
        <div className="subtitle">
          Inspect datasets and machine learning models for fairness.
        </div>
      </div>

      <div className="toolbar">
        <button className="btn btn-secondary" onClick={() => window.resetDemo()}>
          Reset
        </button>
        <button id="run-btn" className="btn btn-primary" onClick={() => window.runAudit()}>
          Run Audit
        </button>
      </div>
    </div>
  );
}