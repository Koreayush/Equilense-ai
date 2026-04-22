export default function Sidebar({ view, setView }) {
  return (
    <aside className="sidebar">
      <div className="logo">
        <div className="logo-name">Equilense AI</div>
        <div className="logo-sub">Bias Detection System</div>
      </div>

      <div className="nav">
        <div
          className={`nav-item ${view === "audit" ? "active" : ""}`}
          onClick={() => setView("audit")}
        >
          ⚖️ Audit Workspace
        </div>

        <div
          className={`nav-item ${view === "dashboard" ? "active" : ""}`}
          onClick={() => setView("dashboard")}
        >
          📊 Dashboard
        </div>

        <div
          className={`nav-item ${view === "reports" ? "active" : ""}`}
          onClick={() => setView("reports")}
        >
          📄 Reports
        </div>
      </div>
    </aside>
  );
}