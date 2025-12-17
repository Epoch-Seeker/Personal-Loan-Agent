import type { JourneyStep } from "@/lib/loanJourney";

const statusClass: Record<JourneyStep["status"], string> = {
  done: "border-green-200 bg-green-50 text-green-800",
  failed: "border-destructive/30 bg-destructive/10 text-destructive",
  current: "border-primary/30 bg-primary/10 text-primary",
  pending: "border-border bg-muted/20 text-muted-foreground",
};

const LoanJourneyBar = ({ steps }: { steps: JourneyStep[] }) => {
  const total = steps.length;
  const done = steps.filter((s) => s.status === "done").length;

  return (
    <div className="lb-surface px-4 py-3">
      <div className="mb-3 flex items-center justify-between text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
        <span>Loan Journey</span>
        <span className="rounded-full border border-border bg-muted/30 px-2 py-1 text-[10px]">
          {done >= total ? "Completed" : `${done}/${total}`}
        </span>
      </div>
      <div className="grid gap-2 sm:grid-cols-5">
        {steps.map((step) => (
          <div
            key={step.key}
            className={`rounded-xl border px-3 py-2 text-xs font-medium ${
              statusClass[step.status]
            }`}
          >
            <div className="flex items-center gap-1.5">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-current" />
              {step.title}
            </div>
            <p className="mt-1 text-[11px] opacity-80">{step.caption}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LoanJourneyBar;
