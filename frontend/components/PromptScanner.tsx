import { useState, type FormEvent } from "react";

import { DemoScenarios } from "@/components/DemoScenarios";

type PromptScannerProps = {
  prompt: string;
  isSubmitting: boolean;
  onPromptChange: (prompt: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onClear: () => void;
};

export function PromptScanner({ prompt, isSubmitting, onPromptChange, onSubmit, onClear }: PromptScannerProps) {
  const [demoMode, setDemoMode] = useState(false);

  return (
    <section className="rounded-2xl border border-slate-800/90 bg-[#0b1220] p-5 shadow-2xl shadow-black/10 sm:p-6" aria-labelledby="scanner-title">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-teal-300/80">Prompt scanner</p>
          <h2 id="scanner-title" className="mt-1 text-xl font-semibold tracking-tight text-white">Inspect before you send</h2>
          <p className="mt-1 max-w-xl text-sm leading-6 text-slate-400">Paste a prompt to inspect it before sending it to a generative AI service.</p>
        </div>
        <span className="text-xs tabular-nums text-slate-500">{prompt.length.toLocaleString()} / 10,000</span>
      </div>
      <form className="mt-5" onSubmit={onSubmit}>
        <label htmlFor="prompt" className="sr-only">Prompt to inspect</label>
        <textarea id="prompt" value={prompt} onChange={(event) => onPromptChange(event.target.value)} maxLength={10000} disabled={isSubmitting} className="min-h-52 w-full resize-y rounded-xl border border-slate-700 bg-[#070d18] p-4 text-sm leading-6 text-slate-100 shadow-inner shadow-black/20 placeholder:text-slate-600 disabled:cursor-wait disabled:opacity-70" placeholder="Enter or paste a prompt..." />
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button type="submit" disabled={isSubmitting} className="inline-flex items-center gap-2 rounded-xl bg-teal-300 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-teal-200 disabled:cursor-wait disabled:opacity-50">
            <span aria-hidden="true">{isSubmitting ? "◌" : "↗"}</span>
            {isSubmitting ? "Analyzing" : "Analyze Prompt"}
          </button>
          <button type="button" onClick={onClear} disabled={isSubmitting || !prompt} className="rounded-xl border border-slate-700 px-4 py-2.5 text-sm font-medium text-slate-300 transition hover:border-slate-500 hover:text-white disabled:cursor-not-allowed disabled:opacity-40">Clear</button>
          <span className="ml-auto text-xs text-slate-600">Processed transiently. No prompt storage.</span>
        </div>
      </form>
      <div className="mt-4 border-t border-slate-800 pt-4">
        <button type="button" onClick={() => setDemoMode((value) => !value)} className="text-xs font-medium text-slate-400 transition hover:text-teal-200" aria-expanded={demoMode}>
          {demoMode ? "Hide demo scenarios" : "Open demo mode"}
        </button>
      </div>
      {demoMode && <DemoScenarios onSelect={onPromptChange} />}
    </section>
  );
}
