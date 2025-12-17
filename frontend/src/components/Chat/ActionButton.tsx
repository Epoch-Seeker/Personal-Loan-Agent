import { Button } from "@/components/ui/button";
import { Upload, ThumbsUp, ThumbsDown, List } from "lucide-react";

export type ActionType = "UPLOAD_SALARY_SLIP" | "YES" | "NO" | "SHOW_OPTIONS";

interface ActionButtonProps {
  action: ActionType;
  label: string;
  onClick: (action: ActionType) => void;
}

const iconMap: Record<ActionType, React.ElementType> = {
  UPLOAD_SALARY_SLIP: Upload,
  YES: ThumbsUp,
  NO: ThumbsDown,
  SHOW_OPTIONS: List,
};

const ActionButton = ({ action, label, onClick }: ActionButtonProps) => {
  const Icon = iconMap[action] || null;
  
  return (
    <Button
      variant="outline"
      size="sm"
      className="flex-1"
      onClick={() => onClick(action)}
    >
      {Icon && <Icon className="mr-2 h-4 w-4" />}
      {label}
    </Button>
  );
};

export default ActionButton;

// Helper to parse action markers from message content
// Format: [ACTION:TYPE|Label]
export const parseActionMarkers = (
  content: string
): { type: ActionType; label: string }[] => {
  const actions: { type: ActionType; label: string }[] = [];
  const regex = /\[ACTION:([A-Z_]+)\|([^\]]+)\]/g;
  let match;
  while ((match = regex.exec(content)) !== null) {
    actions.push({ type: match[1] as ActionType, label: match[2] });
  }
  return actions;
};

// Helper to strip action markers from content for display
export const stripActionMarkers = (content: string): string => {
  return content.replace(/\[ACTION:[A-Z_]+\|[^\]]+\]/g, "").trim();
};
