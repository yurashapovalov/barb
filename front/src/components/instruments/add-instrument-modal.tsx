import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

interface AddInstrumentModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AddInstrumentModal({ open, onOpenChange }: AddInstrumentModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add instrument</DialogTitle>
          <DialogDescription>Search and add instruments to your workspace.</DialogDescription>
        </DialogHeader>
        <p className="text-sm text-muted-foreground">Instrument list coming soon.</p>
      </DialogContent>
    </Dialog>
  );
}
