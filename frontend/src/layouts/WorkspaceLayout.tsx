import { BarChart3 } from "lucide-react";
import type { ReactNode } from "react";

export function WorkspaceLayout({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <a className="brand" href="/" aria-label="SalesEasy home">
          <span className="brand-mark">
            <BarChart3 size={21} />
          </span>
          <span>
            SalesEasy <span className="lite-tag">Lite</span>
          </span>
        </a>
        <span className="header-caption">Field-sales triage</span>
      </header>
      {children}
    </div>
  );
}
