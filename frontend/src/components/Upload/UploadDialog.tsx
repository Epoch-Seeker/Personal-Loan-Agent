import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Upload, FileText, CheckCircle, Loader2 } from "lucide-react";
import { useDropzone } from "react-dropzone";
import { uploadSalarySlip } from "@/services/api";
import { useSession } from "@/context/SessionContext";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { Progress } from "@/components/ui/progress";

interface UploadDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUploadComplete?: () => void;
}

const UploadDialog = ({
  open,
  onOpenChange,
  onUploadComplete,
}: UploadDialogProps) => {
  const { getEffectiveSessionId, phone } = useSession();
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadComplete, setUploadComplete] = useState(false);

  const onDrop = (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setUploadComplete(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "image/*": [".png", ".jpg", ".jpeg"],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
    disabled: isUploading,
  });

  const simulateProgress = () => {
    return new Promise<void>((resolve) => {
      let progress = 0;
      const interval = setInterval(() => {
        progress += 10;
        setUploadProgress(progress);
        if (progress >= 100) {
          clearInterval(interval);
          resolve();
        }
      }, 150);
    });
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error("Please select a file first");
      return;
    }

    // Backend requires phone number for file association if available
    // If we have a phone in context, use it. Otherwise use generic session (which might not link to underwriting)
    // We prefer the explicit phone input if the user enters one.
    const effectiveId = phone || getEffectiveSessionId();

    if (!effectiveId) {
       toast.error("No identity found. Please enter phone number.");
       return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      // API call
      const uploadPromise = uploadSalarySlip(effectiveId, file);
      const progressPromise = simulateProgress();

      const [response] = await Promise.all([uploadPromise, progressPromise]);

      if (response.status === true) {
        setUploadComplete(true);
        toast.success("Salary slip uploaded successfully!");
        
        // Close dialog and notify parent
        onUploadComplete?.();
        
        // Short delay to allow animation/state update before closing
        setTimeout(() => {
          onOpenChange(false);
          // Reset state
          setFile(null);
          setUploadComplete(false);
          setUploadProgress(0);
        }, 500);
      } else {
        toast.error(response.msg || "Upload failed");
      }
    } catch (err) {
      let errorMsg = "Failed to upload file. Please try again.";
      if (typeof err === "object" && err !== null && "response" in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        if (axiosErr.response?.data?.detail) {
          errorMsg = axiosErr.response.data.detail;
        }
      }
      toast.error(errorMsg);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="text-2xl">Upload Salary Slip</DialogTitle>
          <DialogDescription>
            Upload your salary slip to continue with the loan application
            process. We'll analyze it to determine your eligibility.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* File Upload Area */}
          <div
            {...getRootProps()}
            className={cn(
              "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors",
              isDragActive
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50 hover:bg-muted/50",
              uploadComplete && "border-green-500 bg-green-50",
              isUploading && "pointer-events-none opacity-50"
            )}
          >
            <input {...getInputProps()} />

            {uploadComplete ? (
              <div className="flex flex-col items-center gap-3">
                <div className="rounded-full bg-green-100 p-3">
                  <CheckCircle className="h-8 w-8 text-green-600" />
                </div>
                <div className="text-center">
                  <p className="font-medium text-green-900">Upload Complete!</p>
                  <p className="text-sm text-green-600">
                    Processing your document...
                  </p>
                </div>
              </div>
            ) : file ? (
              <div className="flex w-full flex-col gap-3">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-blue-50 p-3">
                    <FileText className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="flex-1 text-left">
                    <p className="font-medium text-sm">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                {isUploading && (
                  <div className="space-y-2">
                    <Progress value={uploadProgress} className="h-2" />
                    <p className="text-center text-xs text-muted-foreground">
                      Uploading... {uploadProgress}%
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3 text-center">
                <div className="rounded-full bg-primary/10 p-3">
                  <Upload className="h-8 w-8 text-primary" />
                </div>
                <div>
                  <p className="font-medium">
                    {isDragActive
                      ? "Drop your file here"
                      : "Drag & drop or click to select"}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    PDF, PNG, JPG up to 10MB
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isUploading}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={handleUpload}
              disabled={!file || isUploading}
              className="flex-1"
            >
              {isUploading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default UploadDialog;
