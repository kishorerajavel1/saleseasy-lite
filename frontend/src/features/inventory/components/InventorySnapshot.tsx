import { ChevronDown, Package } from "lucide-react";
import { useInventorySnapshot } from "../hooks/useInventorySnapshot";

export function InventorySnapshot({
  open,
  onToggle,
}: {
  open: boolean;
  onToggle: () => void;
}) {
  const { records, error } = useInventorySnapshot();
  return (
    <section className="card inventory-card" id="verified-data">
      <button
        className="inventory-toggle"
        aria-expanded={open}
        onClick={onToggle}
      >
        <div>
          <Package size={17} />
          <h2>Verified inventory</h2>
          <span>{records ? `${records.length} records` : "Snapshot"}</span>
        </div>
        <ChevronDown size={16} className={open ? "expanded" : ""} />
      </button>
      {open && (
        <>
          <p className="inventory-description">
            Trusted system snapshot · physical stock may differ
          </p>
          {error ? (
            <p className="inventory-description" role="status">
              {error}
            </p>
          ) : !records ? (
            <p className="inventory-description">Loading inventory…</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>OUTLET</th>
                  <th>SKU</th>
                  <th className="stock-col">SYSTEM STOCK</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr key={record.id}>
                    <td>{record.outlet}</td>
                    <td>{record.sku}</td>
                    <td className="stock-col">
                      <span
                        className={`stock ${record.system_stock === 0 ? "zero" : ""}`}
                      >
                        {record.system_stock} units
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </section>
  );
}
