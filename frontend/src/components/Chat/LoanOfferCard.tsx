import {
  IndianRupee,
  Zap,
  FileCheck,
  Clock,
  Gift,
  TrendingUp,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface LoanOffer {
  preApprovedLimit: number;
  interestRate: number;
  maxTenure: number;
  emi?: number;
  processingFee?: string;
}

interface LoanOfferCardProps {
  offer: LoanOffer;
  onAccept?: () => void;
  onCustomize?: () => void;
}

const LoanOfferCard = ({
  offer,
  onAccept,
  onCustomize,
}: LoanOfferCardProps) => {
  const formatCurrency = (amount: number) => {
    if (amount >= 100000) {
      return `₹${(amount / 100000).toFixed(1)}L`;
    }
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const benefits = [
    {
      icon: Zap,
      label: "Instant Disbursal",
      description: "Get funds in 24 hours",
    },
    {
      icon: FileCheck,
      label: "Zero Paperwork",
      description: "Completely digital process",
    },
    {
      icon: Clock,
      label: "Quick Approval",
      description: "Decision in minutes",
    },
  ];

  return (
    <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-primary/10">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Gift className="h-5 w-5 text-primary" />
            <span>Your Personalized Offer</span>
          </CardTitle>
          <Badge className="bg-green-500 text-white hover:bg-green-600">
            Pre-Approved
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Main Offer Amount */}
        <div className="rounded-lg bg-primary/10 p-4 text-center">
          <p className="text-sm text-muted-foreground">Pre-Approved Limit</p>
          <div className="flex items-center justify-center gap-1">
            <IndianRupee className="h-8 w-8 text-primary" />
            <span className="text-4xl font-bold text-primary">
              {(offer.preApprovedLimit / 100000).toFixed(1)}L
            </span>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            Up to {formatCurrency(offer.preApprovedLimit)}
          </p>
        </div>

        {/* Offer Details Grid */}
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-lg bg-card p-3 text-center shadow-sm">
            <TrendingUp className="mx-auto h-5 w-5 text-blue-500" />
            <p className="mt-1 text-lg font-bold">{offer.interestRate}%</p>
            <p className="text-xs text-muted-foreground">Interest Rate p.a.</p>
          </div>
          <div className="rounded-lg bg-card p-3 text-center shadow-sm">
            <Clock className="mx-auto h-5 w-5 text-purple-500" />
            <p className="mt-1 text-lg font-bold">{offer.maxTenure}</p>
            <p className="text-xs text-muted-foreground">Max Months</p>
          </div>
        </div>

        {offer.emi && (
          <div className="rounded-lg border border-dashed border-primary/30 p-3 text-center">
            <p className="text-sm text-muted-foreground">
              Estimated Monthly EMI
            </p>
            <p className="text-2xl font-bold text-primary">
              ₹{offer.emi.toLocaleString("en-IN")}
            </p>
          </div>
        )}

        {/* Benefits */}
        <div className="space-y-2">
          <p className="text-sm font-medium">Exclusive Benefits</p>
          <div className="grid gap-2">
            {benefits.map(({ icon: Icon, label, description }) => (
              <div
                key={label}
                className="flex items-center gap-3 rounded-lg bg-card p-2 shadow-sm"
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                  <Icon className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-medium">{label}</p>
                  <p className="text-xs text-muted-foreground">{description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        {(onAccept || onCustomize) && (
          <div className="flex gap-2 pt-2">
            {onAccept && (
              <Button onClick={onAccept} className="flex-1">
                Accept Offer
              </Button>
            )}
            {onCustomize && (
              <Button
                onClick={onCustomize}
                variant="outline"
                className="flex-1"
              >
                Customize
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default LoanOfferCard;
