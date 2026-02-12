"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { RefreshCw } from "lucide-react";

interface FilesystemSyncDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  oldVersion: string;
  newVersion: string;
  changesSummary?: string;
}

export function FilesystemSyncDialog({
  open,
  onOpenChange,
  oldVersion,
  newVersion,
  changesSummary,
}: FilesystemSyncDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5 text-blue-500" />
            Filesystem Changes Synced
          </DialogTitle>
          <DialogDescription>
            Local files on disk differ from the database version. A new version
            has been created automatically.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2 text-sm">
          <p>
            <span className="text-muted-foreground">Version:</span>{" "}
            <span className="font-mono">v{oldVersion}</span>
            {" → "}
            <span className="font-mono font-semibold">v{newVersion}</span>
          </p>
          {changesSummary && (
            <p>
              <span className="text-muted-foreground">Changes:</span>{" "}
              {changesSummary}
            </p>
          )}
        </div>
        <DialogFooter>
          <Button onClick={() => onOpenChange(false)}>OK</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
