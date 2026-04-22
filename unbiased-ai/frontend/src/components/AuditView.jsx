import UploadSection from "./UploadSection";
import ResultsSection from "./ResultsSection";

export default function AuditView({ controller }) {
  const { state } = controller;

  return (
    <div>
      {!state.result && <UploadSection controller={controller} />}
      {state.result && <ResultsSection controller={controller} />}
    </div>
  );
}