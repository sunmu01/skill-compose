"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { skillDependenciesApi, type InstallStreamEvent } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { AlertTriangle, Download, Loader2, Terminal, X } from "lucide-react";

interface DependenciesBannerProps {
  skillName: string;
  onInstallComplete?: () => void;
}

export function DependenciesBanner({ skillName, onInstallComplete }: DependenciesBannerProps) {
  const [dismissed, setDismissed] = React.useState(false);
  const [isInstalling, setIsInstalling] = React.useState(false);
  const [logDialogOpen, setLogDialogOpen] = React.useState(false);
  const [installLog, setInstallLog] = React.useState<string>("");
  const [installSuccess, setInstallSuccess] = React.useState<boolean | null>(null);
  const logEndRef = React.useRef<HTMLDivElement>(null);
  const abortControllerRef = React.useRef<AbortController | null>(null);

  // Fetch dependencies status
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["skill-dependencies", skillName],
    queryFn: () => skillDependenciesApi.getStatus(skillName),
    retry: false,
  });

  // Auto-scroll to bottom when log updates
  React.useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [installLog]);

  // Handle install with streaming
  const handleInstall = async () => {
    setIsInstalling(true);
    setInstallLog("");
    setInstallSuccess(null);
    setLogDialogOpen(true);

    abortControllerRef.current = new AbortController();

    try {
      await skillDependenciesApi.installStream(
        skillName,
        (event: InstallStreamEvent) => {
          if (event.event === "start") {
            setInstallLog((prev) => prev + `Starting installation for ${event.skill_name}...\n`);
          } else if (event.event === "log" && event.line) {
            setInstallLog((prev) => prev + event.line);
          } else if (event.event === "complete") {
            setInstallSuccess(event.success ?? false);
            setInstallLog((prev) =>
              prev + `\n--- Installation ${event.success ? "completed successfully" : "failed"} (exit code: ${event.return_code}) ---\n`
            );
          } else if (event.event === "error") {
            setInstallSuccess(false);
            setInstallLog((prev) => prev + `\nError: ${event.message}\n`);
          }
        },
        abortControllerRef.current.signal
      );
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setInstallLog((prev) => prev + `\nError: ${(err as Error).message}\n`);
        setInstallSuccess(false);
      }
    } finally {
      setIsInstalling(false);
      abortControllerRef.current = null;
      refetch();
      onInstallComplete?.();
    }
  };

  // Handle dialog close
  const handleDialogClose = (open: boolean) => {
    if (!open && isInstalling) {
      abortControllerRef.current?.abort();
    }
    setLogDialogOpen(open);
  };

  // Don't show if dismissed, loading, no data, or no install needed
  if (dismissed || isLoading || !data || !data.needs_install) {
    return null;
  }

  return (
    <>
      <div className="mb-4 rounded-lg border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-800 dark:bg-yellow-950">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
              Dependencies Required
            </h4>
            <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
              This skill has a setup.sh script that needs to be run to install dependencies.
            </p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setDismissed(true)}
              className="text-yellow-700 hover:text-yellow-800 hover:bg-yellow-100 dark:text-yellow-300 dark:hover:bg-yellow-900"
            >
              <X className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              onClick={handleInstall}
              disabled={isInstalling}
              className="bg-yellow-600 hover:bg-yellow-700 text-white"
            >
              {isInstalling ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Installing...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Install Now
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Installation Log Dialog */}
      <Dialog open={logDialogOpen} onOpenChange={handleDialogClose}>
        <DialogContent className="max-w-3xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Terminal className="h-5 w-5" />
              Installation Log
              {isInstalling && (
                <Badge variant="secondary" className="ml-2">
                  <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                  Running
                </Badge>
              )}
              {!isInstalling && installSuccess === true && (
                <Badge variant="success" className="ml-2">Success</Badge>
              )}
              {!isInstalling && installSuccess === false && (
                <Badge variant="destructive" className="ml-2">Failed</Badge>
              )}
            </DialogTitle>
            <DialogDescription>
              Output from running setup.sh for {skillName}
            </DialogDescription>
          </DialogHeader>

          <div className="h-[400px] w-full rounded-md border bg-black p-4 overflow-auto">
            <pre className="text-xs font-mono text-green-400 whitespace-pre-wrap break-words">
              {installLog || "Waiting for output..."}
              <div ref={logEndRef} />
            </pre>
          </div>

          <DialogFooter>
            {isInstalling ? (
              <Button
                variant="destructive"
                onClick={() => abortControllerRef.current?.abort()}
              >
                Cancel
              </Button>
            ) : (
              <Button variant="outline" onClick={() => setLogDialogOpen(false)}>
                Close
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
