import { UploadCloud } from "lucide-react";
import { Button } from "@/components/ui/button";

const InlineUploadPrompt = ({ onOpenUpload }: { onOpenUpload: () => void }) => {
  return (
    <div className="lb-surface flex items-start gap-3 px-4 py-3">
      <div className="mt-0.5 rounded-lg bg-primary/10 p-2 text-primary">
        <UploadCloud className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-foreground">
          Salary slip required
        </p>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Upload your salary slip to continue the application.
        </p>
      </div>
      <Button variant="outline" size="sm" onClick={onOpenUpload}>
        Upload
      </Button>
    </div>
  );
};

export default InlineUploadPrompt;
