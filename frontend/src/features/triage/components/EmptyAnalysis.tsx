import { ClipboardCheck, LoaderCircle } from "lucide-react";

export function EmptyAnalysis({ busy }: { busy: boolean }) {
  return (
    <div className="card empty-result" role="status">
      {busy ? (
        <LoaderCircle size={28} className="spin" />
      ) : (
        <ClipboardCheck size={28} />
      )}
      <h2>{busy ? "Analyzing update…" : "Your analysis will appear here"}</h2>
      <p>
        {busy
          ? "Checking the report and supporting inventory."
          : "Enter a report or choose an example to get started."}
      </p>
    </div>
  );
}
