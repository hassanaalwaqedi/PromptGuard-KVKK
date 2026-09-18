const steps = [
  "Scanning prompt",
  "Detecting identifiers",
  "Evaluating privacy exposure",
  "Building sanitized version",
];

type LoadingAnalysisProps = {
  step: number;
};

export function LoadingAnalysis({ step }: LoadingAnalysisProps) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-teal-400/20 bg-teal-400/[0.06] p-5" role="status" aria-live="polite">
      <div className="absolute inset-x-0 top-0 h-px overflow-hidden bg-teal-300/10">
        <div className="animate-scan-line h-full w-1/4 bg-teal-300/80" />
      </div>
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-teal-300/20 bg-teal-300/10 text-teal-200">
          <span className="h-3 w-3 animate-pulse rounded-full bg-teal-300" aria-hidden="true" />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-100">Analysis in progress</p>
          <p className="mt-0.5 text-xs text-slate-400">The engine is evaluating this prompt in memory.</p>
        </div>
      </div>
      <div className="mt-5 grid gap-2 sm:grid-cols-4">
        {steps.map((label, index) => (
          <div key={label} className={`flex items-center gap-2 text-xs ${index <= step ? "text-teal-200" : "text-slate-600"}`}>
            <span className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[10px] ${index < step ? "border-teal-300/60 bg-teal-300/20" : index === step ? "border-teal-300 bg-teal-300/10" : "border-slate-700"}`}>
              {index < step ? "✓" : index + 1}
            </span>
            <span>{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
