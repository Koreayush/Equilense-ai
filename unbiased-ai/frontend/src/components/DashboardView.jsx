export default function DashboardView() {
  return (
    <section id="view-dashboard" className="view">
      <div className="grid grid-2">
        <div className="card chart-card">
          <canvas id="chartTrend"></canvas>
        </div>

        <div className="card">
          <div className="section-title">Audit Overview</div>

          <div className="overview-list">
            <div className="overview-item">
              <span>Mode</span>
              <strong id="dashboard-mode">Dataset</strong>
            </div>

            <div className="overview-item">
              <span>Risk</span>
              <strong id="dashboard-risk">LOW</strong>
            </div>

            <div className="overview-item">
              <span>Findings</span>
              <strong id="dashboard-findings">0</strong>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}