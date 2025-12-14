import { useState } from "react";
import {
  Upload,
  FileDown,
  Calculator,
  IndianRupee,
  Target,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import FileUploader from "@/components/Upload/FileUploader";
import { getSanctionLetterUrl } from "@/services/api";
import { useSession } from "@/context/SessionContext";

const LOAN_PURPOSES = [
  { value: "home_renovation", label: "Home Renovation" },
  { value: "medical", label: "Medical Emergency" },
  { value: "wedding", label: "Wedding" },
  { value: "travel", label: "Travel" },
  { value: "debt_consolidation", label: "Debt Consolidation" },
  { value: "education", label: "Education" },
  { value: "business", label: "Business" },
  { value: "other", label: "Other" },
];

interface LoanSidebarProps {
  onSalarySlipUploaded?: () => void;
}

const LoanSidebar = ({ onSalarySlipUploaded }: LoanSidebarProps) => {
  const {
    phone,
    tenure: contextTenure,
    setTenure: setContextTenure,
  } = useSession();
  const [loanAmount, setLoanAmount] = useState("500000");
  const [tenure, setTenure] = useState(contextTenure.toString());
  const [interestRate] = useState(14);
  const [loanPurpose, setLoanPurpose] = useState("");

  // Update context tenure when local tenure changes
  const handleTenureChange = (value: string) => {
    setTenure(value);
    const numValue = parseInt(value, 10);
    if (!isNaN(numValue) && numValue > 0) {
      setContextTenure(numValue);
    }
  };

  const calculateEMI = () => {
    const P = parseFloat(loanAmount) || 0;
    const R = interestRate / 12 / 100;
    const N = parseInt(tenure) || 1;

    if (P <= 0 || N <= 0) return 0;

    const emi = (P * R * Math.pow(1 + R, N)) / (Math.pow(1 + R, N) - 1);
    return Math.round(emi);
  };

  const emi = calculateEMI();
  const totalAmount = emi * parseInt(tenure || "1");
  const totalInterest = totalAmount - parseFloat(loanAmount || "0");

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const handleDownloadSanction = () => {
    if (phone) {
      window.open(getSanctionLetterUrl(phone), "_blank");
    }
  };

  return (
    <div className="flex h-full w-full flex-col overflow-y-auto border-l border-border bg-background p-4 lg:w-80">
      <Tabs defaultValue="calculator" className="flex-1">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="calculator">
            <Calculator className="mr-2 h-4 w-4" />
            EMI
          </TabsTrigger>
          <TabsTrigger value="upload">
            <Upload className="mr-2 h-4 w-4" />
            Upload
          </TabsTrigger>
        </TabsList>

        <TabsContent value="calculator" className="mt-4 space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">EMI Calculator</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="amount">Loan Amount (₹)</Label>
                <Input
                  id="amount"
                  type="number"
                  value={loanAmount}
                  onChange={(e) => setLoanAmount(e.target.value)}
                  placeholder="500000"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="tenure">Tenure (Months)</Label>
                <Input
                  id="tenure"
                  type="number"
                  value={tenure}
                  onChange={(e) => handleTenureChange(e.target.value)}
                  placeholder="12"
                  min={1}
                  max={60}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="purpose">Loan Purpose</Label>
                <Select value={loanPurpose} onValueChange={setLoanPurpose}>
                  <SelectTrigger>
                    <Target className="mr-2 h-4 w-4 text-muted-foreground" />
                    <SelectValue placeholder="Select purpose" />
                  </SelectTrigger>
                  <SelectContent>
                    {LOAN_PURPOSES.map((purpose) => (
                      <SelectItem key={purpose.value} value={purpose.value}>
                        {purpose.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Interest Rate</Label>
                <p className="text-2xl font-bold text-primary">
                  {interestRate}% p.a.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-primary/5">
            <CardContent className="space-y-3 pt-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">
                  Monthly EMI
                </span>
                <span className="flex items-center text-xl font-bold text-primary">
                  <IndianRupee className="h-4 w-4" />
                  {emi.toLocaleString("en-IN")}
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
                <span className="font-medium">
                  {formatCurrency(totalAmount)}
                </span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="upload" className="mt-4 space-y-4">
          <FileUploader onUploadSuccess={() => onSalarySlipUploaded?.()} />

          {phone && (
            <Button
              variant="outline"
              onClick={handleDownloadSanction}
              className="w-full"
            >
              <FileDown className="mr-2 h-4 w-4" />
              Download Sanction Letter
            </Button>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default LoanSidebar;
