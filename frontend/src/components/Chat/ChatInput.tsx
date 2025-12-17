import { useState, KeyboardEvent, useRef, useEffect } from "react";
import { Send, Mic, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import SpeechRecognition, {
  useSpeechRecognition,
} from "react-speech-recognition";
import QuickActionChips from "./QuickActionChips";
import { toast } from "sonner";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  autoFocus?: boolean;
  showQuickActions?: boolean;
  onQuickAction?: (action: string) => void;
}

const ChatInput = ({
  onSend,
  disabled,
  placeholder = "Type your message...",
  autoFocus = true,
  showQuickActions = false,
  onQuickAction,
}: ChatInputProps) => {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const {
    transcript,
    listening,
    browserSupportsSpeechRecognition,
    resetTranscript,
  } = useSpeechRecognition();
  const [baseText, setBaseText] = useState("");

  // Auto-focus the input when not disabled
  useEffect(() => {
    if (autoFocus && !disabled && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [disabled, autoFocus]);

  // Sync transcript into the message while listening
  useEffect(() => {
    if (listening) {
      setMessage((baseText + " " + transcript).trim());
    }
  }, [transcript, listening, baseText]);

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage("");
      resetTranscript();
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleStartListening = () => {
    if (!browserSupportsSpeechRecognition) {
      toast.error(
        "Speech recognition is not supported in this browser. Try Chrome or Edge."
      );
      return;
    }
    if (disabled) return;

    setBaseText(message);
    resetTranscript();
    SpeechRecognition.startListening({
      continuous: true,
      language: "en-US", // Changed to en-US for better compatibility
    })
      .then(() => {
        console.log("🎤 Started listening");
        toast.info("🎤 Listening... Speak now", { duration: 2000 });
      })
      .catch((err) => {
        console.error("Failed to start speech recognition:", err);
        toast.error("Could not start microphone. Please check permissions.");
      });
  };

  const handleStopListening = () => {
    SpeechRecognition.stopListening();
    console.log("🛑 Stopped listening. Transcript:", transcript);
    // Finalize the message with the captured transcript
    const finalMessage = (baseText + " " + transcript).trim();
    if (finalMessage) {
      setMessage(finalMessage);
    }
    setBaseText("");
    resetTranscript();
    toast.success("Voice input stopped", { duration: 1000 });
  };

  return (
    <div className="border-t border-border bg-white p-4">
      <div className="space-y-3">
        {/* Quick Action Chips */}
        {showQuickActions && onQuickAction && (
          <QuickActionChips onAction={onQuickAction} disabled={disabled} />
        )}

        {/* Input Area */}
        <div className="relative flex items-end gap-2">
          <Textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            className="min-h-[48px] max-h-32 resize-none rounded-xl bg-gray-50 pr-24"
            rows={1}
            autoFocus={autoFocus}
          />

          {/* Action Buttons Inside Input */}
          <div className="absolute bottom-2 right-2 flex items-center gap-1">
            {browserSupportsSpeechRecognition && (
              <Button
                type="button"
                variant={listening ? "destructive" : "ghost"}
                onClick={listening ? handleStopListening : handleStartListening}
                disabled={disabled}
                size="icon"
                className={`h-8 w-8 shrink-0 ${
                  listening ? "animate-pulse" : ""
                }`}
                title={listening ? "Stop recording" : "Start voice input"}
              >
                {listening ? (
                  <Square className="h-3.5 w-3.5" />
                ) : (
                  <Mic className="h-3.5 w-3.5" />
                )}
              </Button>
            )}

            <Button
              onClick={handleSend}
              disabled={!message.trim() || disabled}
              size="icon"
              className="h-8 w-8 shrink-0"
            >
              <Send className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInput;
