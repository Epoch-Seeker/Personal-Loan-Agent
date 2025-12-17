import { useState } from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface EMICalculatorDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const EMICalculatorDialog = ({
  open,
  onOpenChange,
}: EMICalculatorDialogProps) => {
  const [loanAmount, setLoanAmount] = useState(500000);
  const [tenure, setTenure] = useState(24);
  const interestRate = 14;

  const calculateEMI = () => {
    const P = loanAmount;
    const R = interestRate / 12 / 100;
    const N = tenure;

    if (P <= 0 || N <= 0) return 0;

    const emi = (P * R * Math.pow(1 + R, N)) / (Math.pow(1 + R, N) - 1);
    return Math.round(emi);
  };

  const emi = calculateEMI();
  const totalAmount = emi * tenure;
  const totalInterest = totalAmount - loanAmount;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const tenureOptions = [12, 24, 36, 48, 60];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>EMI Calculator</DialogTitle>
          <DialogDescription>
            Calculate your monthly payment and total interest
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Loan Amount */}
          <div className="space-y-2">
            <Label htmlFor="amount">Loan Amount</Label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
                ₹
              </span>
              <Input
                id="amount"
                type="number"
                value={loanAmount}
                onChange={(e) => setLoanAmount(Number(e.target.value))}
                className="pl-8"
                step={10000}
                min={10000}
                max={2000000}
              />
            </div>
            <input
              type="range"
              min={10000}
              max={2000000}
              step={10000}
              value={loanAmount}
              onChange={(e) => setLoanAmount(Number(e.target.value))}
              className="w-full"
              aria-label="Adjust loan amount"
            />
          </div>

          {/* Tenure Pills */}
          <div className="space-y-2">
            <Label>Tenure (Months)</Label>
            <div className="flex gap-2">
              {tenureOptions.map((months) => (
                <Button
                  key={months}
                  variant={tenure === months ? "default" : "outline"}
                  size="sm"
                  onClick={() => setTenure(months)}
                  className="flex-1"
                >
                  {months}m
                </Button>
              ))}
            </div>
          </div>

          {/* Interest Rate */}
          <div className="space-y-2">
            <Label>Interest Rate</Label>
            <p className="text-2xl font-bold text-primary">
              {interestRate}% p.a.
            </p>
          </div>

          {/* EMI Display */}
          <div className="rounded-lg bg-primary/5 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Monthly EMI</span>
              <span className="text-2xl font-bold text-primary">
                {formatCurrency(emi)}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Total Interest</span>
              <span className="font-medium">
                {formatCurrency(totalInterest)}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Total Amount</span>
              <span className="font-medium">{formatCurrency(totalAmount)}</span>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default EMICalculatorDialog;
