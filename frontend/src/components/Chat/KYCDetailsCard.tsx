import { CheckCircle, User, Phone, MapPin, Home } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface KYCDetails {
  name: string;
  phone: string;
  city: string;
  address: string;
  verified?: boolean;
}

interface KYCDetailsCardProps {
  details: KYCDetails;
}

const KYCDetailsCard = ({ details }: KYCDetailsCardProps) => {
  return (
    <Card className="border-green-200 bg-green-50/50 dark:border-green-800 dark:bg-green-950/20">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <CheckCircle className="h-5 w-5 text-green-500" />
          <span>KYC Verified</span>
          <Badge
            variant="secondary"
            className="ml-auto bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
          >
            Verified
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid gap-3">
          <div className="flex items-center gap-3">
            <User className="h-4 w-4 text-muted-foreground" />
            <div className="flex-1">
              <p className="text-xs text-muted-foreground">Full Name</p>
              <p className="font-medium">{details.name}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Phone className="h-4 w-4 text-muted-foreground" />
            <div className="flex-1">
              <p className="text-xs text-muted-foreground">Phone Number</p>
              <p className="font-medium">{details.phone}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <MapPin className="h-4 w-4 text-muted-foreground" />
            <div className="flex-1">
              <p className="text-xs text-muted-foreground">City</p>
              <p className="font-medium">{details.city}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Home className="h-4 w-4 text-muted-foreground" />
            <div className="flex-1">
              <p className="text-xs text-muted-foreground">Address</p>
              <p className="font-medium">{details.address}</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default KYCDetailsCard;
