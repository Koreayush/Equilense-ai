import React, { useState } from 'react';
import { 
  Upload, 
  BrainCircuit, 
  Settings2, 
  Play, 
  AlertCircle, 
  X, 
  CheckCircle2,
  Database,
  ArrowRight,
  ShieldCheck,
  Cpu
} from 'lucide-react';
import { Card } from '../ui/Cards';
import { cn } from '../../lib/utils';
import { auditApi } from '../../api/client';
import useStore from '../../store/useStore';

const ModelAudit = () => {
  const [modelFile, setModelFile] = useState(null);
  const [evalFile, setEvalFile] = useState(null);
  const [config, setConfig] = useState({
    target_column: '',
    sensitive_columns: '',
    positive_label: '1',
    y_pred_column: ''
  });
  const { setIsLoading, setAuditResult, setError, isLoading, error, setActiveTab } = useStore();

  const handleFileChange = (e, type) => {
    const file = e.target.files[0];
    if (!file) return;

    if (type === 'model') {
      const ext = file.name.split('.').pop().toLowerCase();
      if (['pkl', 'joblib', 'onnx'].includes(ext)) {
        setModelFile(file);
      } else {
        alert('Supported model formats: .pkl, .joblib, .onnx');
      }
    } else {
      if (file.name.endsWith('.csv')) {
        setEvalFile(file);
      } else {
        alert('Evaluation data must be a CSV file.');
      }
    }
  };

  const handleRunAudit = async () => {
    if (!modelFile || !evalFile || !config.target_column || !config.sensitive_columns) {
      alert('Please fill in all required fields.');
      return;
    }

    setIsLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('model_file', modelFile);
    formData.append('eval_file', evalFile);
    formData.append('target_column', config.target_column);
    formData.append('sensitive_columns', config.sensitive_columns);
    formData.append('positive_label', config.positive_label);
    if (config.y_pred_column) {
      formData.append('y_pred_column', config.y_pred_column);
    }

    try {
      const result = await auditApi.runModelAudit(formData);
      setAuditResult(result); // Using same result store for now
      setActiveTab('audit-results');
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Model audit failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-slide-up">
      <div className="flex flex-col gap-1 text-center md:text-left">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">AI Model Fairness Audit</h1>
        <p className="text-slate-500 font-medium">Layer 2: Validate live model impact and performance across demographic groups.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Step 1: Uploads */}
        <div className="lg:col-span-2 space-y-6">
          <Card title="1. Model & Data" subtitle="Upload your artifacts for verification">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
               {/* Model Upload */}
               <div 
                className={cn(
                  "border-2 border-dashed rounded-2xl p-6 flex flex-col items-center justify-center transition-all cursor-pointer",
                  modelFile ? "border-emerald-200 bg-emerald-50/20" : "border-slate-200 hover:border-brand-400 hover:bg-brand-50/20"
                )}
                onClick={() => document.getElementById('model-upload').click()}
              >
                <input id="model-upload" type="file" className="hidden" onChange={(e) => handleFileChange(e, 'model')} />
                {modelFile ? (
                  <div className="text-center">
                    <div className="w-10 h-10 bg-emerald-100 text-emerald-600 rounded-xl flex items-center justify-center mx-auto mb-2">
                       <Cpu className="w-5 h-5" />
                    </div>
                    <p className="text-xs font-bold text-slate-900 truncate max-w-[120px]">{modelFile.name}</p>
                    <button onClick={(e) => {e.stopPropagation(); setModelFile(null);}} className="mt-2 text-[10px] font-bold text-rose-500">Remove</button>
                  </div>
                ) : (
                  <>
                    <BrainCircuit className="w-8 h-8 text-slate-300 mb-2" />
                    <p className="text-xs font-bold text-slate-900">Upload Model</p>
                    <p className="text-[10px] text-slate-400 mt-1">PKL, JOBLIB, ONNX</p>
                  </>
                )}
              </div>

               {/* Eval Data Upload */}
               <div 
                className={cn(
                  "border-2 border-dashed rounded-2xl p-6 flex flex-col items-center justify-center transition-all cursor-pointer",
                  evalFile ? "border-emerald-200 bg-emerald-50/20" : "border-slate-200 hover:border-brand-400 hover:bg-brand-50/20"
                )}
                onClick={() => document.getElementById('eval-upload').click()}
              >
                <input id="eval-upload" type="file" className="hidden" accept=".csv" onChange={(e) => handleFileChange(e, 'data')} />
                {evalFile ? (
                  <div className="text-center">
                    <div className="w-10 h-10 bg-emerald-100 text-emerald-600 rounded-xl flex items-center justify-center mx-auto mb-2">
                       <Database className="w-5 h-5" />
                    </div>
                    <p className="text-xs font-bold text-slate-900 truncate max-w-[120px]">{evalFile.name}</p>
                    <button onClick={(e) => {e.stopPropagation(); setEvalFile(null);}} className="mt-2 text-[10px] font-bold text-rose-500">Remove</button>
                  </div>
                ) : (
                  <>
                    <Database className="w-8 h-8 text-slate-300 mb-2" />
                    <p className="text-xs font-bold text-slate-900">Evaluation CSV</p>
                    <p className="text-[10px] text-slate-400 mt-1">Test dataset</p>
                  </>
                )}
              </div>
            </div>

            <div className="mt-6 p-4 rounded-xl bg-slate-900 text-white flex items-center gap-4">
              <div className="p-2 bg-white/10 rounded-lg">
                <ShieldCheck className="w-5 h-5 text-brand-400" />
              </div>
              <p className="text-xs font-medium text-slate-300">
                Model inspection performs <span className="text-brand-400 font-bold">In-Memory Inference</span> for zero-trust auditing.
              </p>
            </div>
          </Card>
        </div>

        {/* Step 2: Configuration */}
        <div className="lg:col-span-2 space-y-6">
          <Card title="2. Audit Logic" subtitle="Mapping expectations to model behavior" action={<Settings2 className="w-5 h-5 text-slate-300" />}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Ground Truth Column</label>
                <input type="text" placeholder="e.g. y_true" className="input-field py-2" value={config.target_column} onChange={e => setConfig({...config, target_column: e.target.value})} />
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Protected Attributes</label>
                <input type="text" placeholder="e.g. race, age" className="input-field py-2" value={config.sensitive_columns} onChange={e => setConfig({...config, sensitive_columns: e.target.value})} />
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Positive Class Value</label>
                <input type="text" placeholder="e.g. 1 or Approved" className="input-field py-2" value={config.positive_label} onChange={e => setConfig({...config, positive_label: e.target.value})} />
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Predict Prob Column (Opt)</label>
                <input type="text" placeholder="e.g. pred_prob" className="input-field py-2" value={config.y_pred_column} onChange={e => setConfig({...config, y_pred_column: e.target.value})} />
              </div>
            </div>

            {error && (
              <div className="mt-6 p-4 rounded-xl bg-rose-50 border border-rose-100 flex gap-3 animate-shake">
                <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-bold text-rose-900">Model Pipeline Error</p>
                  <p className="text-xs text-rose-700 mt-0.5 leading-relaxed">{error}</p>
                </div>
              </div>
            )}

            <div className="mt-8 flex justify-end">
              <button 
                onClick={handleRunAudit}
                disabled={isLoading || !modelFile || !evalFile}
                className="btn-primary flex items-center gap-3 px-8 py-4 w-full md:w-auto"
              >
                {isLoading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Auditing Model...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5" />
                    Run Model Verification
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

export default ModelAudit;
