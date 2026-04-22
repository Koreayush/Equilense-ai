export default function ResultsSection({ controller }) {
  if (!controller) return <div>No controller 😭</div>;

  const { state, reset } = controller;
  const { result } = state;

  if (!result) return <div>No results</div>;

  return (
    <div className="card">
      <h2>Audit Results</h2>

      <p><strong>Risk Score:</strong> {result.summary?.risk_score}</p>

      <p>
        Failed: {result.summary?.metrics_failed} / {result.summary?.metrics_total}
      </p>

      <h3>Findings</h3>

      {result.findings?.map((f, i) => (
        <div key={i} className="finding">
          <b>{f.title}</b>
          <p>{f.description}</p>
        </div>
      ))}

      <br />

      <button className="btn" onClick={reset}>
        🔄 Run Again
      </button>
    </div>
  );
}