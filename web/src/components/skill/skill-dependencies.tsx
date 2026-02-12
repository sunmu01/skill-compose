"use client";

import React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { skillDependenciesApi, type InstallStreamEvent } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  AlertCircle,
  CheckCircle2,
  Download,
  Loader2,
  RefreshCw,
  Terminal,
  XCircle,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface SkillDependenciesProps {
  skillName: string;
}

export function SkillDependencies({ skillName }: SkillDependenciesProps) {
  const queryClient = useQueryClient();
  const [isInstalling, setIsInstalling] = React.useState(false);
  const [logDialogOpen, setLogDialogOpen] = React.useState(false);
  const [installLog, setInstallLog] = React.useState<string>("");
  const [installSuccess, setInstallSuccess] = React.useState<boolean | null>(null);
  const logEndRef = React.useRef<HTMLDivElement>(null);
  const abortControllerRef = React.useRef<AbortController | null>(null);

  // Fetch dependencies status
  const { data, isLoading, error, refetch } = useQuery({
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
    }
  };

  // Handle view log click
  const handleViewLog = async () => {
    try {
      const logResult = await skillDependenciesApi.getInstallLog(skillName);
      setInstallLog(logResult.install_log);
      setInstallSuccess(data?.last_install_success ?? null);
      setLogDialogOpen(true);
    } catch {
      // Log not available
    }
  };

  // Handle dialog close
  const handleDialogClose = (open: boolean) => {
    if (!open && isInstalling) {
      // Cancel installation if closing while installing
      abortControllerRef.current?.abort();
    }
    setLogDialogOpen(open);
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading dependencies status...
      </div>
    );
  }

  // No setup.sh for this skill
  if (error || !data || !data.has_setup_script) {
    return (
      <div className="text-sm text-muted-foreground">
        No setup.sh found. This skill has no dependencies to install.
      </div>
    );
  }

  const { setup_script_path, last_installed_at, last_install_success, needs_install } = data;

  return (
    <div className="space-y-4">
      {/* Status Summary */}
      <div className="flex items-center gap-2">
        {last_install_success === true ? (
          <>
            <CheckCircle2 className="h-5 w-5 text-green-500" />
            <span className="text-sm font-medium text-green-700 dark:text-green-400">
              Dependencies installed
            </span>
          </>
        ) : last_install_success === false ? (
          <>
            <XCircle className="h-5 w-5 text-red-500" />
            <span className="text-sm font-medium text-red-700 dark:text-red-400">
              Last installation failed
            </span>
          </>
        ) : (
          <>
            <AlertCircle className="h-5 w-5 text-amber-500" />
            <span className="text-sm font-medium text-amber-700 dark:text-amber-400">
              Dependencies not installed
            </span>
          </>
        )}
      </div>

      {/* Setup Script Info */}
      <div className="p-3 rounded-lg border bg-card">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <Terminal className="h-4 w-4 text-muted-foreground" />
              <code className="text-sm font-mono font-medium">setup.sh</code>
              <Badge variant="outline" className="text-xs">
                Install Script
              </Badge>
            </div>
            {setup_script_path && (
              <p className="text-xs text-muted-foreground mt-1 ml-6 truncate">
                {setup_script_path}
              </p>
            )}
            {last_installed_at && (
              <p className="text-xs text-muted-foreground mt-1 ml-6">
                Last run: {new Date(last_installed_at).toLocaleString()}
              </p>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Status Badge */}
            {last_install_success === true ? (
              <Badge variant="success">Installed</Badge>
            ) : last_install_success === false ? (
              <Badge variant="destructive">Failed</Badge>
            ) : (
              <Badge variant="warning">Not Installed</Badge>
            )}

            {/* View Log Button (if there's a log) */}
            {last_installed_at && !isInstalling && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleViewLog}
              >
                View Log
              </Button>
            )}

            {/* Install/Reinstall Button */}
            <Button
              variant={needs_install ? "default" : "outline"}
              size="sm"
              onClick={handleInstall}
              disabled={isInstalling}
            >
              {isInstalling ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Installing...
                </>
              ) : last_installed_at ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Reinstall
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Install
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
    </div>
  );
}
