const scenarios = [
  {
    name: "Hospital",
    hint: "Synthetic patient contact",
    prompt: "Synthetic hospital note: Ahmet Y\u0131lmaz can be reached at +90 532 123 45 67. T.C. Kimlik: 10000000146. Follow-up appointment requested.",
  },
  {
    name: "Bank",
    hint: "Synthetic payment review",
    prompt: "Synthetic bank review for Ay\u015fe Demir: IBAN TR330006100519786457841326, card 4242-4242-4242-4242, phone +90 532 123 45 67.",
  },
  {
    name: "HR Department",
    hint: "Synthetic employee record",
    prompt: "Synthetic HR record: Mehmet Kaya, mehmet@example.com, phone +90 532 123 45 67. Please prepare a salary review summary.",
  },
  {
    name: "University",
    hint: "Synthetic student record",
    prompt: "Synthetic university record: Elif A\u011f\u00e7a, elif.student@example.com, student contact +90 532 123 45 67, T.C. Kimlik 10000000146.",
  },
];

type DemoScenariosProps = {
  onSelect: (prompt: string) => void;
};

export function DemoScenarios({ onSelect }: DemoScenariosProps) {
  return (
    <div className="mt-4 border-t border-slate-800 pt-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Demo scenarios</p>
          <p className="mt-1 text-xs text-slate-600">Synthetic prompts for your presentation. Select, then analyze.</p>
        </div>
        <span className="rounded-full border border-slate-800 px-2 py-1 text-[10px] uppercase tracking-wider text-slate-500">Demo mode</span>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {scenarios.map((scenario) => (
          <button key={scenario.name} type="button" onClick={() => onSelect(scenario.prompt)} className="group rounded-xl border border-slate-800 bg-slate-900/40 p-3 text-left transition hover:border-teal-300/40 hover:bg-teal-300/[0.06]">
            <span className="block text-sm font-medium text-slate-200 group-hover:text-teal-200">{scenario.name}</span>
            <span className="mt-1 block text-[11px] leading-4 text-slate-500">{scenario.hint}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
