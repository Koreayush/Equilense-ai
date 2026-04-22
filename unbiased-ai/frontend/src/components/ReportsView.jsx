export default function ReportsView() {
  return (
    <section id="view-reports" className="view">
      <div className="card">
        <div className="section-title">Generated Reports</div>

        <p id="report-meta">No reports yet.</p>

        <div style={{ display: "flex", gap: 12 }}>
          <a id="download-pdf-btn" className="btn btn-primary" href="#">
            Download PDF
          </a>

          <a id="download-json-btn" className="btn btn-secondary" href="#">
            Download JSON
          </a>
        </div>
      </div>
    </section>
  );
}