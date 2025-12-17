import axios from "axios";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000, // 30 second timeout for AI responses
});

export interface ChatRequest {
  session_id: string;
  message: string;
  tenure?: number;
}

export interface ChatResponse {
  response: string;
}

export interface HealthCheckResponse {
  status: string;
  agent: string;
}

export interface UploadResponse {
  status: boolean;
  msg: string;
}

// Health check endpoint
export const checkHealth = async (): Promise<HealthCheckResponse> => {
  const response = await api.get("/");
  return response.data;
};

// Main chat endpoint
export const sendMessage = async (
  sessionId: string,
  message: string,
  tenure: number = 12
): Promise<ChatResponse> => {
  const response = await api.post("/chat", {
    session_id: sessionId,
    message,
    tenure,
  });
  return response.data;
};

// Upload salary slip
export const uploadSalarySlip = async (
  sessionId: string,
  file: File
): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post(`/upload?phone=${sessionId}`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

// Get sanction letter PDF URL
export const getSanctionLetterUrl = (phone: string): string => {
  return `${API_BASE}/pdfs/${phone}_sanction.pdf`;
};

// Helper to extract PDF URLs from bot response
export const extractPdfUrl = (text: string): string | null => {
  const pdfMatch = text.match(/\[([^\]]+)\]\((http[^)]+\.pdf)\)/);
  if (pdfMatch) {
    return pdfMatch[2];
  }
  // Also check for plain URLs
  const plainUrlMatch = text.match(/(http[^\s]+\.pdf)/);
  if (plainUrlMatch) {
    return plainUrlMatch[1];
  }
  return null;
};

// Helper to format currency in Indian format
export const formatIndianCurrency = (amount: number): string => {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
};

// Parse loan amount from various formats (5 lakh, 2.5L, 50000, 40k)
export const parseLoanAmount = (text: string): number | null => {
  const lakhMatch = text.match(/(\d+(?:\.\d+)?)\s*(?:lakh|lac|l)/i);
  if (lakhMatch) {
    return parseFloat(lakhMatch[1]) * 100000;
  }

  const kMatch = text.match(/(\d+(?:\.\d+)?)\s*k/i);
  if (kMatch) {
    return parseFloat(kMatch[1]) * 1000;
  }

  const numMatch = text.match(/(\d+(?:,\d+)*(?:\.\d+)?)/);
  if (numMatch) {
    return parseFloat(numMatch[1].replace(/,/g, ""));
  }

  return null;
};
