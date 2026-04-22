import React from 'react';
import { 
  BarChart3, 
  ShieldCheck, 
  FileSearch, 
  BrainCircuit,
  Database,
  FileText,
  Settings,
  HelpCircle
} from 'lucide-react';
import { cn } from '../../lib/utils';
import useStore from '../../store/useStore';

const NavItem = ({ icon: Icon, label, active, onClick }) => (
  <button
    onClick={onClick}
    className={cn(
      "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group",
      active 
        ? "bg-brand-50 text-brand-700 shadow-sm" 
        : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
    )}
  >
    <Icon className={cn(
      "w-5 h-5 transition-transform duration-200 group-hover:scale-110",
      active ? "text-brand-600" : "text-slate-400"
    )} />
    <span className="font-medium text-sm">{label}</span>
    {active && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-brand-600 animate-pulse" />}
  </button>
);

const Sidebar = () => {
  const { activeTab, setActiveTab } = useStore();

  const primaryNav = [
    { id: 'dashboard', label: 'Overview', icon: BarChart3 },
    { id: 'dataset-audit', label: 'Dataset Audit', icon: Database },
    { id: 'model-audit', label: 'Model Audit', icon: BrainCircuit },
    { id: 'audit-history', label: 'Reports', icon: FileText },
  ];

  return (
    <aside className="w-72 h-screen flex flex-col bg-white border-r border-slate-200/60 sticky top-0 overflow-hidden">
      <div className="p-6">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 bg-brand-600 rounded-xl flex items-center justify-center shadow-lg shadow-brand-200 transition-transform hover:scale-105">
            <ShieldCheck className="text-white w-6 h-6" />
          </div>
          <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-600 tracking-tight">
            Equilense AI
          </span>
        </div>

        <nav className="space-y-1">
          <p className="px-4 text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Core Platform</p>
          {primaryNav.map((item) => (
            <NavItem
              key={item.id}
              {...item}
              active={activeTab === item.id}
              onClick={() => {
                if (item.id === 'audit-history') useStore.getState().resetResults();
                setActiveTab(item.id);
              }}
            />
          ))}
        </nav>
      </div>

      <div className="mt-auto p-6">
        <div className="p-6 rounded-[2rem] bg-slate-900 text-white relative overflow-hidden group shadow-2xl shadow-slate-900/20">
          <div className="absolute top-0 right-0 w-24 h-24 bg-brand-500/20 rounded-full blur-2xl -mr-12 -mt-12 transition-transform group-hover:scale-125 duration-700" />
          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1.5">Platform Status</p>
          <p className="text-sm font-bold mb-3">Enterprise Ready</p>
          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
            <div className="w-full h-full bg-emerald-500 rounded-full" />
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
