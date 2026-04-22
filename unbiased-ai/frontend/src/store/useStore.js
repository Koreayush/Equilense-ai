import { create } from 'zustand';

const useStore = create((set) => ({
  // Navigation
  activeTab: 'dashboard',
  setActiveTab: (tab) => set({ activeTab: tab }),

  // Audit Data
  auditResult: null,
  recentReports: [],
  isLoading: false,
  error: null,

  setAuditResult: (result) => set((state) => {
    const newReport = {
        ...result,
        id: Math.random().toString(36).substr(2, 9).toUpperCase(),
        timestamp: new Date().toISOString()
    };
    return { 
        auditResult: result,
        recentReports: [newReport, ...state.recentReports].slice(0, 10) // Keep last 10
    };
  }),
  
  setIsLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error: error }),

  // Reset
  resetResults: () => set({ auditResult: null, error: null }),
}));

export default useStore;
