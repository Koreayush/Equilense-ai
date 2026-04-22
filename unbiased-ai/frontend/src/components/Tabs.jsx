export default function Tabs() {
  return (
    <div className="card" style={{ marginTop: 20 }}>
      <div className="tabs">
        <button className="tab active" onClick={() => window.switchTab("metrics")}>Metrics</button>
        <button className="tab" onClick={() => window.switchTab("findings")}>Findings</button>
        <button className="tab" onClick={() => window.switchTab("groups")}>Groups</button>
        <button className="tab" onClick={() => window.switchTab("summary")}>Summary</button>
      </div>

      {/* Metrics */}
      <div id="tab-metrics" className="tab-content" style={{ display: "block" }}>
        <table>
          <thead>
            <tr>
              <th>Attribute</th>
              <th>Metric</th>
              <th>Value</th>
              <th>Threshold</th>
              <th>Status</th>
              <th>Severity</th>
            </tr>
          </thead>
          <tbody id="metrics-table-body"></tbody>
        </table>
      </div>

      {/* Findings */}
      <div id="tab-findings" className="tab-content">
        <div id="findings-list"></div>
      </div>

      {/* Groups */}
      <div id="tab-groups" className="tab-content">
        <canvas id="chartRace"></canvas>
        <canvas id="chartGender"></canvas>

        <table>
          <tbody id="group-breakdown-body"></tbody>
        </table>
      </div>

      {/* Summary */}
      <div id="tab-summary" className="tab-content">
        <div id="executive-summary-box"></div>
      </div>
    </div>
  );
}