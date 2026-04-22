import React from 'react';
import { cn } from '../../lib/utils';

export const Card = ({ children, className, title, subtitle, action }) => (
  <div className={cn("glass-card p-6 flex flex-col", className)}>
    {(title || subtitle || action) && (
      <div className="flex items-center justify-between mb-6">
        <div>
          {title && <h3 className="text-lg font-bold text-slate-900 tracking-tight">{title}</h3>}
          {subtitle && <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p>}
        </div>
        {action && <div>{action}</div>}
      </div>
    )}
    {children}
  </div>
);

export const MetricCard = ({ title, value, icon: Icon, trend, color = "brand" }) => {
  const colors = {
    brand: "bg-brand-50 text-brand-700",
    emerald: "bg-emerald-50 text-emerald-700",
    rose: "bg-rose-50 text-rose-700",
    amber: "bg-amber-50 text-amber-700",
    slate: "bg-slate-50 text-slate-700",
  };

  return (
    <div className="glass-card p-5 group hover:shadow-md transition-all duration-300">
      <div className="flex items-start justify-between">
        <div className={cn("p-2.5 rounded-xl", colors[color])}>
          <Icon className="w-5 h-5" />
        </div>
        {trend && (
          <div className={cn(
            "flex items-center gap-1 text-[11px] font-bold px-2 py-1 rounded-full",
            trend > 0 ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"
          )}>
            {trend > 0 ? "+" : ""}{trend}%
          </div>
        )}
      </div>
      <div className="mt-4">
        <p className="text-sm font-medium text-slate-500">{title}</p>
        <p className="text-2xl font-bold text-slate-900 mt-1 tracking-tight">{value}</p>
      </div>
    </div>
  );
};
