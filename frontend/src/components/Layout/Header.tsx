import { Wallet, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

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
          <h1 className="text-xl font-bold text-foreground">LoanBuddy</h1>
          <p className="text-sm text-muted-foreground">Your Personal Loan Assistant</p>
        </div>
      </div>
      {onReset && (
        <Button variant="outline" size="sm" onClick={onReset}>
          <RefreshCw className="mr-2 h-4 w-4" />
          New Chat
        </Button>
      )}
    </header>
  );
};

export default Header;
