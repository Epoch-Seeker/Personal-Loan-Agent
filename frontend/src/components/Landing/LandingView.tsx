import { ArrowRight, ShieldCheck, Sparkles, WifiOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const LandingView = ({
  onGetStarted,
  onAdmin,
  serverOnline,
}: {
  onGetStarted: () => void;
  onAdmin: () => void;
  serverOnline: boolean;
}) => {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-6 pb-24 pt-10 lg:pt-16">
      <div className="grid gap-10 lg:grid-cols-2 lg:items-center">
        <div className="space-y-6">
          <div className="lb-pill inline-flex items-center gap-2">
            <ShieldCheck className="h-4 w-4" />
            Bank-grade security
          </div>

          <h1 className="text-4xl font-bold leading-tight tracking-tight text-foreground sm:text-5xl">
            Personal loans, explained and processed in chat.
          </h1>
          <p className="max-w-2xl text-lg text-muted-foreground">
            Verify KYC, upload salary slips, and get your sanction letter with a
            simple, guided flow.
          </p>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <Button size="lg" className="gap-2" onClick={onGetStarted}>
              Start chat
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="lg" onClick={onAdmin}>
              Admin sign-in
            </Button>
          </div>

          {!serverOnline && (
            <div className="lb-pill inline-flex items-center gap-2 bg-destructive/10 text-destructive">
              <WifiOff className="h-4 w-4" />
              Backend offline. Please start the server.
            </div>
          )}

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {["KYC & eligibility", "Salary slip upload", "Sanction letter"].map(
              (item) => (
                <Card key={item} className="border-border">
                  <CardContent className="flex items-center gap-2 py-4 text-sm font-medium text-foreground">
                    <Sparkles className="h-4 w-4 text-primary" />
                    {item}
                  </CardContent>
                </Card>
              )
            )}
          </div>
        </div>

        <div className="lb-surface p-6">
          <div className="flex items-center justify-between border-b border-border pb-4">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                What you get
              </p>
              <p className="text-lg font-semibold text-foreground">
                A guided loan journey
              </p>
            </div>
          </div>
          <div className="mt-4 space-y-3">
            {[
              "Enter phone number",
              "Get offer",
              "Upload salary slip",
              "Download letter",
            ].map((label) => (
              <div
                key={label}
                className="flex items-center justify-between rounded-xl border border-border bg-muted/20 px-4 py-3"
              >
                <div className="text-sm font-medium text-foreground">
                  {label}
                </div>
                <div className="text-xs font-semibold text-muted-foreground">
                  ~2 min
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
};

export default LandingView;
