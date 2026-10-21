import { useRef, useState } from "react";
import { WorkspaceLayout } from "../layouts/WorkspaceLayout";
import { InventorySnapshot } from "../features/inventory/components/InventorySnapshot";
import { AnalysisPanel } from "../features/triage/components/AnalysisPanel";
import { EmptyAnalysis } from "../features/triage/components/EmptyAnalysis";
import { FieldUpdateForm } from "../features/triage/components/FieldUpdateForm";
import { ScenarioPicker } from "../features/triage/components/ScenarioPicker";
import { useServiceHealth } from "../features/triage/hooks/useServiceHealth";
import { useTriageAnalysis } from "../features/triage/hooks/useTriageAnalysis";

export default function App() {
  const { health, offline } = useServiceHealth();
  const limit = health?.max_input_chars ?? 2000;
  const triage = useTriageAnalysis(limit);
  const textarea = useRef<HTMLTextAreaElement>(null);
  const [showInventory, setShowInventory] = useState(false);
  return (
    <WorkspaceLayout>
      <main id="analysis">
        <div className="page-heading">
          <h1>Analyze a field update</h1>
          <p>
            Review the issue, supporting evidence, and recommended next step.
          </p>
        </div>
        {offline && (
          <p className="service-error" role="status">
            The service is unavailable. Check the connection and refresh to
            retry.
          </p>
        )}
        <div className="analysis-layout">
          <section className="input-column" aria-label="Field report">
            <FieldUpdateForm
              {...triage}
              limit={limit}
              offline={offline}
              textarea={textarea}
            />
            <ScenarioPicker
              text={triage.text}
              busy={triage.busy}
              onSelect={(value) => {
                triage.changeText(value);
                textarea.current?.focus();
              }}
            />
            <InventorySnapshot
              open={showInventory}
              onToggle={() => setShowInventory((value) => !value)}
            />
          </section>
          <section
            className="result-column"
            aria-label="Analysis"
            aria-live="polite"
            aria-busy={triage.busy}
          >
            {triage.result ? (
              <AnalysisPanel
                result={triage.result}
                clear={triage.clearResult}
              />
            ) : (
              <EmptyAnalysis busy={triage.busy} />
            )}
          </section>
        </div>
      </main>
    </WorkspaceLayout>
  );
}
