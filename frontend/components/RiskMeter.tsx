import type { RiskLevel } from "@/types/api";

const levelStyles: Record<RiskLevel, { accent: string; label: string }> = {
  LOW: { accent: "#34d399", label: "Low exposure" },
  MEDIUM: { accent: "#fbbf24", label: "Moderate exposure" },
  HIGH: { accent: "#fb923c", label: "High exposure" },
  CRITICAL: { accent: "#fb7185", label: "Critical exposure" },
};

type RiskMeterProps = {
  score: number;
  level: RiskLevel;
};

export function RiskMeter({ score, level }: RiskMeterProps) {
  const safeScore = Math.max(0, Math.min(100, score));
  const style = levelStyles[level];

  return (
    <div className="flex items-center gap-6 sm:gap-8">
      <div className="relative h-32 w-32 shrink-0 rounded-full p-[7px]" style={{ background: `conic-gradient(${style.accent} ${safeScore * 3.6}deg, #1b2738 ${safeScore * 3.6}deg)` }} aria-label={`Risk score ${safeScore} out of 100, ${level}`}>
        <div className="flex h-full w-full flex-col items-center justify-center rounded-full bg-[#0b1220]">
          <span className="text-3xl font-semibold tracking-tight text-white">{safeScore}</span>
          <span className="text-[10px] uppercase tracking-[0.2em] text-slate-500">/ 100</span>
        </div>
      </div>
      <div>
        <p className="text-xs font-medium uppercase tracking-[0.22em] text-slate-500">Risk level</p>
        <p className="mt-2 text-2xl font-semibold tracking-tight" style={{ color: style.accent }}>{level}</p>
        <p className="mt-1 text-sm text-slate-400">{style.label}</p>
      </div>
    </div>
  );
}
