import {
  ArrowRight,
  Check,
  CheckCheck,
  ChevronDown,
  CircleHelp,
  Code2,
  Layers3,
  MessageSquareText,
  RotateCcw,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react";
import type { Result } from "../../../shared/api/contracts";
import { actions, categories } from "../data/presentation";
export function AnalysisPanel({
  result,
  clear,
}: {
  result: Result;
  clear: () => void;
}) {
  const { data } = result;
  const action = actions[data.recommended_next_action];
  return (
    <div className="card result-card">
      <div className="result-header">
        <div>
          <span className="eyebrow">ANALYSIS COMPLETE</span>
          <h2>{categories[data.issue_category]}</h2>
        </div>
        <button
          className="icon-button"
          aria-label="Clear analysis"
          title="Clear analysis"
          onClick={clear}
        >
          <RotateCcw size={16} />
        </button>
      </div>
      <div className="result-badges">
        <span className={`urgency ${data.urgency}`}>
          <span />
          {data.urgency} urgency
        </span>
        <span
          className={`review-badge ${data.needs_human_review ? "required" : ""}`}
        >
          {data.needs_human_review ? (
            <TriangleAlert size={12} />
          ) : (
            <Check size={12} />
          )}
          {data.needs_human_review
            ? "Human review required"
            : "No review required"}
        </span>
      </div>
      <div className="action-panel">
        <span className="section-label">RECOMMENDED NEXT STEP</span>
        <h3>
          <ArrowRight size={17} />
          {action.title}
        </h3>
        <p>{action.description}</p>
        <small>Recommendation only · no action has been executed</small>
      </div>
      <section className="result-section">
        <div className="result-section-heading">
          <h3>
            <Layers3 size={15} />
            Evidence trail
          </h3>
          <span>{data.evidence.length} sources</span>
        </div>
        {data.evidence
          .filter((e) => e.source === "verified_table")
          .map((item, i) => (
            <div className="evidence-item verified" key={`v${i}`}>
              <span className="evidence-label">
                <CheckCheck size={13} />
                VERIFIED SYSTEM RECORD
              </span>
              <p>{item.reference}</p>
            </div>
          ))}
        {data.evidence
          .filter((e) => e.source === "field_update")
          .map((item, i) => (
            <div className="evidence-item claim" key={`c${i}`}>
              <span className="evidence-label">
                <MessageSquareText size={12} />
                REPORTED · UNVERIFIED
              </span>
              <blockquote>{item.reference}</blockquote>
            </div>
          ))}
      </section>
      {data.review_reason && (
        <section className="result-section review-reason">
          <h3>
            <ShieldCheck size={15} />
            Why a person should review
          </h3>
          <p>{data.review_reason}</p>
        </section>
      )}
      {data.missing_information.length > 0 && (
        <section className="result-section">
          <h3>
            <CircleHelp size={15} />
            What to clarify
          </h3>
          <ul className="question-list">
            {data.missing_information.map((question, i) => (
              <li key={question}>
                <span>{String(i + 1).padStart(2, "0")}</span>
                {question}
              </li>
            ))}
          </ul>
        </section>
      )}
      <details className="json-details">
        <summary>
          <Code2 size={14} />
          Structured JSON
          <ChevronDown size={14} />
        </summary>
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </details>
    </div>
  );
}
