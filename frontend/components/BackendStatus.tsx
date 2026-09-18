type BackendStatusProps = {
  connected: boolean | null;
};

export function BackendStatus({ connected }: BackendStatusProps) {
  const label = connected === true ? "Protected Engine Online" : connected === false ? "Engine Offline" : "Checking Engine";
  const tone = connected === true ? "text-emerald-300" : connected === false ? "text-rose-300" : "text-slate-400";
  const dot = connected === true ? "bg-emerald-400" : connected === false ? "bg-rose-400" : "bg-slate-500";

  return (
    <div className={`inline-flex items-center gap-2 text-xs font-medium ${tone}`} aria-live="polite">
      <span className={`h-2 w-2 rounded-full ${dot} ${connected === null ? "animate-pulse-soft" : ""}`} aria-hidden="true" />
      {label}
    </div>
  );
}
