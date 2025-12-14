import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { v4 as uuidv4 } from "uuid";

interface SessionContextType {
  sessionId: string;
  phone: string;
  tenure: number;
  setPhone: (phone: string) => void;
  setTenure: (tenure: number) => void;
  resetSession: () => void;
  // Use phone as session ID when available (backend uses phone for session tracking)
  getEffectiveSessionId: () => string;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export const SessionProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [sessionId, setSessionId] = useState<string>(() => {
    const stored = localStorage.getItem("loan_session_id");
    return stored || uuidv4();
  });

  const [phone, setPhoneState] = useState<string>(() => {
    return localStorage.getItem("loan_user_phone") || "";
  });

  const [tenure, setTenureState] = useState<number>(() => {
    const stored = localStorage.getItem("loan_tenure");
    return stored ? parseInt(stored, 10) : 12;
  });

  useEffect(() => {
    localStorage.setItem("loan_session_id", sessionId);
  }, [sessionId]);

  useEffect(() => {
    localStorage.setItem("loan_user_phone", phone);
  }, [phone]);

  useEffect(() => {
    localStorage.setItem("loan_tenure", tenure.toString());
  }, [tenure]);

  const setPhone = (newPhone: string) => {
    setPhoneState(newPhone);
  };

  const setTenure = (newTenure: number) => {
    setTenureState(newTenure);
  };

  const resetSession = () => {
    const newSessionId = uuidv4();
    setSessionId(newSessionId);
    setPhoneState("");
    localStorage.setItem("loan_session_id", newSessionId);
    localStorage.removeItem("loan_user_phone");
    localStorage.removeItem("loan_chat_messages");
  };

  // Backend uses phone number as session identifier
  const getEffectiveSessionId = () => {
    return phone || sessionId;
  };

  return (
    <SessionContext.Provider
      value={{
        sessionId,
        phone,
        tenure,
        setPhone,
        setTenure,
        resetSession,
        getEffectiveSessionId,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
};

export const useSession = () => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSession must be used within a SessionProvider");
  }
  return context;
};
