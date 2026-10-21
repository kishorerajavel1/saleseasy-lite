import { ArrowUpRight } from "lucide-react";
import { samples } from "../data/scenarios";
type Props = { text: string; busy: boolean; onSelect: (value: string) => void };
export function ScenarioPicker({ text, busy, onSelect }: Props) {
  return (
    <details className="samples-section" open>
      <summary>Try an example</summary>
      <div className="sample-grid">
        {samples.map((sample) => (
          <button
            className={`sample-button ${text === sample.text ? "selected" : ""}`}
            key={sample.label}
            disabled={busy}
            onClick={() => {
              onSelect(sample.text);
            }}
          >
            {sample.name}
            <ArrowUpRight size={13} />
          </button>
        ))}
      </div>
    </details>
  );
}
