import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils";
import { Message } from "@/hooks/useChat";
import { User, Bot, FileDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import KYCDetailsCard from "./KYCDetailsCard";
import LoanOfferCard from "./LoanOfferCard";
import EligibilityCard from "./EligibilityCard";
import LoanSummaryCard from "./LoanSummaryCard";
import ApprovalCard from "./ApprovalCard";
import RejectionCard from "./RejectionCard";

interface MessageBubbleProps {
  message: Message;
}

// Helper to extract PDF download links from markdown
const extractPdfLinks = (content: string): { url: string; text: string }[] => {
  const links: { url: string; text: string }[] = [];
  // Match markdown links to PDF files
  const markdownLinkRegex = /\[([^\]]+)\]\((http[^)]+\.pdf)\)/g;
  let match;
  while ((match = markdownLinkRegex.exec(content)) !== null) {
    links.push({ text: match[1], url: match[2] });
  }
  return links;
};

// Helper function to detect and parse structured data from message content
const parseStructuredContent = (content: string) => {
  // Try to detect KYC verification data
  const kycMatch = content.match(
    /\[KYC_VERIFIED\]([\s\S]*?)\[\/KYC_VERIFIED\]/
  );
  if (kycMatch) {
    try {
      const data = JSON.parse(kycMatch[1]);
      return {
        type: "kyc" as const,
        data,
        remainingContent: content.replace(kycMatch[0], "").trim(),
      };
    } catch {
      // Not valid JSON, continue
    }
  }

  // Try to detect loan offer data
  const offerMatch = content.match(/\[LOAN_OFFER\]([\s\S]*?)\[\/LOAN_OFFER\]/);
  if (offerMatch) {
    try {
      const data = JSON.parse(offerMatch[1]);
      return {
        type: "offer" as const,
        data,
        remainingContent: content.replace(offerMatch[0], "").trim(),
      };
    } catch {
      // Not valid JSON, continue
    }
  }

  // Try to detect eligibility result
  const eligibilityMatch = content.match(
    /\[ELIGIBILITY\]([\s\S]*?)\[\/ELIGIBILITY\]/
  );
  if (eligibilityMatch) {
    try {
      const data = JSON.parse(eligibilityMatch[1]);
      return {
        type: "eligibility" as const,
        data,
        remainingContent: content.replace(eligibilityMatch[0], "").trim(),
      };
    } catch {
      // Not valid JSON, continue
    }
  }

  // Try to detect loan summary data
  const summaryMatch = content.match(
    /\[LOAN_SUMMARY\]([\s\S]*?)\[\/LOAN_SUMMARY\]/
  );
  if (summaryMatch) {
    try {
      const data = JSON.parse(summaryMatch[1]);
      return {
        type: "summary" as const,
        data,
        remainingContent: content.replace(summaryMatch[0], "").trim(),
      };
    } catch {
      // Not valid JSON, continue
    }
  }

  // Try to detect approval data
  const approvalMatch = content.match(/\[APPROVAL\]([\s\S]*?)\[\/APPROVAL\]/);
  if (approvalMatch) {
    try {
      const data = JSON.parse(approvalMatch[1]);
      return {
        type: "approval" as const,
        data,
        remainingContent: content.replace(approvalMatch[0], "").trim(),
      };
    } catch {
      // Not valid JSON, continue
    }
  }

  // Try to detect rejection data
  const rejectionMatch = content.match(
    /\[REJECTION\]([\s\S]*?)\[\/REJECTION\]/
  );
  if (rejectionMatch) {
    try {
      const data = JSON.parse(rejectionMatch[1]);
      return {
        type: "rejection" as const,
        data,
        remainingContent: content.replace(rejectionMatch[0], "").trim(),
      };
    } catch {
      // Not valid JSON, continue
    }
  }

  return null;
};

const MessageBubble = ({ message }: MessageBubbleProps) => {
  const isUser = message.role === "user";

  // Parse for structured content in assistant messages
  const structuredContent = !isUser
    ? parseStructuredContent(message.content)
    : null;

  // Get the text content to display (without the structured tags)
  const displayContent = structuredContent?.remainingContent || message.content;

  // Extract PDF links for download buttons, but only from the display content (not from structured tags)
  // Also skip if structured content is an approval (which has its own download button)
  const pdfLinks =
    !isUser && structuredContent?.type !== "approval"
      ? extractPdfLinks(displayContent)
      : [];

  const renderStructuredCard = () => {
    if (!structuredContent) return null;

    switch (structuredContent.type) {
      case "kyc":
        return <KYCDetailsCard details={structuredContent.data} />;
      case "offer":
        return <LoanOfferCard offer={structuredContent.data} />;
      case "eligibility":
        return <EligibilityCard result={structuredContent.data} />;
      case "summary":
        return <LoanSummaryCard summary={structuredContent.data} />;
      case "approval":
        return <ApprovalCard approval={structuredContent.data} />;
      case "rejection":
        return <RejectionCard rejection={structuredContent.data} />;
      default:
        return null;
    }
  };

  return (
    <div
      className={cn("flex items-start gap-3 p-4", isUser && "flex-row-reverse")}
    >
      <div
        className={cn(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-secondary" : "bg-primary"
        )}
      >
        {isUser ? (
          <User className="h-5 w-5 text-secondary-foreground" />
        ) : (
          <Bot className="h-5 w-5 text-primary-foreground" />
        )}
      </div>
      <div
        className={cn(
          "max-w-[80%] space-y-3",
          isUser && "flex flex-col items-end"
        )}
      >
        {/* Structured Card (if any) */}
        {structuredContent && (
          <div className="w-full max-w-md">{renderStructuredCard()}</div>
        )}

        {/* Text Content */}
        {displayContent && (
          <div
            className={cn(
              "rounded-2xl px-4 py-3 shadow-sm",
              isUser
                ? "bg-primary text-primary-foreground"
                : "bg-card text-card-foreground"
            )}
          >
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown
                components={{
                  // Custom link renderer for clickable links
                  a: ({ href, children }) => (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline font-medium"
                    >
                      {children}
                    </a>
                  ),
                }}
              >
                {displayContent}
              </ReactMarkdown>
            </div>

            {/* PDF Download Buttons */}
            {pdfLinks.length > 0 && (
              <div className="mt-3 pt-3 border-t border-current/10 space-y-2">
                {pdfLinks.map((link, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    className="w-full bg-primary/10 hover:bg-primary/20 border-primary/30"
                    onClick={() => window.open(link.url, "_blank")}
                  >
                    <FileDown className="mr-2 h-4 w-4" />
                    {link.text || "Download Sanction Letter"}
                  </Button>
                ))}
              </div>
            )}

            <p
              className={cn(
                "mt-2 text-xs",
                isUser ? "text-primary-foreground/70" : "text-muted-foreground"
              )}
            >
              {message.timestamp.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;
