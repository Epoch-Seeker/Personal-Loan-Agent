import type { Message } from "@/hooks/useChat";

export type JourneyStepStatus = "pending" | "current" | "done" | "failed";

export type JourneyStep = {
  key: "details" | "kyc" | "offer" | "docs" | "decision";
  title: string;
  caption: string;
  status: JourneyStepStatus;
};

export type LoanJourneyState = {
  started: boolean;
  needsUpload: boolean;
  canDownloadSanction: boolean;
  steps: JourneyStep[];
};

const TAGS = [
  "KYC_VERIFIED",
  "LOAN_OFFER",
  "ELIGIBILITY",
  "LOAN_SUMMARY",
  "APPROVAL",
  "REJECTION",
] as const;

const hasAnyTag = (messages: Message[]) =>
  messages.some((m) => TAGS.some((t) => m.content.includes(`[${t}]`)));

const hasTag = (messages: Message[], tag: (typeof TAGS)[number]) =>
  messages.some((m) => m.content.includes(`[${tag}]`));

const hasUploadedSignal = (messages: Message[]) =>
  messages.some(
    (m) => m.role === "user" && m.content.toLowerCase().includes("uploaded")
  );

const hasPhoneLike = (messages: Message[]) =>
  messages.some((m) => m.role === "user" && /\b\d{10}\b/.test(m.content));

const assistantRequestsUpload = (messages: Message[]) => {
  const pattern =
    /upload\s+(your\s+)?(salary\s+slip|payslip|salary|income\s+proof)|salary\s+slip|income\s+proof|attach\s+(a\s+)?(pdf|document)/i;
  return messages.some(
    (m) => m.role === "assistant" && pattern.test(m.content)
  );
};

export const deriveLoanJourney = (messages: Message[]): LoanJourneyState => {
  const rejected = hasTag(messages, "REJECTION");
  const approved = hasTag(messages, "APPROVAL");

  const detailsDone = hasPhoneLike(messages);
  const kycDone = hasTag(messages, "KYC_VERIFIED");
  const offerDone =
    hasTag(messages, "LOAN_OFFER") ||
    hasTag(messages, "ELIGIBILITY") ||
    hasTag(messages, "LOAN_SUMMARY");
  const docsDone = hasUploadedSignal(messages);

  const uploadRequested = assistantRequestsUpload(messages);
  const needsUpload = uploadRequested && !docsDone && !approved && !rejected;

  const started =
    messages.length > 0 &&
    (detailsDone || hasAnyTag(messages) || uploadRequested);

  const steps: JourneyStep[] = [
    {
      key: "details",
      title: "Details",
      caption: "Phone & basics",
      status: "pending",
    },
    { key: "kyc", title: "KYC", caption: "Verification", status: "pending" },
    { key: "offer", title: "Offer", caption: "Eligibility", status: "pending" },
    { key: "docs", title: "Docs", caption: "Salary slip", status: "pending" },
    {
      key: "decision",
      title: "Decision",
      caption: "Sanction",
      status: "pending",
    },
  ];

  const set = (key: JourneyStep["key"], status: JourneyStepStatus) => {
    const item = steps.find((s) => s.key === key);
    if (item) item.status = status;
  };

  if (detailsDone) set("details", "done");
  if (kycDone) set("kyc", "done");
  if (offerDone) set("offer", "done");
  if (docsDone) set("docs", "done");

  if (rejected) set("decision", "failed");
  else if (approved) set("decision", "done");

  // Mark first pending after last done as current
  for (let index = 0; index < steps.length; index += 1) {
    if (steps[index].status !== "pending") continue;
    const prevOk = index === 0 || steps[index - 1].status === "done";
    if (prevOk) {
      steps[index].status = "current";
      break;
    }
  }

  return {
    started,
    needsUpload,
    canDownloadSanction: approved,
    steps,
  };
};
