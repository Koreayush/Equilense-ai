import React, { useState } from 'react';
import { 
  Upload, 
  FileText, 
  Settings2, 
  Play, 
  AlertCircle, 
  X, 
  CheckCircle2,
  ChevronRight,
  Database,
  ArrowRight
} from 'lucide-react';
import { Card } from '../ui/Cards';
import { cn } from '../../lib/utils';
import { auditApi } from '../../api/client';
import useStore from '../../store/useStore';

const DatasetAudit = () => {
  const [file, setFile] = useState(null);
  const [config, setConfig] = useState({
    target_column: '',
    sensitive_columns: '',
    y_pred_column: '',
    positive_label: '1'
  });
  const { setIsLoading, setAuditResult, setError, isLoading, error, setActiveTab } = useStore();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.endsWith('.csv')) {
      setFile(selectedFile);
    } else {
      alert('Please upload a valid CSV file.');
    }
  };

  const handleRunAudit = async () => {
    if (!file || !config.target_column || !config.sensitive_columns) {
      alert('Please fill in all required fields.');
      return;
    }

    setIsLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('target_column', config.target_column);
    formData.append('sensitive_columns', config.sensitive_columns);
    formData.append('positive_label', config.positive_label);
    if (config.y_pred_column) {
      formData.append('y_pred_column', config.y_pred_column);
    }

    try {
      const result = await auditApi.runDatasetAudit(formData);
      setAuditResult(result);
      setActiveTab('audit-results'); // Redirect to results or show them here
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Audit failed. Please check your inputs.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-slide-up">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Dataset Fairness Audit</h1>
        <p className="text-slate-500 font-medium">Layer 1: Analyze training data for bias before model development.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Section */}
        <div className="lg:col-span-1 space-y-6">
          <Card title="1. Upload Data" subtitle="Select your CSV dataset">
            <div 
              className={cn(
                "border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center transition-all cursor-pointer group",
                file ? "border-emerald-200 bg-emerald-50/30" : "border-slate-200 hover:border-brand-400 hover:bg-brand-50/30"
              )}
              onClick={() => document.getElementById('file-upload').click()}
            >
              <input 
                id="file-upload" 
                type="file" 
                className="hidden" 
                accept=".csv"
                onChange={handleFileChange}
              />
              {file ? (
                <div className="flex flex-col items-center animate-fade-in">
                  <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-xl flex items-center justify-center mb-3">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>
                  <p className="text-sm font-bold text-slate-900 max-w-[150px] truncate text-center">{file.name}</p>
                  <p className="text-[10px] text-slate-500 font-medium mt-1">{(file.size / 1024).toFixed(1)} KB</p>
                  <button 
                    onClick={(e) => { e.stopPropagation(); setFile(null); }}
                    className="mt-4 text-xs font-bold text-slate-400 hover:text-rose-500 flex items-center gap-1 transition-colors"
                  >
                    <X className="w-3 h-3" /> Remove
                  </button>
                </div>
              ) : (
                <>
                  <div className="w-12 h-12 bg-slate-100 text-slate-400 rounded-xl flex items-center justify-center mb-4 group-hover:bg-brand-100 group-hover:text-brand-600 transition-all">
                    <Upload className="w-6 h-6" />
                  </div>
                  <p className="text-sm font-bold text-slate-900">Drop CSV file here</p>
                  <p className="text-xs text-slate-500 mt-1">or click to browse</p>
                </>
              )}
            </div>
          </Card>

          <div className="glass-card p-6 bg-brand-900 text-white relative overflow-hidden">
             <div className="absolute top-0 right-0 w-32 h-32 bg-brand-500/20 rounded-full blur-3xl -mr-16 -mt-16" />
             <div className="relative z-10">
                <div className="flex items-center gap-2 text-brand-300 mb-2">
                  <Database className="w-4 h-4" />
                  <span className="text-[10px] font-bold uppercase tracking-widest">Audit Guide</span>
                </div>
                <h4 className="font-bold text-lg leading-tight mb-4">How it works?</h4>
                <ul className="space-y-3">
                  {[
                    'Identify protected groups',
                    'Check for representation gaps',
                    'Analyze outcome disparities',
                    'Generate mitigation report'
                  ].map((text, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-brand-100">
                      <ChevronRight className="w-3.5 h-3.5 mt-0.5 text-brand-400" />
                      {text}
                    </li>
                  ))}
                </ul>
             </div>
          </div>
        </div>

        {/* Config Section */}
        <div className="lg:col-span-2 space-y-6">
          <Card 
            title="2. Configure Parameters" 
            subtitle="Define columns and sensitive attributes"
            action={<Settings2 className="w-5 h-5 text-slate-300" />}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Target Column *</label>
                <input 
                  type="text" 
                  placeholder="e.g. approved_loan" 
                  className="input-field"
                  value={config.target_column}
                  onChange={(e) => setConfig({...config, target_column: e.target.value})}
                />
                <p className="text-[10px] text-slate-400">The historical outcome column in your data.</p>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Sensitive Columns *</label>
                <input 
                  type="text" 
                  placeholder="e.g. gender, race, age_group" 
                  className="input-field"
                  value={config.sensitive_columns}
                  onChange={(e) => setConfig({...config, sensitive_columns: e.target.value})}
                />
                <p className="text-[10px] text-slate-400">Comma-separated list of columns to audit.</p>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Prediction Column (Optional)</label>
                <input 
                  type="text" 
                  placeholder="e.g. model_score" 
                  className="input-field"
                  value={config.y_pred_column}
                  onChange={(e) => setConfig({...config, y_pred_column: e.target.value})}
                />
                <p className="text-[10px] text-slate-400">Include to run model-agnostic fairness checks.</p>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Positive Label *</label>
                <input 
                  type="text" 
                  placeholder="e.g. 1" 
                  className="input-field"
                  value={config.positive_label}
                  onChange={(e) => setConfig({...config, positive_label: e.target.value})}
                />
                <p className="text-[10px] text-slate-400">The value representing a 'privileged' or 'pass' outcome.</p>
              </div>
            </div>

            <div className="mt-8 p-4 rounded-xl bg-amber-50 border border-amber-100 flex gap-3">
              <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-bold text-amber-900">Audit Processing</p>
                <p className="text-xs text-amber-700 mt-0.5 leading-relaxed">
                  Running a full audit may take several seconds depending on dataset size. Your data is processed securely and is not stored after session end.
                </p>
              </div>
            </div>

            {error && (
              <div className="mt-8 p-4 rounded-xl bg-rose-50 border border-rose-100 flex gap-3 animate-shake">
                <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-bold text-rose-900">Audit Pipeline Error</p>
                  <p className="text-xs text-rose-700 mt-0.5 leading-relaxed">{error}</p>
                </div>
              </div>
            )}

            <div className="mt-10 flex justify-end">
              <button 
                onClick={handleRunAudit}
                disabled={isLoading || !file}
                className="btn-primary flex items-center gap-3 px-8 py-4 text-lg"
              >
                {isLoading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Running Audit...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5" />
                    Initiate Audit Pipeline
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </>
                )}
              </button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default DatasetAudit;
