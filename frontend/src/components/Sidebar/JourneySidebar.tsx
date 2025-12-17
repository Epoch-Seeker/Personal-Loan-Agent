import { CheckCircle, Circle, FileDown, X, MessageCircle, FileText, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getSanctionLetterUrl } from "@/services/api";
import { useSession } from "@/context/SessionContext";
import type { JourneyStep } from "@/lib/loanJourney";

interface JourneySidebarProps {
  steps: JourneyStep[];
  canDownloadSanction?: boolean;
  salarySlipUploaded?: boolean;
  onExit?: () => void;
  onSupport?: () => void;
}

const JourneySidebar = ({
  steps,
  canDownloadSanction,
  salarySlipUploaded,
  onExit,
  onSupport,
}: JourneySidebarProps) => {
  const { phone } = useSession();

  const handleDownloadSanction = () => {
    if (phone) {
      window.open(getSanctionLetterUrl(phone), "_blank");
    }
  };

  return (
    <aside className="flex h-full w-full flex-col border-l border-border bg-slate-50 lg:w-80">
      {/* Header - Pinned */}
      <div className="border-b border-border bg-white p-6 flex-shrink-0">
        <h2 className="text-xl font-bold text-gray-900">Loan Journey</h2>
      </div>

      {/* Journey Timeline - Pinned */}
      <div className="space-y-1 p-6 flex-shrink-0">
        {steps.map((step, idx) => {
          const isDone = step.status === "done";
          const isCurrent = step.status === "current";
          const isPending = step.status === "pending";

          return (
            <div key={step.key} className="relative flex gap-4 items-start">
              {/* Connector Line */}
              {idx < steps.length - 1 && (
                <div className="absolute left-4 top-8 bottom-0 w-0.5 bg-gray-200" />
              )}

              {/* Icon */}
              <div
                className={`relative z-10 flex h-8 w-8 items-center justify-center rounded-full border-2 ${
                  isDone
                    ? "border-primary bg-primary"
                    : isCurrent
                    ? "border-primary bg-white ring-4 ring-blue-100"
                    : "border-gray-300 bg-white"
                }`}
              >
                {isDone ? (
                  <CheckCircle className="h-4 w-4 text-white" />
                ) : (
                  <Circle
                    className={`h-3 w-3 ${
                      isCurrent ? "text-primary" : "text-gray-300"
                    }`}
                  />
                )}
              </div>

              {/* Label */}
              <div className="flex-1 pt-1">
                <p
                  className={`text-sm font-medium ${
                    isCurrent
                      ? "font-bold text-primary"
                      : isDone
                      ? "text-gray-900"
                      : "text-gray-500"
                  }`}
                >
                  {step.title}
                </p>
                {step.caption && (
                  <p className="text-xs text-gray-400">{step.caption}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Documents Section - Scrollable */}
      <div className="flex-1 overflow-y-auto bg-slate-50 p-6">
        <h3 className="mb-4 text-xs font-semibold uppercase tracking-wider text-gray-500">
          DOCUMENTS
        </h3>
        
        <div className="space-y-3">
          {/* Salary Slip - Show only if actually uploaded */}
          {salarySlipUploaded && (
            <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-3 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="rounded bg-green-100 p-2">
                  <FileText className="h-4 w-4 text-green-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">Salary Slip</p>
                  <p className="text-xs text-gray-500">Uploaded</p>
                </div>
              </div>
              <span className="rounded bg-green-100 px-2 py-0.5 text-[10px] font-bold uppercase text-green-700">
                Verified
              </span>
            </div>
          )}

          {/* Sanction Letter */}
          {phone && canDownloadSanction && (
            <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-3 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="rounded bg-red-100 p-2">
                  <FileDown className="h-4 w-4 text-red-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">Sanction letter PDF</p>
                  <Button 
                    variant="link" 
                    className="h-auto p-0 text-xs text-blue-600 hover:no-underline"
                    onClick={handleDownloadSanction}
                  >
                    Download
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons - Pinned at bottom */}
      <div className="flex-shrink-0 border-t border-border bg-slate-50 p-6 space-y-4">
        {onExit && (
          <button
            onClick={onExit}
            className="flex w-full items-center gap-3 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white border border-gray-200 shadow-sm">
              <LogOut className="h-4 w-4 text-gray-600" />
            </div>
            Exit & save progress
          </button>
        )}
        {onSupport && (
          <button
            onClick={onSupport}
            className="flex w-full items-center gap-3 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white border border-gray-200 shadow-sm">
              <MessageCircle className="h-4 w-4 text-gray-600" />
            </div>
            Talk to support
          </button>
        )}
      </div>
    </aside>
  );
};

export default JourneySidebar;
