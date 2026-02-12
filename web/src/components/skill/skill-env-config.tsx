"use client";

import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { skillConfigApi, type SkillSecretStatus } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  AlertCircle,
  CheckCircle2,
  Eye,
  EyeOff,
  Key,
  Loader2,
  Save,
  Trash2,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface SkillEnvConfigProps {
  skillName: string;
}

export function SkillEnvConfig({ skillName }: SkillEnvConfigProps) {
  const queryClient = useQueryClient();
  const [editingKey, setEditingKey] = React.useState<string | null>(null);
  const [secretValue, setSecretValue] = React.useState("");
  const [showValue, setShowValue] = React.useState(false);

  // Fetch secrets status
  const { data, isLoading, error } = useQuery({
    queryKey: ["skill-secrets", skillName],
    queryFn: () => skillConfigApi.getSecretsStatus(skillName),
    retry: false,
  });

  // Set secret mutation
  const setSecretMutation = useMutation({
    mutationFn: ({ keyName, value }: { keyName: string; value: string }) =>
      skillConfigApi.setSecret(skillName, keyName, value),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["skill-secrets", skillName] });
      setEditingKey(null);
      setSecretValue("");
    },
  });

  // Delete secret mutation
  const deleteSecretMutation = useMutation({
    mutationFn: (keyName: string) =>
      skillConfigApi.deleteSecret(skillName, keyName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["skill-secrets", skillName] });
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading config...
      </div>
    );
  }

  // No config for this skill
  if (error || !data) {
    return (
      <div className="text-sm text-muted-foreground">
        No environment configuration required for this skill.
      </div>
    );
  }

  const { ready, missing, status } = data;
  const entries = Object.entries(status);

  if (entries.length === 0) {
    return (
      <div className="text-sm text-muted-foreground">
        No environment configuration required for this skill.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Status Summary */}
      <div className="flex items-center gap-2">
        {ready ? (
          <>
            <CheckCircle2 className="h-5 w-5 text-green-500" />
            <span className="text-sm font-medium text-green-700 dark:text-green-400">
              All environment variables configured
            </span>
          </>
        ) : (
          <>
            <AlertCircle className="h-5 w-5 text-amber-500" />
            <span className="text-sm font-medium text-amber-700 dark:text-amber-400">
              Missing: {missing.join(", ")}
            </span>
          </>
        )}
      </div>

      {/* Environment Variables List */}
      <div className="space-y-3">
        {entries.map(([keyName, info]) => (
          <div
            key={keyName}
            className="flex items-center justify-between p-3 rounded-lg border bg-card"
          >
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <Key className="h-4 w-4 text-muted-foreground" />
                <code className="text-sm font-mono font-medium">{keyName}</code>
                {info.secret && (
                  <Badge variant="outline" className="text-xs">
                    Secret
                  </Badge>
                )}
              </div>
              {info.description && (
                <p className="text-xs text-muted-foreground mt-1 ml-6">
                  {info.description}
                </p>
              )}
            </div>

            <div className="flex items-center gap-2">
              {/* Status Badge */}
              {info.configured ? (
                <Badge
                  variant={
                    info.source === "secrets"
                      ? "default"
                      : info.source === "env"
                      ? "secondary"
                      : "outline"
                  }
                >
                  {(() => {
                    switch (info.source) {
                      case "secrets": return "UI Config";
                      case "env": return "Env Var";
                      case "default": return "Default";
                      default: return "Not Set";
                    }
                  })()}
                </Badge>
              ) : (
                <Badge variant="destructive">Missing</Badge>
              )}

              {/* Actions */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setEditingKey(keyName);
                  setSecretValue("");
                  setShowValue(false);
                }}
              >
                {info.configured && info.source === "secrets" ? "Edit" : "Set"}
              </Button>

              {info.configured && info.source === "secrets" && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-red-600 hover:text-red-700"
                  onClick={() => deleteSecretMutation.mutate(keyName)}
                  disabled={deleteSecretMutation.isPending}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Edit Secret Dialog */}
      <Dialog open={!!editingKey} onOpenChange={(open) => !open && setEditingKey(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Set Secret Value</DialogTitle>
            <DialogDescription>
              Enter the value for <code className="font-mono">{editingKey}</code>.
              This will be saved securely and take priority over environment variables.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="secret-value">Value</Label>
              <div className="relative">
                <Input
                  id="secret-value"
                  type={showValue ? "text" : "password"}
                  value={secretValue}
                  onChange={(e) => setSecretValue(e.target.value)}
                  placeholder="Enter secret value..."
                  className="pr-10"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3"
                  onClick={() => setShowValue(!showValue)}
                >
                  {showValue ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingKey(null)}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                if (editingKey && secretValue) {
                  setSecretMutation.mutate({ keyName: editingKey, value: secretValue });
                }
              }}
              disabled={!secretValue || setSecretMutation.isPending}
            >
              {setSecretMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
