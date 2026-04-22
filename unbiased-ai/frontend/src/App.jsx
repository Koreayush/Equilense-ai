import React from 'react';
import MainLayout from './components/layout/MainLayout';
import Overview from './components/dashboard/Overview';
import DatasetAudit from './components/audit/DatasetAudit';
import ModelAudit from './components/audit/ModelAudit';
import AuditResults from './components/audit/AuditResults';
import useStore from './store/useStore';

function App() {
  const { activeTab } = useStore();

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Overview />;
      case 'dataset-audit':
        return <DatasetAudit />;
      case 'model-audit':
        return <ModelAudit />;
      case 'audit-results':
        return <AuditResults />;
      case 'audit-history':
        return <AuditResults />;
      default:
        return <Overview />;
    }
  };

  return (
    <MainLayout>
      {renderContent()}
    </MainLayout>
  );
}

export default App;