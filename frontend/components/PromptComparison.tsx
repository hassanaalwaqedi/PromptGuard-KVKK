"use client";

import { useState } from "react";

import type { AnalyzeResponse } from "@/types/api";
import { EntityHighlight } from "@/components/EntityHighlight";

type PromptComparisonProps = {
  result: AnalyzeResponse;
  prompt: string;
};

export function PromptComparison({ result, prompt }: PromptComparisonProps) {
  const [copied, setCopied] = useState(false);

  async function copySanitizedPrompt() {
    try {
      await navigator.clipboard.writeText(result.sanitized_prompt);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  }

  return (
    <section className="rounded-2xl border border-slate-800/90 bg-[#0b1220] p-5 sm:p-6" aria-labelledby="comparison-title">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Prompt transformation</p>
          <h2 id="comparison-title" className="mt-1 text-lg font-semibold text-white">Original vs Sanitized Prompt</h2>
        </div>
        <button type="button" onClick={copySanitizedPrompt} className="rounded-lg border border-teal-300/25 bg-teal-300/[0.06] px-3 py-2 text-xs font-medium text-teal-200 transition hover:border-teal-300/60 hover:bg-teal-300/10">{copied ? "Copied Sanitized Prompt" : "Copy Sanitized Prompt"}</button>
      </div>
      <div className="mt-5 grid gap-3 lg:grid-cols-[1fr_auto_1fr] lg:items-stretch">
        <div className="rounded-xl border border-slate-800 bg-[#070d18] p-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">Original prompt</p>
          <div className="mt-3"><EntityHighlight prompt={prompt} entities={result.entities} /></div>
        </div>
        <div className="flex items-center justify-center text-xl text-teal-300/70" aria-hidden="true">→</div>
        <div className="rounded-xl border border-teal-300/20 bg-teal-300/[0.04] p-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-teal-300/80">Sanitized Prompt</p>
          <p className="mt-3 whitespace-pre-wrap break-words text-sm leading-6 text-slate-200">{result.sanitized_prompt}</p>
        </div>
      </div>
    </section>
  );
}
