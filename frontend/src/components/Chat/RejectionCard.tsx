import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { XCircle, AlertCircle } from "lucide-react";

interface RejectionData {
  reason: string;
}

interface RejectionCardProps {
  rejection: RejectionData;
}

const RejectionCard = ({ rejection }: RejectionCardProps) => {
  return (
    <Card className="w-full max-w-md border-2 border-red-300 bg-gradient-to-br from-red-50 to-rose-50 shadow-lg">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-red-800">
          <XCircle className="h-6 w-6 text-red-600" />
          Application Status
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-start gap-3 p-4 bg-white/70 rounded-lg border border-red-200">
          <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-red-800 mb-1">
              Unable to Process
            </p>
            <p className="text-sm text-gray-700">{rejection.reason}</p>
          </div>
        </div>

        <div className="pt-2 text-center">
          <p className="text-xs text-muted-foreground">
            Please contact support if you believe this is an error.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default RejectionCard;
