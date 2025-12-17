import { Calculator, MessageCircle, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";

interface QuickActionChipsProps {
  onAction: (action: string) => void;
  disabled?: boolean;
}

const QuickActionChips = ({ onAction, disabled }: QuickActionChipsProps) => {
  const actions = [
    { id: "calculator", label: "Check EMI", icon: Calculator },
    { id: "options", label: "Show loan options", icon: FileText },
    { id: "support", label: "Talk to support", icon: MessageCircle },
  ];

  return (
    <div className="flex gap-2 overflow-x-auto pb-1">
      {actions.map((action) => (
        <Button
          key={action.id}
          variant="outline"
          size="sm"
          onClick={() => onAction(action.id)}
          disabled={disabled}
          className="whitespace-nowrap text-xs"
        >
          <action.icon className="mr-1.5 h-3 w-3" />
          {action.label}
        </Button>
      ))}
    </div>
  );
};

export default QuickActionChips;
