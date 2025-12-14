import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Calculator, Percent, Calendar, IndianRupee } from "lucide-react";

interface LoanSummaryData {
  amount: number;
  interestRate: number;
  tenure: number;
  emi: number;
}

interface LoanSummaryCardProps {
  summary: LoanSummaryData;
}

const LoanSummaryCard = ({ summary }: LoanSummaryCardProps) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatEMI = (value: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(value);
  };

  const totalPayable = summary.emi * summary.tenure;
  const totalInterest = totalPayable - summary.amount;

  return (
    <Card className="w-full max-w-md border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50 shadow-lg">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-blue-800">
          <Calculator className="h-5 w-5" />
          Loan Summary
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center gap-2 p-3 bg-white/60 rounded-lg">
            <IndianRupee className="h-4 w-4 text-blue-600" />
            <div>
              <p className="text-xs text-muted-foreground">Loan Amount</p>
              <p className="font-semibold text-blue-800">
                {formatCurrency(summary.amount)}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 p-3 bg-white/60 rounded-lg">
            <Percent className="h-4 w-4 text-blue-600" />
            <div>
              <p className="text-xs text-muted-foreground">Interest Rate</p>
              <p className="font-semibold text-blue-800">
                {summary.interestRate}% p.a.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 p-3 bg-white/60 rounded-lg">
            <Calendar className="h-4 w-4 text-blue-600" />
            <div>
              <p className="text-xs text-muted-foreground">Tenure</p>
              <p className="font-semibold text-blue-800">
                {summary.tenure} months
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 p-3 bg-white/60 rounded-lg">
            <IndianRupee className="h-4 w-4 text-green-600" />
            <div>
              <p className="text-xs text-muted-foreground">Monthly EMI</p>
              <p className="font-semibold text-green-700">
                {formatEMI(summary.emi)}
              </p>
            </div>
          </div>
        </div>

        <div className="pt-3 border-t border-blue-200 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Total Interest</span>
            <span className="font-medium text-orange-600">
              {formatCurrency(totalInterest)}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Total Payable</span>
            <span className="font-semibold text-blue-800">
              {formatCurrency(totalPayable)}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default LoanSummaryCard;
