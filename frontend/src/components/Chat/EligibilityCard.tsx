import {
  AlertTriangle,
  CheckCircle,
  IndianRupee,
  TrendingDown,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

interface EligibilityResult {
  isApproved: boolean;
  requestedAmount: number;
  approvedAmount: number;
  monthlySalary: number;
  maxEmi: number;
  reason?: string;
}

interface EligibilityCardProps {
  result: EligibilityResult;
  onAcceptAlternate?: () => void;
  onModifyRequest?: () => void;
}

const EligibilityCard = ({
  result,
  onAcceptAlternate,
  onModifyRequest,
}: EligibilityCardProps) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const emiPercentage = (result.maxEmi / result.monthlySalary) * 100;
  const isPartialApproval = !result.isApproved && result.approvedAmount > 0;

  return (
    <Card
      className={
        result.isApproved
          ? "border-green-200 bg-green-50/50 dark:border-green-800 dark:bg-green-950/20"
          : isPartialApproval
          ? "border-yellow-200 bg-yellow-50/50 dark:border-yellow-800 dark:bg-yellow-950/20"
          : "border-red-200 bg-red-50/50 dark:border-red-800 dark:bg-red-950/20"
      }
    >
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          {result.isApproved ? (
            <>
              <CheckCircle className="h-5 w-5 text-green-500" />
              <span>Eligibility Confirmed</span>
              <Badge className="ml-auto bg-green-500 text-white">
                Approved
              </Badge>
            </>
          ) : isPartialApproval ? (
            <>
              <TrendingDown className="h-5 w-5 text-yellow-500" />
              <span>Partial Eligibility</span>
              <Badge
                variant="secondary"
                className="ml-auto bg-yellow-100 text-yellow-700"
              >
                Counter Offer
              </Badge>
            </>
          ) : (
            <>
              <AlertTriangle className="h-5 w-5 text-red-500" />
              <span>Eligibility Check</span>
              <Badge variant="destructive" className="ml-auto">
                Not Eligible
              </Badge>
            </>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Salary Analysis */}
        <div className="rounded-lg bg-card p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">
              Monthly Income
            </span>
            <span className="font-semibold">
              {formatCurrency(result.monthlySalary)}
            </span>
          </div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">
              Max Eligible EMI (50%)
            </span>
            <span className="font-semibold text-primary">
              {formatCurrency(result.maxEmi)}
            </span>
          </div>
          <div className="mt-3">
            <div className="flex justify-between text-xs text-muted-foreground mb-1">
              <span>EMI to Income Ratio</span>
              <span>{emiPercentage.toFixed(0)}%</span>
            </div>
            <Progress value={Math.min(emiPercentage, 100)} className="h-2" />
          </div>
        </div>

        {/* Amount Comparison */}
        {isPartialApproval && (
          <div className="space-y-3">
            <div className="flex items-center justify-between rounded-lg bg-red-100/50 p-3 dark:bg-red-900/20">
              <div>
                <p className="text-xs text-muted-foreground">
                  Requested Amount
                </p>
                <p className="font-semibold line-through text-muted-foreground">
                  {formatCurrency(result.requestedAmount)}
                </p>
              </div>
              <AlertTriangle className="h-5 w-5 text-red-400" />
            </div>

            <div className="flex items-center justify-between rounded-lg bg-green-100/50 p-3 dark:bg-green-900/20">
              <div>
                <p className="text-xs text-muted-foreground">We Can Offer</p>
                <div className="flex items-center gap-1">
                  <IndianRupee className="h-5 w-5 text-green-600" />
                  <p className="text-xl font-bold text-green-600">
                    {(result.approvedAmount / 100000).toFixed(1)}L
                  </p>
                </div>
              </div>
              <CheckCircle className="h-5 w-5 text-green-500" />
            </div>
          </div>
        )}

        {result.reason && (
          <p className="text-sm text-muted-foreground italic">
            {result.reason}
          </p>
        )}

        {/* Action Buttons */}
        {isPartialApproval && (onAcceptAlternate || onModifyRequest) && (
          <div className="flex gap-2 pt-2">
            {onAcceptAlternate && (
              <Button
                onClick={onAcceptAlternate}
                className="flex-1 bg-green-600 hover:bg-green-700"
              >
                Accept {formatCurrency(result.approvedAmount)}
              </Button>
            )}
            {onModifyRequest && (
              <Button
                onClick={onModifyRequest}
                variant="outline"
                className="flex-1"
              >
                Modify Request
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default EligibilityCard;
