import React from 'react';
import { 
  BarChart3, 
  History, 
  ShieldCheck, 
  AlertTriangle, 
  ArrowRight, 
  FileSearch,
  Zap,
  Layers,
  BrainCircuit,
  ArrowUpRight,
  TrendingUp,
  Activity
} from 'lucide-react';
import { Card } from '../ui/Cards';
import { cn } from '../../lib/utils';
import useStore from '../../store/useStore';
import { ResponsiveContainer, BarChart, Bar, XAxis, Tooltip } from 'recharts';

const Overview = () => {
  const { setActiveTab, setAuditResult, recentReports, isLoading } = useStore();

  const handleAuditClick = (report) => {
    setAuditResult(report);
    setActiveTab('audit-results');
  };

  // Aggregated Stats
  const totalAudits = recentReports.length;
  const avgRisk = recentReports.length > 0 
    ? recentReports.reduce((acc, curr) => acc + curr.overall_risk_score, 0) / totalAudits
    : 0;
  const totalFindings = recentReports.reduce((acc, curr) => acc + curr.findings.length, 0);

  return (
    <div className="max-w-7xl mx-auto space-y-10 animate-fade-in pb-20">
      {/* Hero Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-50 border border-brand-100 text-brand-700 text-[10px] font-black uppercase tracking-widest">
            <span className="w-1.5 h-1.5 rounded-full bg-brand-500 animate-pulse" /> System Active
          </div>
          <h1 className="text-4xl font-black text-slate-900 tracking-tight">Enterprise Trust Dashboard</h1>
          <p className="text-slate-500 font-medium max-w-xl">
            Real-time monitoring of decision fairness across your model ecosystem.
          </p>
        </div>
        
        <div className="flex gap-3">
          <button 
            onClick={() => setActiveTab('dataset-audit')}
            className="btn-primary py-4 px-8 shadow-xl shadow-brand-500/10 flex items-center gap-2"
          >
            <Zap className="w-4 h-4" />
            Start New Audit
          </button>
        </div>
      </div>

      {/* KPI Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard 
          title="Total Audits" 
          value={totalAudits + 12} 
          icon={<History className="w-5 h-5 text-indigo-500" />} 
          trend="+4%"
          color="indigo"
        />
        <KPICard 
          title="Avg Risk Score" 
          value={(avgRisk * 100).toFixed(1)} 
          suffix="%"
          icon={<ShieldCheck className="w-5 h-5 text-emerald-500" />} 
          trend="-2.4%"
          color="emerald"
        />
        <KPICard 
          title="Flagged Issues" 
          value={totalFindings + 8} 
          icon={<AlertTriangle className="w-5 h-5 text-rose-500" />} 
          trend="+2"
          color="rose"
        />
        <KPICard 
          title="Live Throughput" 
          value="2.4k" 
          suffix="/hr"
          icon={<Activity className="w-5 h-5 text-amber-500" />} 
          trend="Stable"
          color="amber"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Feed */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between px-2">
            <h2 className="text-xl font-black text-slate-900 tracking-tight flex items-center gap-3">
               Recent Activity
               <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-500 text-[10px] font-black">LIVE</span>
            </h2>
            <button onClick={() => setActiveTab('audit-results')} className="text-xs font-bold text-brand-600 hover:text-brand-700 flex items-center gap-1 group">
               View All <ArrowUpRight className="w-3 h-3 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
            </button>
          </div>
          
          <div className="space-y-4">
            {recentReports.length > 0 ? (
              recentReports.map((report) => (
                <ActivityRow 
                  key={report.id} 
                  report={report} 
                  onClick={() => handleAuditClick(report)} 
                />
              ))
            ) : (
              <div className="bg-slate-50/50 rounded-[2.5rem] p-12 text-center border-2 border-dashed border-slate-200">
                <FileSearch className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                <h3 className="font-bold text-slate-900">No Audits in Vault</h3>
                <p className="text-sm text-slate-500 mt-1">Initiate an audit to see real-time findings here.</p>
              </div>
            )}
            
            {/* System Demo Entries */}
            <ActivityRowPlaceholder name="Credit_Risk_V2.csv" date="2 hours ago" type="Dataset" score="12%" />
            <ActivityRowPlaceholder name="Hiring_Model_Final" date="Yesterday" type="Model" score="45%" color="amber" />
          </div>
        </div>

        {/* Side Stats */}
        <div className="space-y-8">
           <Card title="Risk Distribution" subtitle="Across minority vs majority groups">
              <div className="h-[200px] mt-6">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={DEMO_CHART_DATA}>
                    <XAxis dataKey="name" hide />
                    <Tooltip 
                      cursor={{ fill: 'transparent' }}
                      contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 20px 50px rgba(0,0,0,0.1)', padding: '12px' }}
                    />
                    <Bar dataKey="risk" fill="#3B82F6" radius={[4,4,0,0]} barSize={20} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-4 flex justify-between items-center text-[10px] font-black text-slate-400 uppercase tracking-widest border-t border-slate-100 pt-4">
                <span>Minority Group B</span>
                <span>84% Divergence</span>
              </div>
           </Card>

           <div className="p-8 rounded-[2.5rem] bg-indigo-950 text-white relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-32 h-32 bg-brand-500 opacity-20 blur-3xl -mr-10 -mt-10 group-hover:opacity-40 transition-opacity" />
              <div className="relative z-10">
                <BrainCircuit className="w-10 h-10 text-brand-400 mb-6" />
                <h3 className="text-xl font-bold mb-2">Bias Mitigation AI</h3>
                <p className="text-white/60 text-xs leading-relaxed mb-6">
                  Based on your last audit, we recommend applying <span className="text-brand-400 font-bold underline decoration-brand-400/30 underline-offset-4 cursor-help">Post-processing Calibration</span> to reduce gender-based outcome disparities.
                </p>
                <button className="text-sm font-bold text-brand-400 flex items-center gap-2 hover:translate-x-1 transition-transform">
                  Implement Fix <ArrowRight className="w-4 h-4" />
                </button>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
};

// UI Components
const KPICard = ({ title, value, icon, trend, suffix = '', color = 'brand' }) => (
  <div className="bg-white p-6 rounded-[2.5rem] border border-slate-100 shadow-sm hover:shadow-xl hover:shadow-slate-200/40 transition-all group">
    <div className="flex items-center justify-between mb-4">
      <div className={cn(
        "w-12 h-12 rounded-2xl flex items-center justify-center transition-transform group-hover:scale-110",
        `bg-${color}-50`
      )}>
        {icon}
      </div>
      <div className={cn(
        "px-2 px-1 rounded-lg text-[10px] font-black tracking-tighter",
        trend.startsWith('+') ? "bg-rose-50 text-rose-600" : trend.startsWith('-') ? "bg-emerald-50 text-emerald-600" : "bg-slate-50 text-slate-500"
      )}>
        {trend}
      </div>
    </div>
    <div className="space-y-1">
      <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{title}</p>
      <div className="flex items-baseline gap-1">
        <h3 className="text-3xl font-black text-slate-900 tracking-tighter">{value}</h3>
        {suffix && <span className="text-sm font-bold text-slate-400 tracking-tight">{suffix}</span>}
      </div>
    </div>
  </div>
);

const ActivityRow = ({ report, onClick }) => (
  <div 
    onClick={onClick}
    className="group bg-white p-6 rounded-[2.5rem] border border-slate-100 hover:border-brand-300 hover:shadow-2xl hover:shadow-brand-500/5 transition-all cursor-pointer flex items-center justify-between"
  >
    <div className="flex items-center gap-5">
      <div className={cn(
        "w-14 h-14 rounded-2xl flex items-center justify-center transition-all group-hover:scale-105",
        report.performance ? "bg-brand-50 text-brand-600 shadow-inner" : "bg-emerald-50 text-emerald-600 shadow-inner"
      )}>
        {report.performance ? <ShieldCheck className="w-7 h-7" /> : <BarChart3 className="w-7 h-7" />}
      </div>
      <div>
        <h4 className="font-bold text-slate-900 text-base tracking-tight capitalize group-hover:text-brand-700 transition-colors">
            {report.performance ? 'Model Verification' : 'Dataset Fairness Audit'}
        </h4>
        <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-0.5 flex items-center gap-2">
           <span className="text-brand-500">{report.id}</span>
           <span className="w-1 h-1 rounded-full bg-slate-300" />
           {new Date(report.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </div>
    <div className="flex items-center gap-8">
       <div className="text-right">
         <p className="text-[10px] font-black text-slate-300 uppercase tracking-widest mb-1">Risk Score</p>
         <div className={cn(
            "text-lg font-black tracking-tighter px-3 py-1 rounded-xl inline-block",
            report.overall_risk_score > 0.75 ? "bg-rose-50 text-rose-600" : report.overall_risk_score > 0.4 ? "bg-amber-50 text-amber-600" : "bg-emerald-50 text-emerald-600"
         )}>
           {(report.overall_risk_score * 100).toFixed(0)}%
         </div>
       </div>
       <div className="w-10 h-10 rounded-full bg-slate-50 flex items-center justify-center group-hover:bg-brand-600 group-hover:text-white transition-all shadow-sm">
         <ArrowRight className="w-5 h-5" />
       </div>
    </div>
  </div>
);

const ActivityRowPlaceholder = ({ name, date, type, score, color = 'emerald' }) => (
  <div className="bg-white/40 p-6 rounded-[2.5rem] border border-slate-50 flex items-center justify-between transition-all opacity-60 hover:opacity-100 hover:bg-white hover:border-slate-100 group">
    <div className="flex items-center gap-5">
      <div className={cn(
        "w-14 h-14 rounded-2xl flex items-center justify-center bg-slate-50 text-slate-300"
      )}>
        {type === 'Model' ? <ShieldCheck className="w-7 h-7" /> : <BarChart3 className="w-7 h-7" />}
      </div>
      <div>
        <h4 className="font-bold text-slate-500 text-base tracking-tight group-hover:text-slate-900 transition-colors">{name}</h4>
        <p className="text-[10px] text-slate-300 font-bold uppercase tracking-widest mt-0.5">
          {type} Pipeline • {date}
        </p>
      </div>
    </div>
    <div className="flex items-center gap-8">
       <div className="text-right">
         <p className="text-[10px] font-black text-slate-200 uppercase tracking-widest mb-1">Risk</p>
         <p className={cn( "text-base font-black px-3 py-1 rounded-xl bg-slate-50 text-slate-400 group-hover:bg-opacity-100 group-hover:text-amber-500" )}>
           {score}
         </p>
       </div>
       <div className="w-10 h-10 rounded-full bg-slate-50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
         <ArrowRight className="w-5 h-5 text-slate-300" />
       </div>
    </div>
  </div>
);

const DEMO_CHART_DATA = [
  { name: 'A', risk: 40 },
  { name: 'B', risk: 84 },
  { name: 'C', risk: 20 },
  { name: 'D', risk: 55 },
  { name: 'E', risk: 30 },
  { name: 'F', risk: 65 },
];

export default Overview;
