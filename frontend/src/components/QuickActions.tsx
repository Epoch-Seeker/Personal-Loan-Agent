import { useState } from "react";
import { CreditCard, HelpCircle, Target } from "lucide-react";
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
      <div className="lb-surface p-4">
        <div className="mb-3 flex items-center gap-2">
          <Target className="h-5 w-5 text-primary" />
          <span className="font-medium">What do you need the loan for?</span>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row">
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
          <div className="flex gap-2">
            <Button onClick={handleApplyWithPurpose} disabled={disabled}>
              <CreditCard className="mr-2 h-4 w-4" />
              Start
            </Button>
            <Button
              variant="outline"
              onClick={() => onAction("What can you help me with?")}
              disabled={disabled}
            >
              <HelpCircle className="mr-2 h-4 w-4" />
              Help
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuickActions;
