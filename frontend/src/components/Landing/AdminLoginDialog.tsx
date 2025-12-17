import { toast } from "sonner";
import type { FormEvent } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const AdminLoginDialog = ({
  open,
  onOpenChange,
  email,
  password,
  onEmailChange,
  onPasswordChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  email: string;
  password: string;
  onEmailChange: (val: string) => void;
  onPasswordChange: (val: string) => void;
}) => {
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    toast.success("Signed in (demo only)");
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Admin sign-in</DialogTitle>
          <DialogDescription>Demo-only authentication.</DialogDescription>
        </DialogHeader>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <Label htmlFor="admin-email">Email</Label>
            <Input
              id="admin-email"
              type="email"
              required
              value={email}
              onChange={(e) => onEmailChange(e.target.value)}
              placeholder="work email"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="admin-password">Password</Label>
            <Input
              id="admin-password"
              type="password"
              required
              value={password}
              onChange={(e) => onPasswordChange(e.target.value)}
              placeholder="password"
            />
          </div>
          <div className="flex gap-2">
            <Button type="submit" className="flex-1">
              Continue
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default AdminLoginDialog;
