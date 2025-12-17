# LoanBuddy Frontend

AI-assisted personal loan web app built with Vite, React, TypeScript, Tailwind, and shadcn/ui. Connects to the backend at `http://127.0.0.1:8000` for chat, salary slip upload, and sanction letter download.

## Features

- Conversational loan assistant with structured cards for loan offers, eligibility, KYC, approvals, rejections, and summaries
- Loan calculator sidebar with EMI breakdown and purpose selection
- Salary slip upload (PDF/PNG/JPG), analyzed server-side; chat auto-notified with "uploaded"
- Sanction letter download by phone number
- Auto-focus chat input, dynamic placeholders, and local session persistence

## Getting Started

```sh
git clone <repo-url>
cd frontend
npm install
npm run dev    # starts Vite on http://localhost:5173 by default
```

## Environment & Config

- Backend base URL is defined in `src/services/api.ts` (currently `http://127.0.0.1:8000`).
- Phone number is the session identifier; tenure defaults to 12 months and can be changed in the UI.

## Available Scripts

- `npm run dev` – start the dev server
- `npm run build` – production build
- `npm run preview` – preview the production build
- `npm run lint` – lint the codebase

## Backend Endpoints (expected)

- `POST /chat` – chat messages (body: `{ session_id, message, tenure }`)
- `POST /upload?phone=<number>` – salary slip upload (multipart file)
- `GET /pdfs/{phone}_sanction.pdf` – download sanction letter
- `GET /health` – health check (optional)

## Structured Response Tags

The assistant renders rich cards when messages contain tagged JSON blocks:

- `[LOAN_OFFER]{...}[/LOAN_OFFER]`
- `[KYC_VERIFIED]{...}[/KYC_VERIFIED]`
- `[ELIGIBILITY]{...}[/ELIGIBILITY]`
- `[LOAN_SUMMARY]{...}[/LOAN_SUMMARY]`
- `[APPROVAL]{...}[/APPROVAL]`
- `[REJECTION]{...}[/REJECTION]`

## Notes

- Ensure the backend is running and reachable from the frontend origin.
- For salary slip flow: upload a file in the sidebar, then type or trigger "uploaded" to process.

## License

Proprietary / Internal use only (update if a license is chosen).
