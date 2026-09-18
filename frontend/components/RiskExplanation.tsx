import type { RiskFactor } from "@/types/api";

const labels: Record<RiskFactor["kind"], string> = {
  entity: "Entity risk",
  sensitivity: "Sensitivity",
  combination: "Combination risk",
  repetition: "Repeated exposure",
};

type RiskExplanationProps = {
  factors: RiskFactor[];
};

export function RiskExplanation({ factors }: RiskExplanationProps) {
  return (
    <section className="rounded-2xl border border-slate-800/90 bg-[#0b1220] p-5 sm:p-6" aria-labelledby="explanation-title">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Explainability</p>
        <h2 id="explanation-title" className="mt-1 text-lg font-semibold text-white">Why this score</h2>
      </div>
      {factors.length === 0 ? (
        <p className="mt-5 rounded-xl border border-dashed border-slate-800 p-4 text-sm text-slate-500">No risk factors were added because no supported entities were detected.</p>
      ) : (
        <div className="mt-5 grid gap-2 sm:grid-cols-2">
          {factors.map((factor, index) => (
            <div key={`${factor.rule}-${factor.entity_type ?? "context"}-${index}`} className="rounded-xl border border-slate-800 bg-[#070d18] p-4">
              <div className="flex items-center justify-between gap-3">
                <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-teal-300/80">{labels[factor.kind]}</span>
                <span className="font-mono text-sm text-teal-200">+{factor.bonus.toFixed(2)}</span>
              </div>
              <p className="mt-2 text-sm leading-5 text-slate-300">{factor.message}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
