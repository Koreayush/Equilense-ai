import React from 'react';
import { 
  BarChart3, 
  AlertTriangle, 
  CheckCircle2, 
  Download, 
  FileJson, 
  FileText,
  FileDown,
  FileCode,
  ShieldCheck,
  Info,
  ArrowLeft,
  LayoutDashboard,
  Zap,
  Layers,
  Target,
  Users,
  ArrowRight
} from 'lucide-react';
import { Card, MetricCard } from '../ui/Cards';
import { cn } from '../../lib/utils';
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip,
  Legend,
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis
} from 'recharts';
import useStore from '../../store/useStore';

const AuditResults = () => {
  const { auditResult: result, setActiveTab, recentReports } = useStore();

  if (!result) {
    return (
      <div className="space-y-10 animate-fade-in pb-20">
        <div className="flex flex-col items-center justify-center min-h-[40vh]">
          <div className="w-24 h-24 bg-slate-100 rounded-3xl flex items-center justify-center mb-8 shadow-inner">
            <FileText className="w-12 h-12 text-slate-300" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Report Vault</h2>
          <p className="text-slate-500 mt-3 text-center max-w-md font-medium">
            {recentReports.length > 0 
              ? "Select an audit from the history below or initiate a new one."
              : "Generate your first fairness report by initiating a Layer 1 or Layer 2 audit."}
          </p>
          <div className="flex gap-4 mt-10">
            <button onClick={() => setActiveTab('dataset-audit')} className="btn-secondary flex items-center gap-2">
              <Zap className="w-4 h-4 text-brand-600" /> Dataset Audit
            </button>
            <button onClick={() => setActiveTab('model-audit')} className="btn-primary flex items-center gap-2">
              <Layers className="w-4 h-4" /> Model Audit
            </button>
          </div>
        </div>

        {recentReports.length > 0 && (
          <div className="max-w-4xl mx-auto space-y-6">
            <h3 className="text-sm font-black text-slate-400 uppercase tracking-widest px-2">History ({recentReports.length})</h3>
            <div className="grid grid-cols-1 gap-4">
              {recentReports.map((report) => (
                <div 
                  key={report.id} 
                  className="group bg-white p-6 rounded-[2rem] border border-slate-200 hover:border-brand-400 hover:shadow-2xl hover:shadow-brand-500/10 transition-all cursor-pointer flex items-center justify-between"
                  onClick={() => useStore.getState().setAuditResult(report)}
                >
                  <div className="flex items-center gap-5">
                    <div className={cn(
                      "w-12 h-12 rounded-2xl flex items-center justify-center",
                      report.performance ? "bg-brand-50 text-brand-600" : "bg-emerald-50 text-emerald-600"
                    )}>
                      {report.performance ? <ShieldCheck className="w-6 h-6" /> : <BarChart3 className="w-6 h-6" />}
                    </div>
                    <div>
                      <h4 className="font-bold text-slate-900 tracking-tight">
                        {report.performance ? 'Layer 2: Model Audit' : 'Layer 1: Dataset Audit'}
                      </h4>
                      <p className="text-xs text-slate-400 font-medium">
                        {new Date(report.timestamp).toLocaleString()} • {report.findings.length} findings
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-8">
                     <div className="text-right">
                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Risk Score</p>
                        <p className={cn(
                          "text-lg font-black tracking-tight",
                          report.overall_risk_score > 0.75 ? "text-rose-500" : report.overall_risk_score > 0.4 ? "text-amber-500" : "text-emerald-500"
                        )}>
                          {(report.overall_risk_score * 100).toFixed(0)}%
                        </p>
                     </div>
                     <div className="w-10 h-10 rounded-full border border-slate-100 flex items-center justify-center group-hover:bg-brand-600 group-hover:text-white transition-all">
                        <ArrowRight className="w-4 h-4" />
                     </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  const { 
    overall_risk_score = 0, 
    executive_summary = "", 
    metrics = [], 
    findings = [], 
    report_urls = {},
    performance = null,
    subgroup_performance = [],
    model_meta = {}
  } = result || {};
  
  const isModelAudit = !!performance;
  const riskPercent = (overall_risk_score * 100);
  const riskColor = riskPercent > 75 ? '#ef4444' : riskPercent > 40 ? '#f59e0b' : '#10b981';
  
  const pieData = [
    { name: 'Risk', value: riskPercent },
    { name: 'Fairness', value: 100 - riskPercent },
  ];

  // Radar chart data for fairness metrics
  const radarData = (metrics || []).map(m => ({
    subject: (m.metric_name || "Unknown").split('_').map(w => w[0].toUpperCase() + w.slice(1)).join(' '),
    A: m.value || 0,
    fullMark: 1,
  }));

  return (
    <div className="space-y-10 pb-20 animate-fade-in">
      {/* Dynamic Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-8 bg-white p-8 rounded-[2.5rem] border border-slate-200/60 shadow-xl shadow-slate-200/20">
        <div className="flex items-start gap-6">
          <div className={cn(
            "w-16 h-16 rounded-2xl flex items-center justify-center shadow-lg transition-transform hover:scale-105 cursor-pointer",
            isModelAudit ? "bg-brand-600 shadow-brand-200" : "bg-emerald-600 shadow-emerald-200"
          )} onClick={() => setActiveTab('dashboard')}>
            {isModelAudit ? <ShieldCheck className="text-white w-8 h-8" /> : <BarChart3 className="text-white w-8 h-8" />}
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <span className={cn(
                "text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-full",
                isModelAudit ? "bg-brand-50 text-brand-700" : "bg-emerald-50 text-emerald-700"
              )}>
                {isModelAudit ? 'Layer 2: Model Performance & Bias' : 'Layer 1: Dataset Bias Audit'}
              </span>
              <span className="text-[10px] text-slate-400 font-bold bg-slate-100 px-3 py-1 rounded-full">
                ID: {Math.random().toString(36).substr(2, 9).toUpperCase()}
              </span>
            </div>
            <h1 className="text-3xl font-black text-slate-900 tracking-tighter">
              Fairness Assurance Report
            </h1>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <button 
            onClick={() => useStore.getState().resetResults()}
            className="btn-secondary flex items-center gap-2 py-3 px-5"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm font-bold tracking-tight">Return to Vault</span>
          </button>
          {report_urls && (
            <>
              <a 
                href={report_urls.pdf || "#"} 
                target="_blank" 
                rel="noopener noreferrer"
                className="btn-secondary flex items-center gap-2 py-3 px-5 group"
              >
                <FileDown className="w-4 h-4 text-slate-400 group-hover:text-brand-600 transition-colors" />
                <span className="text-sm font-bold tracking-tight">Export PDF Report</span>
              </a>
              <a 
                href={report_urls.json || "#"} 
                target="_blank" 
                rel="noopener noreferrer"
                className="btn-secondary flex items-center gap-2 py-3 px-5 group"
              >
                <FileCode className="w-4 h-4 text-slate-400 group-hover:text-brand-600 transition-colors" />
                <span className="text-sm font-bold tracking-tight">Raw Data (JSON)</span>
              </a>
            </>
          )}
        </div>
      </div>

      {/* Hero Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Risk Score Gauge */}
        <Card className="lg:col-span-4 flex flex-col items-center justify-center text-center py-12 bg-gradient-to-b from-white to-slate-50/50">
          <div className="relative w-56 h-56 mb-8">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={85}
                  outerRadius={105}
                  paddingAngle={8}
                  dataKey="value"
                  startAngle={90}
                  endAngle={450}
                  stroke="none"
                >
                  <Cell fill={riskColor} />
                  <Cell fill="#e2e8f0" />
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <p className="text-6xl font-black text-slate-900 leading-none tracking-tighter" style={{ color: riskColor }}>
                {riskPercent.toFixed(0)}%
              </p>
              <p className="text-[11px] font-black text-slate-400 uppercase tracking-widest mt-3">Risk Assessment</p>
            </div>
          </div>
          <div className={cn(
            "px-6 py-2 rounded-2xl text-xs font-black uppercase tracking-widest shadow-sm",
            riskPercent > 75 ? "bg-rose-100 text-rose-700" : 
            riskPercent > 40 ? "bg-amber-100 text-amber-700" : "bg-emerald-100 text-emerald-700"
          )}>
            {riskPercent > 75 ? 'Critical Warning' : riskPercent > 40 ? 'Action Required' : 'Compliance Ready'}
          </div>
        </Card>

        {/* Executive summary & Performance */}
        <div className="lg:col-span-8 space-y-8">
          <Card title="Executive Insight" action={<Info className="w-5 h-5 text-slate-300" />}>
            <div className="bg-slate-50/80 backdrop-blur-sm p-8 rounded-3xl border border-slate-100/50">
              <p className="text-slate-700 leading-relaxed font-semibold italic text-lg">
                "{executive_summary}"
              </p>
            </div>
            
            {/* Performance Metrics for Model Audit */}
            {isModelAudit && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
                {Object.entries(performance).map(([key, val]) => (
                  <div key={key} className="p-4 rounded-2xl border border-slate-100 bg-white shadow-sm hover:shadow-md transition-shadow">
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{key.replace('_', ' ')}</p>
                    <p className="text-2xl font-black text-slate-900 tracking-tight">{(val * 100).toFixed(1)}%</p>
                  </div>
                ))}
              </div>
            )}
          </Card>
          
          {!isModelAudit && (
             <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <MetricCard title="Bias Metrics" value={metrics.length} icon={Target} color="brand" />
                <MetricCard title="Total Findings" value={findings.length} icon={AlertTriangle} color="rose" trend={-4} />
                <MetricCard title="Success Rate" value={((metrics.filter(m => m.passed).length / metrics.length) * 100).toFixed(0) + "%"} icon={CheckCircle2} color="emerald" />
             </div>
          )}
        </div>
      </div>

      {/* Fairness Visualization */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card title="Harmonization Index" subtitle="Radar analysis of fairness metric distribution">
          <div className="h-[400px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 10, fontWeight: 700 }} />
                <PolarRadiusAxis angle={30} domain={[0, 1]} tick={false} axisLine={false} />
                <Radar
                  name="Score"
                  dataKey="A"
                  stroke={isModelAudit ? "#0284c7" : "#059669"}
                  fill={isModelAudit ? "#0ea5e9" : "#10b981"}
                  fillOpacity={0.5}
                />
                <Tooltip 
                  contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1)' }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Policy Compliance" subtitle="Fairness metrics vs. configured thresholds">
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metrics} layout="vertical" margin={{ left: 20, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#f1f5f9" />
                <XAxis type="number" domain={[0, 1]} axisLine={false} tickLine={false} tick={{fill: '#94a3b8', fontSize: 10}} />
                <YAxis 
                  type="category" 
                  dataKey="metric_name" 
                  width={140} 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{fill: '#1e293b', fontSize: 10, fontWeight: 800}} 
                  tickFormatter={(val) => val.split('_').map(w => w[0].toUpperCase() + w.slice(1)).join(' ')}
                />
                <Tooltip 
                   cursor={{fill: '#f8fafc'}}
                   contentStyle={{ backgroundColor: '#fff', border: 'none', borderRadius: '16px', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                />
                <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={24}>
                  {metrics.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.passed ? '#10b981' : '#f43f5e'} />
                  ))}
                </Bar>
                <Bar dataKey="threshold" fill="#f1f5f9" barSize={12} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Subgroup Performance Table (Layer 2 Only) */}
      {isModelAudit && subgroup_performance && (
        <Card 
          title="Demographic Performance Analysis" 
          subtitle="Precision and Accuracy breakdown across protected subgroups"
          action={<Users className="w-6 h-6 text-slate-400" />}
        >
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50/50">
                <tr className="text-left border-b border-slate-100">
                  <th className="px-6 py-4 font-black text-slate-900 text-[10px] uppercase tracking-widest">Sensitive Subgroup</th>
                  <th className="px-6 py-4 font-black text-slate-900 text-[10px] uppercase tracking-widest">Precision</th>
                  <th className="px-6 py-4 font-black text-slate-900 text-[10px] uppercase tracking-widest">Accuracy</th>
                  <th className="px-6 py-4 font-black text-slate-900 text-[10px] uppercase tracking-widest">Recall</th>
                  <th className="px-6 py-4 font-black text-slate-900 text-[10px] uppercase tracking-widest text-right">Violation Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {Object.entries(subgroup_performance).map(([group, perf], i) => (
                  <tr key={i} className="hover:bg-slate-50/30 transition-colors group">
                    <td className="px-6 py-5">
                      <span className="font-black text-slate-900 text-sm tracking-tight">{group.replace(/_/g, ' ')}</span>
                    </td>
                    <td className="px-6 py-5 font-bold text-slate-600 text-sm">{(perf.precision * 100).toFixed(1)}%</td>
                    <td className="px-6 py-5 font-bold text-slate-600 text-sm">{(perf.accuracy * 100).toFixed(1)}%</td>
                    <td className="px-6 py-5 font-bold text-slate-600 text-sm">{(perf.recall * 100).toFixed(1)}%</td>
                    <td className="px-6 py-5 text-right">
                      <div className={cn(
                        "inline-flex w-3 h-3 rounded-full animate-pulse",
                        perf.accuracy < performance.accuracy - 0.05 ? "bg-rose-500 shadow-xl shadow-rose-200" : "bg-emerald-500 shadow-xl shadow-emerald-200"
                      )} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Risk Categorization & Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-1 gap-8">
        <Card 
          title="Actionable Mitigation Strategy" 
          subtitle="Identified behavioral concerns and corresponding technical resolutions"
          action={<LayoutDashboard className="w-6 h-6 text-brand-600" />}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {findings.map((finding, i) => (
              <div key={i} className="group p-6 rounded-[2rem] bg-white border border-slate-100 hover:border-brand-300 hover:shadow-2xl hover:shadow-brand-500/10 transition-all duration-300 flex flex-col">
                <div className="flex items-start justify-between mb-4">
                  <div className={cn(
                    "p-3 rounded-2xl",
                    finding.severity === 'critical' ? "bg-rose-50 text-rose-600" : 
                    finding.severity === 'high' ? "bg-amber-50 text-amber-600" : "bg-blue-50 text-blue-600"
                  )}>
                    {finding.severity === 'critical' || finding.severity === 'high' ? <AlertTriangle className="w-6 h-6" /> : <Info className="w-6 h-6" />}
                  </div>
                  <span className={cn(
                    "text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-lg",
                    finding.severity === 'critical' ? "bg-rose-600 text-white" : 
                    finding.severity === 'high' ? "bg-amber-100 text-amber-600" : "bg-blue-50 text-blue-700"
                  )}>
                    {finding.severity}
                  </span>
                </div>
                
                <h4 className="font-extrabold text-slate-900 group-hover:text-brand-700 transition-colors uppercase tracking-tight text-sm mb-1">
                  {finding.finding_type.split('_').join(' ')}
                </h4>
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Attribute: {finding.attribute}</p>
                
                <p className="text-slate-600 text-sm leading-relaxed mb-8 flex-1">
                  {finding.description}
                </p>
                
                <div className="mt-auto pt-6 border-t border-slate-50">
                  <p className="text-[10px] font-black text-slate-900 uppercase tracking-widest mb-3 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Resolution Logic
                  </p>
                  <p className="text-sm text-slate-500 font-medium italic leading-relaxed">
                    "{finding.recommendation}"
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default AuditResults;
