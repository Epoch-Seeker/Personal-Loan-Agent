import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import {
  Upload,
  FileText,
  CheckCircle,
  AlertCircle,
  Loader2,
  Search,
  TrendingUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { uploadSalarySlip } from "@/services/api";
import { useSession } from "@/context/SessionContext";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { Progress } from "@/components/ui/progress";

interface UploadResult {
  success: boolean;
  salary?: number;
  maxEligibleAmount?: number;
  requestedAmount?: number;
  alternateAmount?: number;
  message?: string;
}

interface FileUploaderProps {
  onUploadSuccess?: (result?: UploadResult) => void;
}

const FileUploader = ({ onUploadSuccess }: FileUploaderProps) => {
  const { phone, setPhone } = useSession();
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<
    "idle" | "success" | "error" | "partial"
  >("idle");
  const [analysisResult, setAnalysisResult] = useState<UploadResult | null>(
    null
  );
  const [analysisProgress, setAnalysisProgress] = useState(0);

  const clearSelectedFile = () => {
    setFile(null);
    setUploadStatus("idle");
    setAnalysisResult(null);
    setAnalysisProgress(0);
  };

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const selectedFile = acceptedFiles[0];
      console.log("File selected:", selectedFile.name, selectedFile.size);
      setFile(selectedFile);
      setUploadStatus("idle");
      setAnalysisResult(null);
      setAnalysisProgress(0);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "image/*": [".png", ".jpg", ".jpeg"],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
    disabled: isUploading || isAnalyzing,
  });

  const simulateAnalysis = () => {
    return new Promise<void>((resolve) => {
      let progress = 0;
      const interval = setInterval(() => {
        progress += 10;
        setAnalysisProgress(progress);
        if (progress >= 100) {
          clearInterval(interval);
          resolve();
        }
      }, 200);
    });
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error("Please select a file first");
      return;
    }
    if (!phone || phone.length !== 10) {
      toast.error("Please enter a valid 10-digit phone number");
      return;
    }

    setIsUploading(true);
    setAnalysisProgress(0);

    try {
      const response = await uploadSalarySlip(phone, file);
      setIsUploading(false);

      // Show analyzing state for visual feedback
      setIsAnalyzing(true);
      toast.info("Processing salary slip...");
      await simulateAnalysis();
      setIsAnalyzing(false);

      // Backend returns { status: boolean, msg: string }
      // The actual salary analysis happens when user says "uploaded" in chat
      const result: UploadResult = {
        success: response.status === true,
        message: response.msg,
      };

      setAnalysisResult(result);

      if (result.success) {
        setUploadStatus("success");
        toast.success(response.msg || "Salary slip uploaded successfully!");
        // Trigger callback to notify chat - user should say "uploaded"
        onUploadSuccess?.(result);
        // Reset file after successful upload so user can upload again
        setTimeout(() => {
          clearSelectedFile();
        }, 2000);
      } else {
        setUploadStatus("error");
        toast.error(response.msg || "Unable to upload salary slip");
      }
    } catch (err) {
      setUploadStatus("error");
      setIsUploading(false);
      setIsAnalyzing(false);
      // Handle axios error
      let errorMsg = "Failed to upload file. Please try again.";
      if (typeof err === "object" && err !== null && "response" in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        if (axiosErr.response?.data?.detail) {
          errorMsg = axiosErr.response.data.detail;
        }
      }
      toast.error(errorMsg);
    }
  };

  const validatePhone = (value: string) => {
    const cleaned = value.replace(/\D/g, "").slice(0, 10);
    setPhone(cleaned);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="space-y-4 rounded-lg border border-border bg-card p-6">
      <div className="space-y-2">
        <Label htmlFor="phone">Phone Number</Label>
        <Input
          id="phone"
          type="tel"
          placeholder="Enter 10-digit phone number"
          value={phone}
          onChange={(e) => validatePhone(e.target.value)}
          maxLength={10}
        />
        {phone && phone.length !== 10 && (
          <p className="text-sm text-destructive">
            Please enter a valid 10-digit phone number
          </p>
        )}
      </div>

      <div
        {...getRootProps()}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors",
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-border hover:border-primary/50 hover:bg-muted/50",
          uploadStatus === "success" &&
            "border-green-500 bg-green-50 dark:bg-green-950/20",
          uploadStatus === "partial" &&
            "border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20",
          uploadStatus === "error" && "border-destructive bg-destructive/5"
        )}
      >
        <input {...getInputProps()} />
        {file ? (
          <div className="flex w-full flex-col gap-3">
            <div className="flex items-center gap-3">
              <FileText className="h-8 w-8 text-primary" />
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-foreground">
                  {file.name}
                </p>
                <p className="text-sm text-muted-foreground">
                  {file.size > 0
                    ? (file.size / 1024 / 1024).toFixed(2)
                    : "0.00"}{" "}
                  MB
                </p>
              </div>
              {uploadStatus === "success" && (
                <CheckCircle className="h-6 w-6 text-green-500" />
              )}
              {uploadStatus === "partial" && (
                <TrendingUp className="h-6 w-6 text-yellow-500" />
              )}
              {uploadStatus === "error" && (
                <AlertCircle className="h-6 w-6 text-destructive" />
              )}
            </div>

            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground">
                Click the area to pick another file.
              </p>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={isUploading || isAnalyzing}
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  clearSelectedFile();
                }}
              >
                Change file
              </Button>
            </div>
          </div>
        ) : (
          <>
            <Upload className="mb-4 h-12 w-12 text-muted-foreground" />
            <p className="text-center font-medium text-foreground">
              {isDragActive
                ? "Drop your file here"
                : "Drag & drop your salary slip"}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              or click to browse (PDF, PNG, JPG - Max 10MB)
            </p>
          </>
        )}
      </div>

      {/* Analysis Progress */}
      {isAnalyzing && (
        <div className="space-y-2 rounded-lg bg-blue-50 p-4 dark:bg-blue-950/20">
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 animate-pulse text-blue-500" />
            <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
              Analyzing income eligibility...
            </span>
          </div>
          <Progress value={analysisProgress} className="h-2" />
          <p className="text-xs text-muted-foreground">
            Verifying salary details and calculating maximum eligible amount
          </p>
        </div>
      )}

      {/* Analysis Result */}
      {analysisResult && !isAnalyzing && (
        <div
          className={cn(
            "rounded-lg p-4 space-y-2",
            analysisResult.success
              ? "bg-green-50 dark:bg-green-950/20"
              : "bg-red-50 dark:bg-red-950/20"
          )}
        >
          <div className="flex items-center gap-2">
            {analysisResult.success ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : (
              <AlertCircle className="h-5 w-5 text-red-500" />
            )}
            <span
              className={cn(
                "font-medium",
                analysisResult.success
                  ? "text-green-700 dark:text-green-300"
                  : "text-red-700 dark:text-red-300"
              )}
            >
              {analysisResult.message ||
                (analysisResult.success
                  ? "Upload successful!"
                  : "Upload failed")}
            </span>
          </div>
          {analysisResult.success && (
            <p className="text-sm text-muted-foreground">
              💡 Now go back to the chat and type <strong>"uploaded"</strong> to
              continue your loan application.
            </p>
          )}
        </div>
      )}

      <Button
        onClick={handleUpload}
        disabled={
          !file || !phone || phone.length !== 10 || isUploading || isAnalyzing
        }
        className="w-full"
      >
        {isUploading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Uploading...
          </>
        ) : isAnalyzing ? (
          <>
            <Search className="mr-2 h-4 w-4 animate-pulse" />
            Analyzing...
          </>
        ) : (
          "Upload Salary Slip"
        )}
      </Button>
    </div>
  );
};

export default FileUploader;
