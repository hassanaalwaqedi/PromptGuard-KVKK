import type { AnalyzeResponse, PolicyDecision } from "@/types/api";

import { RiskMeter } from "@/components/RiskMeter";

const decisionStyles: Record<PolicyDecision, { color: string; background: string; copy: string }> = {
  ALLOW: { color: "text-emerald-200", background: "border-emerald-300/25 bg-emerald-300/10", copy: "No supported sensitive data was detected." },
  WARN: { color: "text-amber-200", background: "border-amber-300/25 bg-amber-300/10", copy: "Review the prompt before sending it to a generative AI service." },
  MASK: { color: "text-orange-200", background: "border-orange-300/25 bg-orange-300/10", copy: "Use the sanitized prompt to reduce exposure." },
  BLOCK: { color: "text-rose-200", background: "border-rose-300/25 bg-rose-300/10", copy: "High privacy exposure detected. Use the sanitized prompt instead." },
};

type RiskSummaryProps = {
  result: AnalyzeResponse;
};

export function RiskSummary({ result }: RiskSummaryProps) {
  const decision = decisionStyles[result.risk.decision];

  return (
    <section className="grid gap-4 rounded-2xl border border-slate-800/90 bg-[#0b1220] p-5 shadow-2xl shadow-black/10 lg:grid-cols-[1fr_0.82fr] lg:p-6" aria-labelledby="analysis-summary-title">
      <div>
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-teal-300/80">Analysis result</p>
            <h2 id="analysis-summary-title" className="mt-1 text-lg font-semibold text-white">Privacy exposure overview</h2>
          </div>
          <span className="rounded-full border border-slate-700 px-2.5 py-1 text-xs text-slate-400">{result.entity_count} detected</span>
        </div>
        <div className="mt-6"><RiskMeter score={result.risk.score} level={result.risk.level} /></div>
      </div>
      <div className={`flex flex-col justify-between rounded-2xl border p-5 ${decision.background}`}>
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">Policy decision</p>
          <p className={`mt-3 text-4xl font-semibold tracking-tight ${decision.color}`}>{result.risk.decision}</p>
          <p className="mt-3 max-w-sm text-sm leading-6 text-slate-300">{decision.copy}</p>
        </div>
        <div className="mt-7 flex items-center justify-between border-t border-white/10 pt-4 text-xs text-slate-500">
          <span>Semantic provider</span>
          <span className="font-medium text-slate-300">{result.ner_provider}</span>
        </div>
      </div>
    </section>
  );
}
