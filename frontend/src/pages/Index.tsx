import { useState, useEffect } from "react";
import { useSession } from "@/context/SessionContext";
import { useChat } from "@/hooks/useChat";
import { checkHealth } from "@/services/api";
import Header from "@/components/Layout/Header";
import ChatWindow from "@/components/Chat/ChatWindow";
import ChatInput from "@/components/Chat/ChatInput";
import QuickActions from "@/components/QuickActions";
import LoanSidebar from "@/components/Sidebar/LoanSidebar";
import { Button } from "@/components/ui/button";
import { PanelRightOpen, PanelRightClose, WifiOff, Wifi } from "lucide-react";
import { toast } from "sonner";

const Index = () => {
  const { getEffectiveSessionId, tenure, resetSession, phone } = useSession();
  const sessionId = getEffectiveSessionId();
  const { messages, isLoading, send, clearMessages, sendSystemNotification } =
    useChat(sessionId, tenure);
  const [showSidebar, setShowSidebar] = useState(true);
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

  // Handler for when salary slip is uploaded - notify the chat
  const handleSalarySlipUploaded = () => {
    if (phone) {
      // Send "uploaded" message as per backend API docs
      sendSystemNotification("uploaded");
      toast.success("Salary slip uploaded! Processing...");
    }
  };

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

  return (
    <div className="flex h-screen flex-col bg-background">
      <Header onReset={handleReset} />

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
        <div className="flex flex-1 flex-col">
          {messages.length === 0 && (
            <QuickActions
              onAction={handleQuickAction}
              disabled={isLoading || isServerOnline === false}
            />
          )}

          <ChatWindow messages={messages} isLoading={isLoading} />

          <div className="relative">
            {isServerOnline && (
              <div className="absolute -top-6 left-4 flex items-center gap-1 text-xs text-green-600">
                <Wifi className="h-3 w-3" />
                <span>Connected</span>
              </div>
            )}
            <ChatInput
              onSend={send}
              disabled={isLoading || isServerOnline === false}
              placeholder={getPlaceholder()}
              autoFocus={!isLoading && isServerOnline !== false}
            />
          </div>
        </div>

        {/* Sidebar Toggle for Mobile */}
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

        {/* Sidebar */}
        <div
          className={`fixed inset-y-0 right-0 z-40 transform transition-transform duration-300 lg:relative lg:transform-none ${
            showSidebar ? "translate-x-0" : "translate-x-full"
          }`}
        >
          <LoanSidebar onSalarySlipUploaded={handleSalarySlipUploaded} />
        </div>
      </div>
    </div>
  );
};

export default Index;
