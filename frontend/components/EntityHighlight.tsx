"use client";

import { useState } from "react";

import type { DetectedEntity } from "@/types/api";

type EntityHighlightProps = {
  prompt: string;
  entities: DetectedEntity[];
};

export function EntityHighlight({ prompt, entities }: EntityHighlightProps) {
  const [selected, setSelected] = useState<DetectedEntity | null>(null);
  const segments: Array<{ text: string; entity?: DetectedEntity }> = [];
  let cursor = 0;

  const ordered = [...entities]
    .filter((entity) => entity.start >= 0 && entity.end <= prompt.length && entity.start < entity.end)
    .sort((a, b) => a.start - b.start || b.end - a.end);

  for (const entity of ordered) {
    if (entity.start < cursor) continue;
    if (entity.start > cursor) segments.push({ text: prompt.slice(cursor, entity.start) });
    segments.push({ text: prompt.slice(entity.start, entity.end), entity });
    cursor = entity.end;
  }
  if (cursor < prompt.length) segments.push({ text: prompt.slice(cursor) });

  return (
    <div>
      <div className="rounded-xl border border-slate-800 bg-[#070d18] p-4 text-sm leading-7 text-slate-300" aria-label="Original prompt with detected entities">
        {segments.length === 0 ? <span>{prompt || "No prompt submitted yet."}</span> : segments.map((segment, index) => {
          const entity = segment.entity;
          if (!entity) return <span key={`text-${index}`}>{segment.text}</span>;
          return (
            <button key={`${entity.type}-${entity.start}-${index}`} type="button" onClick={() => setSelected(entity)} className="group relative mx-0.5 inline rounded-md border border-teal-300/35 bg-teal-300/10 px-1.5 py-0.5 text-left text-teal-100 transition hover:border-teal-200 hover:bg-teal-300/20" aria-label={`${entity.type}: ${entity.text}`}>
              {segment.text}
              <span className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 hidden w-56 -translate-x-1/2 rounded-lg border border-slate-700 bg-[#101a2b] p-3 text-left text-xs leading-5 text-slate-200 shadow-xl group-hover:block">
                <span className="block font-semibold text-teal-200">{entity.type}</span>
                <span className="block text-slate-400">{entity.category}</span>
                <span className="mt-1 block">Confidence: {(entity.confidence * 100).toFixed(0)}%</span>
                <span className="block">Contribution: +{entity.risk_contribution.toFixed(2)}</span>
                <span className="block text-slate-400">Source: {entity.source}</span>
              </span>
            </button>
          );
        })}
      </div>
      <p className="mt-2 text-[11px] text-slate-600">Highlighted spans come directly from backend offsets. Select an entity for details.</p>
      {selected && (
        <div className="mt-3 flex items-start justify-between gap-4 rounded-xl border border-teal-300/20 bg-teal-300/[0.06] p-3 text-xs" role="status">
          <div>
            <p className="font-semibold text-teal-200">{selected.type} <span className="font-normal text-slate-400">{selected.category}</span></p>
            <p className="mt-1 text-slate-300">Confidence {(selected.confidence * 100).toFixed(0)}% - +{selected.risk_contribution.toFixed(2)} risk contribution - {selected.source}</p>
          </div>
          <button type="button" onClick={() => setSelected(null)} className="text-slate-500 hover:text-white" aria-label="Close entity details">Close</button>
        </div>
      )}
    </div>
  );
}
