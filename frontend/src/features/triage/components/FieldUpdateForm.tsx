import {
  ArrowRight,
  LoaderCircle,
  MessageSquareText,
  TriangleAlert,
  X,
} from "lucide-react";
import type { RefObject } from "react";
type Props = {
  text: string;
  changeText: (value: string) => void;
  busy: boolean;
  limit: number;
  offline: boolean;
  analyze: () => Promise<void>;
  error: string;
  dismissError: () => void;
  textarea: RefObject<HTMLTextAreaElement | null>;
};
export function FieldUpdateForm({
  text,
  changeText,
  busy,
  limit,
  offline,
  analyze,
  error,
  dismissError,
  textarea,
}: Props) {
  return (
    <div className="card compose-card">
      <div className="card-heading">
        <div className="heading-icon">
          <MessageSquareText size={18} />
        </div>
        <div>
          <h2>Field update</h2>
        </div>
      </div>
      <label className="sr-only" htmlFor="field-update">
        Field update
      </label>
      <div className="textarea-wrap">
        <textarea
          id="field-update"
          ref={textarea}
          value={text}
          onChange={(e) => changeText(e.target.value)}
          disabled={busy}
          maxLength={limit}
          placeholder={
            "What happened at the outlet?\n\nInclude the outlet, product, and what the rep observed."
          }
          onKeyDown={(e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
              e.preventDefault();
              void analyze();
            }
          }}
        />
        <div className="textarea-footer">
          <span>⌘ / Ctrl + Enter to analyze</span>
          <span>
            {text.length.toLocaleString()} / {limit.toLocaleString()}
          </span>
        </div>
      </div>
      <div className="compose-actions">
        <button
          className="primary-button"
          disabled={busy || !text.trim() || offline || text.length > limit}
          onClick={() => void analyze()}
        >
          {busy ? (
            <>
              <LoaderCircle size={16} className="spin" />
              Analyzing…
            </>
          ) : (
            <>
              Analyze update
              <ArrowRight size={16} />
            </>
          )}
        </button>
      </div>
      {error && (
        <div className="error-message" role="alert">
          <TriangleAlert size={16} />
          <span>{error}</span>
          <button aria-label="Dismiss error" onClick={() => dismissError()}>
            <X size={15} />
          </button>
        </div>
      )}
    </div>
  );
}
