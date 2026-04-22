import React from 'react';
import Sidebar from './Sidebar';
import { Bell, Search, User } from 'lucide-react';

const TopNavbar = () => {
  return (
    <header className="h-16 flex items-center justify-between px-8 py-10 bg-white/50 backdrop-blur-md sticky top-0 z-10 border-b border-slate-200/40">
      <div className="flex-1 max-w-xl">
        {/* Search removed as requested */}
      </div>

      <div className="flex items-center gap-4">
        <button className="p-2.5 text-slate-500 hover:bg-slate-100 rounded-xl transition-colors relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-rose-500 border-2 border-white rounded-full" />
        </button>
        <div className="h-8 w-[1px] bg-slate-200 mx-2" />
        <div className="flex items-center gap-3 pl-2 cursor-pointer group">
          <div className="text-right">
            <p className="text-sm font-bold text-slate-900 leading-none mb-1 group-hover:text-brand-600 transition-colors">Ayush Kore</p>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Lead Strategist</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-slate-900 flex items-center justify-center border border-slate-800 transition-all shadow-lg shadow-slate-200">
            <User className="w-5 h-5 text-white" />
          </div>
        </div>
      </div>
    </header>
  );
};

const MainLayout = ({ children }) => {
  return (
    <div className="flex min-h-screen bg-[#F8FAFC]">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <TopNavbar />
        <main className="p-8 pb-12 animate-fade-in">
          {children}
        </main>
      </div>
    </div>
  );
};

export default MainLayout;
