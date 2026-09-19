"use client";

import { FormEvent, useEffect, useState } from "react";

import { BackendStatus } from "@/components/BackendStatus";
import { LoadingAnalysis } from "@/components/LoadingAnalysis";
import { PromptComparison } from "@/components/PromptComparison";
import { PromptScanner } from "@/components/PromptScanner";
import { RiskExplanation } from "@/components/RiskExplanation";
import { RiskSummary } from "@/components/RiskSummary";
import { EntityList } from "@/components/EntityList";
import { analyzePrompt, checkHealth } from "@/lib/api";
import { type AnalyzeResponse } from "@/types/api";

const protections = ["Identity", "Contact", "Financial", "Network", "Personal data"];

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [analyzedPrompt, setAnalyzedPrompt] = useState("");
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void checkHealth()
      .then(() => setIsConnected(true))
      .catch(() => setIsConnected(false));
  }, []);

  useEffect(() => {
    if (!isSubmitting) return;
    const interval = window.setInterval(() => setLoadingStep((step) => Math.min(step + 1, 3)), 280);
    return () => window.clearInterval(interval);
  }, [isSubmitting]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setResult(null);
    if (!prompt.trim()) {
      setError("Enter a prompt before starting an analysis.");
      return;
    }

    setLoadingStep(0);
    setIsSubmitting(true);
    try {
      const response = await analyzePrompt(prompt);
      setResult(response);
      setAnalyzedPrompt(prompt);
      setIsConnected(true);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "The analysis could not be completed.");
      setIsConnected(false);
    } finally {
      setIsSubmitting(false);
    }
  }

  function clearPrompt() {
    setPrompt("");
    setAnalyzedPrompt("");
    setResult(null);
    setError(null);
  }

  function toggleTheme() {
    const nextTheme = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    document.documentElement.dataset.theme = nextTheme;
  }

  return (
    <main className="min-h-screen bg-[#050914] text-slate-100">
      <div className="mx-auto w-full max-w-[1320px] px-4 py-5 sm:px-6 sm:py-8 lg:px-8">
        <header className="flex items-start justify-between gap-6 border-b border-slate-800/80 pb-5">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-teal-300/30 bg-teal-300/10 text-sm font-bold tracking-tight text-teal-200">PG</div>
            <div>
              <p className="text-lg font-semibold tracking-tight text-white">PromptGuard-KVKK</p>
              <p className="mt-0.5 text-xs text-slate-500">Privacy Firewall for Generative AI</p>
            </div>
          </div>
          <div className="flex items-center gap-4 pt-2">
            <BackendStatus connected={isConnected} />
            <button
              type="button"
              onClick={toggleTheme}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-700 px-2.5 py-1.5 text-xs font-medium text-slate-300 transition hover:border-teal-300/50 hover:text-teal-200"
              aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
              aria-pressed={theme === "light"}
              title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            >
              <span aria-hidden="true" className="text-sm">{theme === "dark" ? "☼" : "☾"}</span>
              <span className="hidden sm:inline">{theme === "dark" ? "Light mode" : "Dark mode"}</span>
            </button>
          </div>
        </header>

        <section className="grid gap-6 py-9 lg:grid-cols-[1fr_auto] lg:items-end">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-teal-300/80">KVKK-aware privacy analysis</p>
            <h1 className="mt-3 max-w-3xl text-3xl font-semibold tracking-[-0.03em] text-white sm:text-5xl">Know what your prompt reveals before it leaves your workspace.</h1>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-400 sm:text-base">PromptGuard maps sensitive spans, explains exposure, and creates a safer prompt in one focused inspection flow.</p>
          </div>
          <div className="hidden max-w-xs text-right lg:block">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-600">Protected surface</p>
            <div className="mt-3 flex flex-wrap justify-end gap-2">
              {protections.map((protection) => <span key={protection} className="rounded-full border border-slate-800 px-2.5 py-1 text-[11px] text-slate-500">{protection}</span>)}
            </div>
          </div>
        </section>

        <PromptScanner prompt={prompt} isSubmitting={isSubmitting} onPromptChange={(value) => { setPrompt(value); setError(null); }} onSubmit={handleSubmit} onClear={clearPrompt} />

        {error && (
          <div className="mt-5 flex items-start gap-3 rounded-2xl border border-rose-300/20 bg-rose-300/[0.06] p-4 text-sm text-rose-100" role="alert">
            <span className="mt-0.5 text-rose-300" aria-hidden="true">!</span>
            <div><p className="font-medium">Analysis unavailable</p><p className="mt-1 text-rose-200/70">{error}</p></div>
          </div>
        )}

        {!result && !isSubmitting && !error && (
          <section className="mt-6 rounded-2xl border border-dashed border-slate-800 bg-slate-900/20 p-6" aria-label="Supported protections">
            <p className="text-sm font-medium text-slate-300">Ready when you are.</p>
            <p className="mt-1 text-sm text-slate-500">Paste a prompt above to inspect it before sending it to a generative AI service.</p>
            <div className="mt-4 flex flex-wrap gap-2 lg:hidden">{protections.map((protection) => <span key={protection} className="rounded-full border border-slate-800 px-2.5 py-1 text-[11px] text-slate-500">{protection}</span>)}</div>
          </section>
        )}

        {isSubmitting && <div className="mt-6"><LoadingAnalysis step={loadingStep} /></div>}

        {result && !isSubmitting && (
          <div className="mt-8 space-y-5">
            <RiskSummary result={result} />
            <PromptComparison result={result} prompt={analyzedPrompt} />
            <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
              <EntityList entities={result.entities} />
              <RiskExplanation factors={result.risk_factors} />
            </div>
            <p className="break-all text-right text-[10px] text-slate-700">Analysis ID: {result.analysis_id}</p>
          </div>
        )}

        <footer className="mt-12 flex flex-col justify-between gap-2 border-t border-slate-800/70 pt-5 text-[11px] text-slate-600 sm:flex-row">
          <span>Transient analysis. Raw prompts and detected values are not stored.</span>
          <span>Designed and developed by Yazan</span>
        </footer>
      </div>
    </main>
  );
}
