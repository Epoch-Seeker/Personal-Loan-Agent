import { useState, useEffect, useMemo, useCallback } from "react";
import { useSession } from "@/context/SessionContext";
import { useChat } from "@/hooks/useChat";
import { checkHealth } from "@/services/api";
import Header from "@/components/Layout/Header";
import ChatWindow from "@/components/Chat/ChatWindow";
import ChatInput from "@/components/Chat/ChatInput";
import QuickActions from "@/components/QuickActions";
import JourneySidebar from "@/components/Sidebar/JourneySidebar";
import EMICalculatorDialog from "@/components/Chat/EMICalculatorDialog";
import UploadDialog from "@/components/Upload/UploadDialog";
import { Button } from "@/components/ui/button";
import LandingView from "@/components/Landing/LandingView";
import AdminLoginDialog from "@/components/Landing/AdminLoginDialog";
import { PanelRightOpen, PanelRightClose, WifiOff } from "lucide-react";
import { toast } from "sonner";
import { deriveLoanJourney } from "@/lib/loanJourney";
import type { ActionType } from "@/components/Chat/ActionButton";

const Index = () => {
  const { getEffectiveSessionId, tenure, resetSession, phone, setPhone } = useSession();
  const sessionId = getEffectiveSessionId();
  const { messages, isLoading, send, clearMessages, sendSystemNotification } =
    useChat(sessionId, tenure);
  const [showSidebar, setShowSidebar] = useState(false);
  const [sidebarTab, setSidebarTab] = useState<"calculator" | "upload">(
    "calculator"
  );
  const [showLanding, setShowLanding] = useState(true);
  const [showAdminLogin, setShowAdminLogin] = useState(false);
  const [showEMICalculator, setShowEMICalculator] = useState(false);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [adminEmail, setAdminEmail] = useState("");
  const [adminPass, setAdminPass] = useState("");
  const [isServerOnline, setIsServerOnline] = useState<boolean | null>(null);

  // Check server health on mount
  useEffect(() => {
    const checkServerHealth = async () => {
      try {
        await checkHealth();
        setIsServerOnline(true);
      } catch {
        setIsServerOnline(false);
        toast.error(
          "Unable to connect to server. Please ensure the backend is running."
        );
      }
    };

    checkServerHealth();
    // Re-check every 30 seconds
    const interval = setInterval(checkServerHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleReset = () => {
    resetSession();
    clearMessages();
    toast.success("Session reset. Starting fresh!");
  };

  const handleQuickAction = (message: string) => {
    send(message);
  };

  const handleQuickActionChip = (action: string) => {
    switch (action) {
      case "calculator":
        setShowEMICalculator(true);
        break;
      case "options":
        send("Show me all loan options");
        break;
      case "support":
        send("I need help from support");
        break;
    }
  };

  // Handler for when salary slip is uploaded
  const handleSalarySlipUploaded = () => {
    // Just send the notification, toast already shown by dialog
    if (phone) {
      sendSystemNotification("uploaded");
    }
  };

  // Handler for action buttons in chat messages
  const handleChatAction = useCallback((action: ActionType) => {
    switch (action) {
      case "UPLOAD_SALARY_SLIP":
        setShowUploadDialog(true);
        break;
      case "YES":
        send("yes");
        break;
      case "NO":
        send("no");
        break;
      case "SHOW_OPTIONS":
        send("Show me all loan options");
        break;
      default:
        console.log("Unknown action:", action);
    }
  }, [send]);

  // Hide landing once the user starts interacting
  useEffect(() => {
    if (messages.length > 0) {
      setShowLanding(false);
    }
  }, [messages.length]);

  const journey = useMemo(() => deriveLoanJourney(messages), [messages]);

  const [hasClosedUpload, setHasClosedUpload] = useState(false);

  // Reset unique session requirement flag if needsUpload becomes false
  useEffect(() => {
    if (!journey.needsUpload) {
      setHasClosedUpload(false);
    }
  }, [journey.needsUpload]);

  // Auto-open upload dialog when upload is needed
  useEffect(() => {
    if (journey.needsUpload && !showUploadDialog && !hasClosedUpload) {
      setShowUploadDialog(true);
    }
  }, [journey.needsUpload, showUploadDialog, hasClosedUpload]);

  // Dynamic placeholder based on conversation state
  const getPlaceholder = () => {
    if (isServerOnline === false) {
      return "Server offline...";
    }
    if (messages.length === 0) {
      return "Type your phone number to start or select a quick action...";
    }
    return "Type your response...";
  };

  // Auto-detect phone number from messages if not set
  useEffect(() => {
    if (!phone && messages.length > 0) {
      const phoneMsg = [...messages]
        .reverse()
        .find(
          (m) =>
            m.role === "user" && /\b[6-9]\d{9}\b/.test(m.content)
        );
      
      if (phoneMsg) {
        const match = phoneMsg.content.match(/\b([6-9]\d{9})\b/);
        if (match) {
          setPhone(match[1]);
        }
      }
    }
  }, [messages, phone, setPhone]);

  if (showLanding) {
    return (
      <div className="min-h-screen bg-background">
        <LandingView
          onGetStarted={() => setShowLanding(false)}
          onAdmin={() => setShowAdminLogin(true)}
          serverOnline={isServerOnline !== false}
        />
        <AdminLoginDialog
          open={showAdminLogin}
          onOpenChange={setShowAdminLogin}
          email={adminEmail}
          password={adminPass}
          onEmailChange={setAdminEmail}
          onPasswordChange={setAdminPass}
        />
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-background">
      <Header onReset={messages.length > 0 ? handleReset : undefined} />

      {/* Server Status Banner */}
      {isServerOnline === false && (
        <div className="flex items-center justify-center gap-2 bg-destructive px-4 py-2 text-destructive-foreground">
          <WifiOff className="h-4 w-4" />
          <span className="text-sm">
            Server offline. Please start the backend server.
          </span>
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        {/* Main Chat Area */}
        <div className="relative flex flex-1 flex-col">
          {messages.length === 0 && (
            <QuickActions
              onAction={handleQuickAction}
              disabled={isLoading || isServerOnline === false}
            />
          )}

          <ChatWindow messages={messages} isLoading={isLoading} onAction={handleChatAction} />

          <ChatInput
            onSend={send}
            disabled={isLoading || isServerOnline === false}
            placeholder={getPlaceholder()}
            autoFocus={!isLoading && isServerOnline !== false}
            showQuickActions={messages.length > 0}
            onQuickAction={handleQuickActionChip}
          />
        </div>

        {/* Sidebar Toggle - mobile only */}
        <Button
          variant="outline"
          size="icon"
          onClick={() => setShowSidebar(!showSidebar)}
          className="fixed bottom-24 right-4 z-50 lg:hidden"
        >
          {showSidebar ? (
            <PanelRightClose className="h-5 w-5" />
          ) : (
            <PanelRightOpen className="h-5 w-5" />
          )}
        </Button>

        {/* Sidebar - always visible on desktop, overlay on mobile */}
        <div
          className={`
            fixed inset-y-0 right-0 z-40 w-80 border-l border-border bg-card
            transform transition-transform duration-300
            lg:relative lg:transform-none lg:z-auto lg:w-80
            ${
              showSidebar
                ? "translate-x-0"
                : "translate-x-full lg:translate-x-0"
            }
          `}
        >
          <JourneySidebar
            steps={journey.steps}
            canDownloadSanction={journey.canDownloadSanction}
            salarySlipUploaded={journey.steps.find(s => s.key === 'docs')?.status === 'done'}
            onExit={() => setShowLanding(true)}
            onSupport={() => send("I need help from support")}
          />
        </div>
      </div>

      {/* EMI Calculator Dialog */}
      <EMICalculatorDialog
        open={showEMICalculator}
        onOpenChange={setShowEMICalculator}
      />

      {/* Upload Dialog */}
      <UploadDialog
        open={showUploadDialog}
        onOpenChange={(open) => {
          setShowUploadDialog(open);
          if (!open) {
            setHasClosedUpload(true);
          }
        }}
        onUploadComplete={handleSalarySlipUploaded}
      />
    </div>
  );
};

export default Index;
