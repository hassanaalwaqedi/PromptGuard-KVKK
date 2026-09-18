import type { DetectedEntity } from "@/types/api";

function maskEntity(entity: DetectedEntity): string {
  const value = entity.text;
  if (entity.type === "TC_ID") return `${value.slice(0, 3)}${"*".repeat(Math.max(0, value.length - 5))}${value.slice(-2)}`;
  if (entity.type === "CREDIT_CARD") {
    const digits = value.replace(/\D/g, "");
    return `${digits.slice(0, 4)} **** **** ${digits.slice(-4)}`;
  }
  if (entity.type === "IBAN") return `${value.slice(0, 4)} ${"*".repeat(Math.max(0, value.length - 8))} ${value.slice(-4)}`;
  if (entity.type === "PHONE") return value.replace(/(\d{3})\s*(\d{2})\s*(\d{2})$/, "*** ** $3");
  if (entity.type === "EMAIL") {
    const [local, domain] = value.split("@");
    return `${local?.slice(0, 1) ?? "*"}${"*".repeat(Math.max(2, (local?.length ?? 3) - 1))}@${domain ?? ""}`;
  }
  return value;
}

function actionLabel(action: DetectedEntity["sanitization_action"]): string {
  return action === "PSEUDONYMIZE" ? "PSEUDONYMIZED" : action === "MASK" ? "MASKED" : "KEPT";
}

type EntityListProps = {
  entities: DetectedEntity[];
};

export function EntityList({ entities }: EntityListProps) {
  return (
    <section className="rounded-2xl border border-slate-800/90 bg-[#0b1220] p-5 sm:p-6" aria-labelledby="detected-data-title">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Detected data</p>
          <h2 id="detected-data-title" className="mt-1 text-lg font-semibold text-white">Entity explorer</h2>
        </div>
        <span className="rounded-full border border-slate-700 px-2.5 py-1 text-xs text-slate-400">{entities.length} items</span>
      </div>
      {entities.length === 0 ? (
        <div className="mt-5 rounded-xl border border-dashed border-slate-800 p-5 text-sm text-slate-500">No supported entities were found in this prompt.</div>
      ) : (
        <div className="mt-5 divide-y divide-slate-800/80 overflow-hidden rounded-xl border border-slate-800">
          {entities.map((entity) => (
            <div key={`${entity.type}-${entity.start}-${entity.end}`} className="grid gap-3 bg-[#070d18] p-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-semibold tracking-[0.14em] text-teal-200">{entity.type}</span>
                  <span className="rounded-full border border-slate-700 px-2 py-0.5 text-[10px] text-slate-500">{entity.category}</span>
                  <span className={`rounded-full border px-2 py-0.5 text-[10px] ${entity.sanitization_action === "MASK" ? "border-rose-300/25 text-rose-200/80" : entity.sanitization_action === "PSEUDONYMIZE" ? "border-amber-300/25 text-amber-200/80" : "border-emerald-300/25 text-emerald-200/80"}`}>{actionLabel(entity.sanitization_action)}</span>
                </div>
                <p className="mt-2 break-all font-mono text-sm text-slate-200">{maskEntity(entity)}</p>
              </div>
              <div className="flex shrink-0 gap-4 text-xs text-slate-500 sm:text-right">
                <span>Confidence<br /><strong className="font-medium text-slate-300">{(entity.confidence * 100).toFixed(0)}%</strong></span>
                <span>Contribution<br /><strong className="font-medium text-teal-200">+{entity.risk_contribution.toFixed(2)}</strong></span>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
