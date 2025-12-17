import { useState, useCallback, useEffect } from "react";
import { sendMessage, ChatResponse } from "@/services/api";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

const STORAGE_KEY = "loan_chat_messages";

// Helper to serialize/deserialize messages for localStorage
const serializeMessages = (messages: Message[]): string => {
  return JSON.stringify(
    messages.map((m) => ({
      ...m,
      timestamp: m.timestamp.toISOString(),
    }))
  );
};

const deserializeMessages = (data: string): Message[] => {
  try {
    const parsed = JSON.parse(data);
    return parsed.map(
      (m: {
        id: string;
        role: "user" | "assistant";
        content: string;
        timestamp: string;
      }) => ({
        ...m,
        timestamp: new Date(m.timestamp),
      })
    );
  } catch {
    return [];
  }
};

export const useChat = (sessionId: string, tenure: number = 12) => {
  const [messages, setMessages] = useState<Message[]>(() => {
    // Load messages from localStorage on init
    const stored = localStorage.getItem(`${STORAGE_KEY}_${sessionId}`);
    return stored ? deserializeMessages(stored) : [];
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Persist messages to localStorage whenever they change
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem(
        `${STORAGE_KEY}_${sessionId}`,
        serializeMessages(messages)
      );
    }
  }, [messages, sessionId]);

  const addMessage = useCallback(
    (role: "user" | "assistant", content: string) => {
      const newMessage: Message = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        role,
        content,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, newMessage]);
      return newMessage;
    },
    []
  );

  const send = useCallback(
    async (message: string) => {
      if (!message.trim()) return;

      setError(null);
      addMessage("user", message);
      setIsLoading(true);

      try {
        const response: ChatResponse = await sendMessage(
          sessionId,
          message,
          tenure
        );
        addMessage("assistant", response.response);
      } catch (err) {
        let errorMessage = "Failed to send message";
        if (err instanceof Error) {
          errorMessage = err.message;
        }
        // Check for axios error structure
        if (typeof err === "object" && err !== null && "response" in err) {
          const axiosErr = err as { response?: { data?: { detail?: string } } };
          if (axiosErr.response?.data?.detail) {
            errorMessage = axiosErr.response.data.detail;
          }
        }
        setError(errorMessage);
        addMessage(
          "assistant",
          "😔 Sorry, I encountered an error connecting to the server. Please try again."
        );
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, tenure, addMessage]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    localStorage.removeItem(`${STORAGE_KEY}_${sessionId}`);
  }, [sessionId]);

  // Send a system message (for upload notifications etc.)
  // Note: we do not pre-add the user message here because `send` already
  // adds the user message before posting to the server. Adding it twice would
  // duplicate the "uploaded" text in the chat history.
  const sendSystemNotification = useCallback(
    (message: string) => {
      send(message);
    },
    [send]
  );

  return {
    messages,
    isLoading,
    error,
    send,
    clearMessages,
    sendSystemNotification,
    addMessage,
  };
};
