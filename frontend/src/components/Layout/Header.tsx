import { Wallet, RefreshCw, HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HeaderProps {
  onReset?: () => void;
}

const Header = ({ onReset }: HeaderProps) => {
  return (
    <header className="flex items-center justify-between border-b border-border bg-card px-6 py-4">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
          <Wallet className="h-6 w-6 text-primary-foreground" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-foreground">LoanBuddy</h1>
            <div className="flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
              <div className="h-1.5 w-1.5 rounded-full bg-green-500" />
              Online
            </div>
          </div>
          <p className="text-sm text-muted-foreground">
            Your Personal Loan Assistant
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {onReset && (
          <Button variant="outline" size="sm" onClick={onReset}>
            <RefreshCw className="mr-2 h-4 w-4" />
            New Chat
          </Button>
        )}
        <Button variant="ghost" size="icon" title="Help">
          <HelpCircle className="h-5 w-5" />
        </Button>
      </div>
    </header>
  );
};

export default Header;
