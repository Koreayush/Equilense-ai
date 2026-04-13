/* ─────────────────────────────────────────────────────────────
   Equilense AI — Stable Frontend App Controller
   Fixed Interaction Build
   Layer 1 + Layer 2 Compatible
───────────────────────────────────────────────────────────── */

(() => {
  "use strict";

  /* ───────────────────────────────────────────────────────────
     CONFIG
  ─────────────────────────────────────────────────────────── */
  const CONFIG = {
    API_BASE: "http://localhost:8000",
    ENDPOINTS: {
    // Layer 1
      fairnessAudit: "/api/v1/audit/run",

    // Layer 2
      modelAudit: "/api/v1/model_audit/run",
    },
    MAX_UPLOAD_MB: 50,
  };

  /* ───────────────────────────────────────────────────────────
     STATE
  ─────────────────────────────────────────────────────────── */
  const state = {
    currentView: "audit",
    currentTab: "metrics",
    auditMode: "dataset", // dataset | model
    auditState: "idle",   // idle | uploading | running | completed | failed

    files: {
      dataset: null,
      model: null,
      evalDataset: null,
    },

    result: null,
    charts: {
      race: null,
      gender: null,
      trend: null,
    },
  };

  /* ───────────────────────────────────────────────────────────
     DOM HELPERS
  ─────────────────────────────────────────────────────────── */
  const $ = (id) => document.getElementById(id);
  const $$$ = (selector) => document.querySelectorAll(selector);

  const els = {
    // Sections
    uploadSection: $("upload-section"),
    configSection: $("config-section"),
    runningSection: $("running-section"),
    resultsSection: $("results-section"),

    // Buttons
    runBtn: $("run-btn"),
    resetBtn: null,

    // Inputs
    csvInput: $("file-input"),
    modelInput: $("model-file-input"),
    evalInput: $("eval-file-input"),

    // File labels
    uploadedFileName: $("uploaded-file-name"),
    uploadedModelName: $("uploaded-model-name"),
    uploadedEvalName: $("uploaded-eval-name"),

    // Upload zone
    dropzone: $("dropzone"),

    // Config
    targetColumn: $("target-column"),
    sensitiveColumns: $("sensitive-columns"),
    yPredColumn: $("y-pred-column"),
    positiveLabel: $("positive-label"),

    // Running
    runStatus: $("run-status"),
    progressBar: $("progress-bar"),
    runLog: $("run-log"),

    // Summary cards
    riskScoreVal: $("risk-score-val"),
    riskScoreLabel: $("risk-score-label"),
    metricsFailed: $("metrics-failed"),
    metricsTotal: $("metrics-total"),
    metricsSummary: $("metrics-summary"),
    findingsCount: $("findings-count"),
    diScore: $("di-score"),
    diSummary: $("di-summary"),

    // Result blocks
    metricsTableBody: $("metrics-table-body"),
    findingsList: $("findings-list"),
    groupBreakdownBody: $("group-breakdown-body"),

    // Reports
    executiveSummaryBox: $("executive-summary-box"),
    reportMeta: $("report-meta"),
    downloadPdfBtn: $("download-pdf-btn"),
    downloadJsonBtn: $("download-json-btn"),

    // Meta
    datasetMeta: $("dataset-meta"),
  };

  /* ───────────────────────────────────────────────────────────
     INIT
  ─────────────────────────────────────────────────────────── */
  document.addEventListener("DOMContentLoaded", init);

  function init() {
    try {
      bindEvents();
      attachGlobalFunctions();
      showView("audit");
      switchTab("metrics");
      stepTo(1);
      updateRunButtonState();
      renderDashboardTrend();
      log("Frontend initialized successfully.");
    } catch (err) {
      console.error("Initialization error:", err);
      showToast("Frontend failed to initialize. Check console.");
    }
  }

  /* ───────────────────────────────────────────────────────────
     GLOBAL FUNCTIONS (for HTML onclick compatibility)
  ─────────────────────────────────────────────────────────── */
  function attachGlobalFunctions() {
    window.showView = showView;
    window.switchTab = switchTab;
    window.runAudit = runAudit;
    window.resetDemo = resetDemo;
  }

  /* ───────────────────────────────────────────────────────────
     EVENT BINDING
  ─────────────────────────────────────────────────────────── */
  function bindEvents() {
    // File inputs
    els.csvInput?.addEventListener("change", (e) => {
      const file = e.target.files?.[0];
      if (file) handleDatasetFile(file);
    });

    els.modelInput?.addEventListener("change", (e) => {
      const file = e.target.files?.[0];
      if (file) handleModelFile(file);
    });

    els.evalInput?.addEventListener("change", (e) => {
      const file = e.target.files?.[0];
      if (file) handleEvalFile(file);
    });

    // Run button
    els.runBtn?.addEventListener("click", (e) => {
      e.preventDefault();
      runAudit();
    });

    // Drag & Drop
    if (els.dropzone) {
      ["dragenter", "dragover"].forEach((eventName) => {
        els.dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          e.stopPropagation();
          els.dropzone.classList.add("drag");
        });
      });

      ["dragleave", "drop"].forEach((eventName) => {
        els.dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          e.stopPropagation();
          els.dropzone.classList.remove("drag");
        });
      });

      els.dropzone.addEventListener("drop", (e) => {
        const file = e.dataTransfer.files?.[0];
        if (!file) return;

        if (file.name.toLowerCase().endsWith(".csv")) {
          handleDatasetFile(file);
        } else {
          showToast("Only CSV files can be dropped here.");
        }
      });
    }
  }

  /* ───────────────────────────────────────────────────────────
     VIEW / TAB NAVIGATION
  ─────────────────────────────────────────────────────────── */
  function showView(viewName, el = null) {
    try {
      state.currentView = viewName;

      $$$(".view").forEach((view) => {
        view.style.display = "none";
        view.classList.remove("active");
      });

      const target = $(`view-${viewName}`);
      if (target) {
        target.style.display = "block";
        target.classList.add("active");
      }

      $$$(".nav-item").forEach((item) => item.classList.remove("active"));

      if (el) {
        el.classList.add("active");
      } else {
        const navMap = {
          audit: 0,
          dashboard: 1,
          reports: 2,
        };
        const idx = navMap[viewName];
        const navItems = $$$(".nav-item");
        if (navItems[idx]) navItems[idx].classList.add("active");
      }

      if (viewName === "dashboard") {
        setTimeout(() => renderDashboardTrend(), 100);
      }
    } catch (err) {
      console.error("showView error:", err);
    }
  }

  function switchTab(tabName, el = null) {
    try {
      state.currentTab = tabName;

      $$$(".tab").forEach((tab) => tab.classList.remove("active"));
      if (el) {
        el.classList.add("active");
      } else {
        const tabMap = {
          metrics: 0,
          findings: 1,
          groups: 2,
          summary: 3,
        };
        const idx = tabMap[tabName];
        const tabs = $$$(".tab");
        if (tabs[idx]) tabs[idx].classList.add("active");
      }

      $$$(".tab-content").forEach((content) => {
        content.style.display = "none";
      });

      const tabContent = $(`tab-${tabName}`);
      if (tabContent) {
        tabContent.style.display = "block";
      }

      if (tabName === "groups" && state.result) {
        setTimeout(() => renderGroupCharts(state.result), 100);
      }
    } catch (err) {
      console.error("switchTab error:", err);
    }
  }

  /* ───────────────────────────────────────────────────────────
     FILE HANDLING
  ─────────────────────────────────────────────────────────── */
  function handleDatasetFile(file) {
    if (!validateFile(file, [".csv"])) return;

    state.files.dataset = file;

    // If dataset mode is selected, clear model mode if incomplete
    if (!state.files.model && !state.files.evalDataset) {
      state.auditMode = "dataset";
    }

    if (els.uploadedFileName) els.uploadedFileName.textContent = file.name;
    if (els.datasetMeta) {
      els.datasetMeta.textContent = `${file.name} · ${(file.size / 1024).toFixed(1)} KB`;
    }

    showConfig();
    stepTo(2);
    updateRunButtonState();
    log(`Dataset selected: ${file.name}`);
  }

  function handleModelFile(file) {
    if (!validateFile(file, [".pkl", ".joblib", ".onnx"])) return;

    state.files.model = file;
    state.auditMode = "model";

    if (els.uploadedModelName) els.uploadedModelName.textContent = file.name;

    showConfig();
    stepTo(2);
    updateRunButtonState();
    log(`Model selected: ${file.name}`);
  }

  function handleEvalFile(file) {
    if (!validateFile(file, [".csv"])) return;

    state.files.evalDataset = file;
    if (state.files.model) {
      state.auditMode = "model";
    }

    if (els.uploadedEvalName) els.uploadedEvalName.textContent = file.name;

    showConfig();
    stepTo(2);
    updateRunButtonState();
    log(`Evaluation dataset selected: ${file.name}`);
  }

  function validateFile(file, allowedExtensions) {
    const ext = `.${file.name.split(".").pop().toLowerCase()}`;
    const isAllowed = allowedExtensions.includes(ext);

    if (!isAllowed) {
      showToast(`Invalid file type: ${file.name}`);
      return false;
    }

    const sizeMB = file.size / (1024 * 1024);
    if (sizeMB > CONFIG.MAX_UPLOAD_MB) {
      showToast(`File too large. Max allowed is ${CONFIG.MAX_UPLOAD_MB} MB.`);
      return false;
    }

    return true;
  }

  function updateRunButtonState() {
    const canRunDataset = !!state.files.dataset && !state.files.model && !state.files.evalDataset;
    const canRunModel = !!state.files.model && !!state.files.evalDataset;
    const canRun = canRunDataset || canRunModel;

    if (els.runBtn) {
      els.runBtn.disabled = !canRun;
      els.runBtn.style.opacity = canRun ? "1" : "0.55";
      els.runBtn.style.cursor = canRun ? "pointer" : "not-allowed";
    }
  }

  /* ───────────────────────────────────────────────────────────
     AUDIT FLOW
  ─────────────────────────────────────────────────────────── */
  async function runAudit() {
    try {
      if (!canRunAudit()) {
        showToast("Upload the correct required files before running the audit.");
        return;
      }

      state.auditState = "uploading";
      state.result = null;

      stepTo(3);
      showRunning();
      clearRunLog();
      setProgress(10);
      setRunStatus("Preparing audit request...");
      log(`Audit mode: ${state.auditMode}`);

      const formData = buildFormData();
      const endpoint =
        state.auditMode === "model"
          ? CONFIG.API_BASE + CONFIG.ENDPOINTS.modelAudit
          : CONFIG.API_BASE + CONFIG.ENDPOINTS.fairnessAudit;

      setProgress(35);
      setRunStatus("Sending request to backend...");
      log(`POST → ${endpoint}`);

  

      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });

      log(`Response status: ${response.status} ${response.statusText}`);

      if (!response.ok) {
        const errText = await safeReadError(response);
        throw new Error(errText || "Failed to run audit.");
      }

      setProgress(75);
      setRunStatus("Processing audit response...");
      log("Audit response received.");

      const data = await response.json();

      state.auditState = "completed";
      state.result = normalizeAuditResult(data);

      setProgress(100);
      setRunStatus("Audit completed successfully.");
      log("Audit completed.");

      stepTo(4);
      showResults();
      renderResults(state.result);
    } catch (error) {
      handleAuditFailure(error);
    }
  }

  function canRunAudit() {
    if (state.auditMode === "model") {
      return !!state.files.model && !!state.files.evalDataset;
    }
    return !!state.files.dataset;
  }

  function buildFormData() {
    const formData = new FormData();

    const targetColumn = els.targetColumn?.value?.trim() || "approved";
    const sensitiveColumns = els.sensitiveColumns?.value?.trim() || "gender,race";
    const yPredColumn = els.yPredColumn?.value?.trim() || "";
    const positiveLabel = els.positiveLabel?.value?.trim() || "1";

    formData.append("target_column", targetColumn);
    formData.append("sensitive_columns", sensitiveColumns);
    formData.append("positive_label", positiveLabel);

    if (state.auditMode === "model") {
      formData.append("model_file", state.files.model);
      formData.append("eval_file", state.files.evalDataset);
    } else {
      formData.append("file", state.files.dataset);
      if (yPredColumn) formData.append("y_pred_column", yPredColumn);
    }

    return formData;
  }

  function handleAuditFailure(error) {
    state.auditState = "failed";
    setProgress(100);
    setRunStatus("Audit failed.");
    log(`Error: ${error.message}`);
    console.error("Audit failed:", error);
    showToast(error.message || "Something went wrong.");
  }

  /* ───────────────────────────────────────────────────────────
     NORMALIZATION
  ─────────────────────────────────────────────────────────── */
  function normalizeAuditResult(raw = {}) {
    const rawMetrics = raw.fairness_metrics || raw.metrics || [];
    const rawFindings = raw.findings || raw.bias_findings || [];
    const rawSubgroup = raw.subgroup_performance || [];
    const rawMetricsSource = raw.fairness_metrics || raw.metrics || [];
    const rawReports = raw.report_urls || raw.reports || {};
    const rawPerformance = raw.performance || {};
    const rawMeta = raw.model_meta || {};

    const normalizedMetrics = rawMetrics.map((m) => ({
      attribute: m.attribute || m.sensitive_attribute || "-",
      metric: m.metric || m.metric_name || m.name || "-",
      value: m.value ?? null,
      threshold: m.threshold ?? null,
      status:
        m.status ||
        (typeof m.passed === "boolean" ? (m.passed ? "pass" : "fail") : "unknown"),
      severity:
        m.severity ||
        inferMetricSeverity(m.metric_name || m.metric, m.value, m.threshold, m.passed),
      details: m.details || {},
    }));

    const normalizedFindings = rawFindings.map((f) => ({
      title: f.title || f.issue || f.finding_type || "Bias Finding",
      severity: f.severity || "medium",
      description: f.description || "No description provided.",
      recommendation: f.recommendation || "",
      attribute: f.attribute || "",
      raw_data: f.raw_data || {},
    }));

    
      const normalizedGroupAnalysis =
        rawSubgroup.length > 0
          ? subgroupPerformanceToGroupAnalysis(rawSubgroup)
          : metricsToGroupAnalysis(rawMetricsSource);

    const metricsFailed = normalizedMetrics.filter((m) => m.status === "fail").length;
    const metricsTotal = normalizedMetrics.length;

    const diMetric = normalizedMetrics.find(
      (m) => String(m.metric).toLowerCase() === "disparate_impact"
    );

    const riskScore =
      raw.summary?.risk_score ??
      raw.risk_score ??
      raw.overall_risk_score ??
      computeFallbackRiskScore(normalizedMetrics);

    return {
      summary: {
        risk_score: Number(riskScore || 0),
        metrics_failed: metricsFailed,
        metrics_total: metricsTotal,
        findings_count: normalizedFindings.length,
        disparate_impact: diMetric?.value ?? null,
        executive_summary:
          raw.summary?.executive_summary ||
          raw.executive_summary ||
          "Audit completed. Review the detailed metrics and findings below.",
      },
      fairness_metrics: normalizedMetrics,
      findings: normalizedFindings,
      group_analysis: normalizedGroupAnalysis,
      subgroup_performance: rawSubgroup,
      reports: {
        pdf_url: rawReports.pdf || rawReports.pdf_url || null,
        json_url: rawReports.json || rawReports.json_url || null,
      },
      performance: rawPerformance,
      model_meta: rawMeta,
      raw,
    };
  }

  function subgroupPerformanceToGroupAnalysis(subgroups = []) {
    const grouped = {};
    if (!Array.isArray(subgroups)) return grouped;

    subgroups.forEach((row) => {
      const attr = row.sensitive_attribute || "unknown";
      if (!grouped[attr]) grouped[attr] = [];

      grouped[attr].push({
        group: row.group || "Unknown",
        approval_rate:
        row.approval_rate ??
        row.selection_rate ??
        row.positive_rate ??
        row.recall ??
        row.accuracy ??
        row.f1 ??
        0,

        accuracy: row.accuracy ?? null,
        precision: row.precision ?? null,
        recall: row.recall ?? null,
        f1: row.f1 ?? null,
        fpr: row.fpr ?? null,
        fnr: row.fnr ?? null,
        n_samples: row.n_samples ?? null,
      });
    });

    return grouped;
  }

  function metricsToGroupAnalysis(metrics = []) {
    const grouped = {};

    if (!Array.isArray(metrics)) return grouped;

    metrics.forEach((metric) => {
      const attr = metric.sensitive_attribute || metric.attribute;
      const metricName = metric.metric_name || metric.metric;
      const details = metric.details || {};

    // We only want approval-style chart data from demographic parity / disparate impact style metrics
      if (!attr || !details || typeof details !== "object") return;

    // Best metric to use for "approval rate" charts
      if (metricName !== "demographic_parity" && metricName !== "disparate_impact") return;

      if (!grouped[attr]) grouped[attr] = [];

      Object.entries(details).forEach(([groupName, value]) => {
      // Avoid duplicate entries if same group already added
        const alreadyExists = grouped[attr].some((g) => g.group === groupName);
        if (!alreadyExists) {
          grouped[attr].push({
            group: groupName,
            approval_rate: Number(value) || 0,
          });
        }
      });
    });

    return grouped;
  }

  /* ───────────────────────────────────────────────────────────
     RENDERING
  ─────────────────────────────────────────────────────────── */
  function renderResults(result) {
    renderSummaryCards(result.summary);
    renderMetricsTable(result.fairness_metrics);
    renderFindings(result.findings);
    renderGroupBreakdown(result.group_analysis);
    renderExecutiveSummary(result.summary);
    renderReportLinks(result.reports);

    if (state.currentTab === "groups") {
      setTimeout(() => renderGroupCharts(result), 100);
    }
  }

  function renderSummaryCards(summary) {
    const riskScore = Number(summary.risk_score || 0);
    const metricsFailed = Number(summary.metrics_failed || 0);
    const metricsTotal = Number(summary.metrics_total || 0);
    const findingsCount = Number(summary.findings_count || 0);
    const di = summary.disparate_impact;

    if (els.riskScoreVal) els.riskScoreVal.textContent = riskScore.toFixed(2);

    if (els.riskScoreLabel) {
      els.riskScoreLabel.textContent = riskLabel(riskScore);
      els.riskScoreLabel.className = `pill ${riskPillClass(riskScore)}`;
    }

    if (els.metricsFailed) els.metricsFailed.textContent = metricsFailed;
    if (els.metricsTotal) els.metricsTotal.textContent = metricsTotal;

    if (els.metricsSummary) {
      els.metricsSummary.textContent =
        metricsTotal > 0
          ? `${metricsFailed} of ${metricsTotal} fairness checks failed`
          : "No metrics available";
    }

    if (els.findingsCount) els.findingsCount.textContent = findingsCount;

    if (els.diScore) {
      els.diScore.textContent =
        di !== null && di !== undefined && di !== "" ? Number(di).toFixed(2) : "N/A";
    }

    if (els.diSummary) {
      els.diSummary.textContent =
        di !== null && di !== undefined
          ? Number(di) >= 0.8
            ? "Within commonly accepted range"
            : "Potential impact disparity detected"
          : "No disparate impact value available";
    }
  }

  function renderMetricsTable(metrics = []) {
    if (!els.metricsTableBody) return;

    els.metricsTableBody.innerHTML = "";

    if (!Array.isArray(metrics) || metrics.length === 0) {
      els.metricsTableBody.innerHTML = `
        <tr>
          <td colspan="6" class="muted">No fairness metrics returned from backend.</td>
        </tr>
      `;
      return;
    }

    metrics.forEach((metric) => {
      const status = String(metric.status || "unknown").toLowerCase();
      const severity = String(metric.severity || "low").toLowerCase();

      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${escapeHtml(metric.attribute || "-")}</td>
        <td>${escapeHtml(metric.metric || "-")}</td>
        <td>${formatMetricValue(metric.value)}</td>
        <td>${formatMetricValue(metric.threshold)}</td>
        <td><span class="pill ${status === "pass" ? "pill-pass" : "pill-fail"}">${status.toUpperCase()}</span></td>
        <td><span class="pill ${severityPillClass(severity)}">${severity.toUpperCase()}</span></td>
      `;
      els.metricsTableBody.appendChild(row);
    });
  }

  function renderFindings(findings = []) {
    if (!els.findingsList) return;

    els.findingsList.innerHTML = "";

    if (!Array.isArray(findings) || findings.length === 0) {
      els.findingsList.innerHTML = `
        <div class="card">No bias findings detected. Your model behaved... suspiciously well.</div>
      `;
      return;
    }

    findings.forEach((finding) => {
      const severity = String(finding.severity || "low").toLowerCase();

      const div = document.createElement("div");
      div.className = "finding";
      div.innerHTML = `
        <div class="finding-hdr">
          <div class="finding-title">${escapeHtml(finding.title || "Bias Finding")}</div>
          <span class="pill ${severityPillClass(severity)}">${severity.toUpperCase()}</span>
        </div>
        <div class="finding-desc">${escapeHtml(finding.description || "No description provided.")}</div>
        ${
          finding.recommendation
            ? `<div class="finding-rec"><strong>Recommendation:</strong> ${escapeHtml(finding.recommendation)}</div>`
            : ""
        }
      `;
      els.findingsList.appendChild(div);
    });
  }

  function renderGroupBreakdown(groupAnalysis = {}) {
    if (!els.groupBreakdownBody) return;

    els.groupBreakdownBody.innerHTML = "";

    const flatGroups = flattenGroupAnalysis(groupAnalysis);

    if (flatGroups.length === 0) {
      els.groupBreakdownBody.innerHTML = `
        <tr>
          <td colspan="3" class="muted">No group analysis returned from backend.</td>
        </tr>
      `;
      return;
    }

    flatGroups.forEach((row) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${escapeHtml(row.group)}</td>
        <td>${escapeHtml(row.attribute)}</td>
        <td>${formatPercent(row.approval_rate)}</td>
      `;
      els.groupBreakdownBody.appendChild(tr);
    });
  }

  function renderExecutiveSummary(summary) {
    if (!els.executiveSummaryBox) return;

    els.executiveSummaryBox.innerHTML = `
      <strong>Risk Score:</strong> ${Number(summary.risk_score || 0).toFixed(2)}<br/>
      <strong>Failed Checks:</strong> ${summary.metrics_failed || 0} / ${summary.metrics_total || 0}<br/><br/>
      ${escapeHtml(summary.executive_summary || "No executive summary available.")}
    `;
  }

  
  function renderReportLinks(reports = {}) {
    const pdfHref = resolveReportUrl(reports.pdf_url);
    const jsonHref = resolveReportUrl(reports.json_url);

    if (els.downloadPdfBtn) {
      els.downloadPdfBtn.href = pdfHref || "#";
      els.downloadPdfBtn.target = "_blank";
      els.downloadPdfBtn.style.pointerEvents = pdfHref ? "auto" : "none";
      els.downloadPdfBtn.style.opacity = pdfHref ? "1" : "0.5";
    }

    if (els.downloadJsonBtn) {
      els.downloadJsonBtn.href = jsonHref || "#";
      els.downloadJsonBtn.target = "_blank";
      els.downloadJsonBtn.style.pointerEvents = jsonHref ? "auto" : "none";
      els.downloadJsonBtn.style.opacity = jsonHref ? "1" : "0.5";
    }

    if (els.reportMeta) {
      els.reportMeta.textContent =
        pdfHref || jsonHref
          ? "Report package ready for download."
          : "Reports not generated yet by backend.";
    }

    log(`PDF report URL: ${pdfHref || "Not available"}`);
    log(`JSON report URL: ${jsonHref || "Not available"}`);
  }

  // Helper function 
  function resolveReportUrl(url) {
    if (!url) return null;

    const cleanUrl = String(url).replace(/\\/g, "/").trim();

  // Already full URL
    if (cleanUrl.startsWith("http://") || cleanUrl.startsWith("https://")) {
      return cleanUrl;
    }

  // If backend already returns /reports/...
    if (cleanUrl.startsWith("/reports/")) {
      return `${CONFIG.API_BASE}${cleanUrl}`;
    }

  // If backend returns reports/...
    if (cleanUrl.startsWith("reports/")) {
      return `${CONFIG.API_BASE}/${cleanUrl}`;
    }

  // If backend returns only filename like audit_report.pdf
    return `${CONFIG.API_BASE}/reports/${cleanUrl.split("/").pop()}`;
  }


  // Render bar Charts 
  function renderBarChart(canvasId, label, rows, chartKey) {
    const canvas = $(canvasId);
    if (!canvas || typeof Chart === "undefined") return;

    if (state.charts[chartKey]) {
      state.charts[chartKey].destroy();
    }

    state.charts[chartKey] = new Chart(canvas, {
      type: "bar",
      data: {
        labels: rows.map((r) => r.group),
        datasets: [
          {
            label,
            data: rows.map((r) => Number(r.approval_rate || 0)),
            borderRadius: 10,
            borderSkipped: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `${(ctx.raw * 100).toFixed(1)}%`,
            },
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 1,
            ticks: {
              callback: (value) => `${Math.round(value * 100)}%`,
            },
          },
        },
      },
    });
  }

  function renderGroupCharts(result) {
  try {
    if (!result || !result.group_analysis) {
      console.warn("No group analysis available for charts.");
      return;
    }

    const groupAnalysis = result.group_analysis;
    const keys = Object.keys(groupAnalysis || {});

    const firstKey = keys[0];
    const secondKey = keys[1];

    const firstRows = firstKey ? groupAnalysis[firstKey] : [];
    const secondRows = secondKey ? groupAnalysis[secondKey] : [];

    if (firstRows && firstRows.length > 0) {
      renderBarChart("chartRace", `${firstKey} Approval Rate`, firstRows, "race");
    } else {
      clearChartCanvas("chartRace", "No data available");
    }

    if (secondRows && secondRows.length > 0) {
      renderBarChart("chartGender", `${secondKey} Approval Rate`, secondRows, "gender");
    } else {
      clearChartCanvas("chartGender", "No data available");
    }

    }   catch (err) {
      console.error("renderGroupCharts error:", err);
    }
  }

  function clearChartCanvas(canvasId, message = "No data") {
  const canvas = $(canvasId);
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.font = "16px sans-serif";
  ctx.fillStyle = "#9aa6d1";
  ctx.textAlign = "center";
  ctx.fillText(message, canvas.width / 2, canvas.height / 2);
  ctx.restore();
  }

  function renderDashboardTrend() {
    const canvas = $("chartTrend");
    if (!canvas || typeof Chart === "undefined") return;

    if (state.charts.trend) {
      state.charts.trend.destroy();
    }

    state.charts.trend = new Chart(canvas, {
      type: "line",
      data: {
        labels: ["Run 1", "Run 2", "Run 3"],
        datasets: [
          {
            label: "Risk Score",
            data: [0.71, 0.58, 0.54],
            tension: 0.35,
            fill: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 1,
          },
        },
      },
    });
  }

  /* ───────────────────────────────────────────────────────────
     UI HELPERS
  ─────────────────────────────────────────────────────────── */
  function showConfig() {
    if (els.configSection) els.configSection.style.display = "block";
  }

  function showRunning() {
    if (els.runningSection) els.runningSection.style.display = "block";
    if (els.resultsSection) els.resultsSection.style.display = "none";
  }

  function showResults() {
    if (els.runningSection) els.runningSection.style.display = "none";
    if (els.resultsSection) els.resultsSection.style.display = "block";
  }

  function stepTo(stepNumber) {
    [1, 2, 3, 4].forEach((n) => {
      const step = $(`step${n}`);
      if (!step) return;

      step.classList.remove("done", "active", "idle");

      if (n < stepNumber) step.classList.add("done");
      else if (n === stepNumber) step.classList.add("active");
      else step.classList.add("idle");
    });
  }

  function setProgress(percent) {
    if (els.progressBar) {
      els.progressBar.style.width = `${Math.max(0, Math.min(100, percent))}%`;
    }
  }

  function setRunStatus(message) {
    if (els.runStatus) {
      els.runStatus.textContent = message;
    }
  }

  function clearRunLog() {
    if (els.runLog) {
      els.runLog.innerHTML = "";
    }
  }

  function log(message) {
    if (!els.runLog) return;

    const line = document.createElement("div");
    line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    els.runLog.appendChild(line);
    els.runLog.scrollTop = els.runLog.scrollHeight;
  }

  function resetDemo() {
    try {
      state.auditState = "idle";
      state.result = null;
      state.auditMode = "dataset";
      state.currentView = "audit";
      state.currentTab = "metrics";

      state.files = {
        dataset: null,
        model: null,
        evalDataset: null,
      };

      if (els.csvInput) els.csvInput.value = "";
      if (els.modelInput) els.modelInput.value = "";
      if (els.evalInput) els.evalInput.value = "";

      if (els.uploadedFileName) els.uploadedFileName.textContent = "No file selected";
      if (els.uploadedModelName) els.uploadedModelName.textContent = "No model selected";
      if (els.uploadedEvalName) els.uploadedEvalName.textContent = "No dataset selected";
      if (els.datasetMeta) els.datasetMeta.textContent = "Upload a CSV to begin";

      if (els.configSection) els.configSection.style.display = "none";
      if (els.runningSection) els.runningSection.style.display = "none";
      if (els.resultsSection) els.resultsSection.style.display = "none";

      clearRunLog();
      setProgress(0);
      setRunStatus("Initializing audit engine...");

      stepTo(1);
      updateRunButtonState();
      showView("audit");
      switchTab("metrics");
      log("Reset complete.");
    } catch (err) {
      console.error("Reset error:", err);
    }
  }

  /* ───────────────────────────────────────────────────────────
     UTILITIES
  ─────────────────────────────────────────────────────────── */
  function flattenGroupAnalysis(groupAnalysis = {}) {
    const rows = [];

    Object.entries(groupAnalysis || {}).forEach(([attribute, groups]) => {
      if (Array.isArray(groups)) {
        groups.forEach((g) => {
          rows.push({
            attribute,
            group: g.group || g.name || "Unknown",
            approval_rate: g.approval_rate ?? g.value ?? 0,
          });
        });
      } else if (typeof groups === "object" && groups !== null) {
        Object.entries(groups).forEach(([groupName, value]) => {
          rows.push({
            attribute,
            group: groupName,
            approval_rate:
              typeof value === "object"
                ? value.approval_rate ?? value.value ?? 0
                : value,
          });
        });
      }
    });

    return rows;
  }

  function computeFallbackRiskScore(metrics = []) {
    if (!Array.isArray(metrics) || metrics.length === 0) return 0;
    const failed = metrics.filter((m) => m.status === "fail").length;
    return Number((failed / metrics.length).toFixed(4));
  }

  function inferMetricSeverity(metricName, value, threshold, passed) {
    if (passed === true) return "low";

    const metric = String(metricName || "").toLowerCase();
    const val = Number(value);
    const thr = Number(threshold);

    if (metric === "disparate_impact") {
      if (val < 0.5) return "critical";
      if (val < 0.65) return "high";
      if (val < 0.8) return "medium";
      return "low";
    }

    if (!Number.isNaN(val) && !Number.isNaN(thr)) {
      if (val >= thr + 0.25) return "critical";
      if (val >= thr + 0.15) return "high";
      if (val > thr) return "medium";
    }

    return "medium";
  }

  function formatMetricValue(value) {
    if (value === null || value === undefined || value === "") return "—";
    if (typeof value === "number") return value.toFixed(3);
    const parsed = Number(value);
    return Number.isNaN(parsed) ? escapeHtml(String(value)) : parsed.toFixed(3);
  }

  function formatPercent(value) {
    const num = Number(value);
    if (Number.isNaN(num)) return "—";
    return `${(num * 100).toFixed(1)}%`;
  }

  function riskLabel(score) {
    if (score >= 0.75) return "CRITICAL";
    if (score >= 0.5) return "HIGH";
    if (score >= 0.25) return "MEDIUM";
    return "LOW";
  }

  function riskPillClass(score) {
    if (score >= 0.75) return "pill-critical";
    if (score >= 0.5) return "pill-high";
    if (score >= 0.25) return "pill-medium";
    return "pill-low";
  }

  function severityPillClass(severity) {
    if (severity === "critical") return "pill-critical";
    if (severity === "high") return "pill-high";
    if (severity === "medium") return "pill-medium";
    return "pill-low";
  }

  function escapeHtml(str = "") {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  async function safeReadError(response) {
    try {
      const data = await response.json();

      if (data?.detail) {
        if (Array.isArray(data.detail)) {
          return data.detail.map((d) => d.msg || JSON.stringify(d)).join(" | ");
        }
        if (typeof data.detail === "string") {
          return data.detail;
        }
      }

      return JSON.stringify(data);
    } catch {
      try {
        return await response.text();
      } catch {
        return "Unknown backend error.";
      }
    }
  }

  function showToast(message) {
    alert(message);
  }
})();