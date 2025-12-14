import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, FileDown, IndianRupee, User } from "lucide-react";

interface ApprovalData {
  name: string;
  amount: number;
  emi: string | number;
  pdfLink: string;
}

interface ApprovalCardProps {
  approval: ApprovalData;
}

const ApprovalCard = ({ approval }: ApprovalCardProps) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatEMI = (value: string | number) => {
    const numValue = typeof value === "string" ? parseFloat(value) : value;
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(numValue);
  };

  return (
    <Card className="w-full max-w-md border-2 border-green-300 bg-gradient-to-br from-green-50 to-emerald-50 shadow-lg">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-green-800">
          <CheckCircle2 className="h-6 w-6 text-green-600" />
          Loan Approved! 🎉
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-3">
          <div className="flex items-center gap-3 p-3 bg-white/70 rounded-lg">
            <User className="h-5 w-5 text-green-600" />
            <div>
              <p className="text-xs text-muted-foreground">Applicant Name</p>
              <p className="font-semibold text-gray-800">{approval.name}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 bg-white/70 rounded-lg">
            <IndianRupee className="h-5 w-5 text-green-600" />
            <div>
              <p className="text-xs text-muted-foreground">Approved Amount</p>
              <p className="text-xl font-bold text-green-700">
                {formatCurrency(approval.amount)}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 bg-white/70 rounded-lg">
            <IndianRupee className="h-5 w-5 text-blue-600" />
            <div>
              <p className="text-xs text-muted-foreground">Monthly EMI</p>
              <p className="text-lg font-semibold text-blue-700">
                {formatEMI(approval.emi)}
              </p>
            </div>
          </div>
        </div>

        <div className="pt-3 border-t border-green-200">
          <Button
            className="w-full bg-green-600 hover:bg-green-700 text-white"
            onClick={() => window.open(approval.pdfLink, "_blank")}
          >
            <FileDown className="mr-2 h-4 w-4" />
            Download Sanction Letter
          </Button>
        </div>

        <p className="text-xs text-center text-muted-foreground">
          Congratulations! Your loan has been approved.
        </p>
      </CardContent>
    </Card>
  );
};

export default ApprovalCard;
