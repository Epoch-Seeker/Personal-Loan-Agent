import { useState } from "react";
import {
  Calculator,
  FileText,
  CreditCard,
  HelpCircle,
  Gift,
  Target,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface QuickActionsProps {
  onAction: (message: string) => void;
  disabled?: boolean;
}

const LOAN_PURPOSES = [
  { value: "home_renovation", label: "Home Renovation", emoji: "🏠" },
  { value: "medical", label: "Medical Emergency", emoji: "🏥" },
  { value: "wedding", label: "Wedding", emoji: "💒" },
  { value: "travel", label: "Travel", emoji: "✈️" },
  { value: "debt_consolidation", label: "Debt Consolidation", emoji: "💳" },
  { value: "education", label: "Education", emoji: "📚" },
  { value: "business", label: "Business", emoji: "💼" },
  { value: "other", label: "Other", emoji: "📋" },
];

const actions = [
  {
    icon: Gift,
    label: "Check Offers",
    message: "Show me my pre-approved loan offers",
  },
  {
    icon: FileText,
    label: "Upload Documents",
    message: "I want to upload my salary slip",
  },
  { icon: HelpCircle, label: "Help", message: "What can you help me with?" },
];

const QuickActions = ({ onAction, disabled }: QuickActionsProps) => {
  const [selectedPurpose, setSelectedPurpose] = useState("");

  const handleApplyWithPurpose = () => {
    if (selectedPurpose) {
      const purpose = LOAN_PURPOSES.find((p) => p.value === selectedPurpose);
      onAction(
        `I want to apply for a personal loan for ${purpose?.label.toLowerCase()}`
      );
    } else {
      onAction("I want to apply for a personal loan");
    }
  };

  return (
    <div className="space-y-4 p-4">
      {/* Loan Purpose Selector */}
      <div className="rounded-lg border border-primary/20 bg-primary/5 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Target className="h-5 w-5 text-primary" />
          <span className="font-medium">What do you need the loan for?</span>
        </div>
        <div className="flex gap-2">
          <Select value={selectedPurpose} onValueChange={setSelectedPurpose}>
            <SelectTrigger className="flex-1">
              <SelectValue placeholder="Select loan purpose" />
            </SelectTrigger>
            <SelectContent>
              {LOAN_PURPOSES.map((purpose) => (
                <SelectItem key={purpose.value} value={purpose.value}>
                  <span className="flex items-center gap-2">
                    <span>{purpose.emoji}</span>
                    <span>{purpose.label}</span>
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            onClick={handleApplyWithPurpose}
            disabled={disabled}
            className="shrink-0"
          >
            <CreditCard className="mr-2 h-4 w-4" />
            Apply Now
          </Button>
        </div>
      </div>

      {/* Quick Action Buttons */}
      <div className="grid grid-cols-3 gap-3">
        {actions.map(({ icon: Icon, label, message }) => (
          <Button
            key={label}
            variant="outline"
            onClick={() => onAction(message)}
            disabled={disabled}
            className="flex h-auto flex-col gap-2 py-4"
          >
            <Icon className="h-5 w-5" />
            <span className="text-sm">{label}</span>
          </Button>
        ))}
      </div>

      {/* Promotional Banner */}
      <div className="rounded-lg bg-gradient-to-r from-green-500 to-emerald-600 p-4 text-white">
        <div className="flex items-center gap-2 mb-1">
          <Calculator className="h-5 w-5" />
          <span className="font-semibold">Special Offer!</span>
        </div>
        <p className="text-sm opacity-90">
          Get instant approval with zero paperwork. Pre-approved limits up to
          ₹10L at 14% p.a.
        </p>
      </div>
    </div>
  );
};

export default QuickActions;
