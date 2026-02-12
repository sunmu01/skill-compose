"use client";

import React from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useMCPServers } from "@/hooks/use-mcp";
import { mcpApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Plug, Plus, Trash2, Lock, Key, Check, X, Eye, EyeOff, ChevronDown, ChevronUp, Minus, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { EmptyState } from "@/components/ui/empty-state";
import { useTranslation } from "@/i18n/client";
import type { MCPServerInfo, MCPToolInfo, SecretStatus } from "@/lib/api";

// Built-in MCP servers that cannot be deleted
const BUILTIN_MCP_SERVERS = ["time", "tavily", "git"];

function MCPToolCard({ tool }: { tool: MCPToolInfo }) {
  return (
    <div className="p-3 rounded-lg border bg-muted/30">
      <div className="flex items-center gap-2">
        <code className="text-sm font-mono font-medium">{tool.name}</code>
      </div>
      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
        {tool.description}
      </p>
    </div>
  );
}

function SecretConfigDialog({
  serverName,
  keyName,
  status,
  onSave,
  t,
  tc,
}: {
  serverName: string;
  keyName: string;
  status: SecretStatus;
  onSave: () => Promise<void> | void;
  t: (key: string, options?: Record<string, unknown>) => string;
  tc: (key: string) => string;
}) {
  const [open, setOpen] = React.useState(false);
  const [value, setValue] = React.useState("");
  const [showValue, setShowValue] = React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!value.trim()) {
      setError(t('secrets.placeholder'));
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      await mcpApi.setSecret(serverName, keyName, value.trim());
      await onSave();
      setOpen(false);
      setValue("");
    } catch (err) {
      setError(err instanceof Error ? err.message : t('secrets.error'));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    setIsSubmitting(true);
    try {
      await mcpApi.deleteSecret(serverName, keyName);
      await onSave();
      setOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('secrets.error'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant={status.configured ? "outline" : "default"}
          size="sm"
          className="h-7 text-xs"
        >
          <Key className="h-3 w-3 mr-1" />
          {status.configured ? t('secrets.update') : t('secrets.configure')}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{t('secrets.title')}</DialogTitle>
            <DialogDescription>
              {t('secrets.description')} <code className="bg-muted px-1 rounded">{keyName}</code>
            </DialogDescription>
          </DialogHeader>

          <div className="py-4 space-y-4">
            {status.source === "env" && (
              <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-md">
                <p className="text-sm text-blue-600 dark:text-blue-400">
                  <strong>Info:</strong> {t('secrets.envFallbackInfo')}
                </p>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="api-key">{t('secrets.apiKey')}</Label>
              <div className="relative">
                <Input
                  id="api-key"
                  type={showValue ? "text" : "password"}
                  placeholder={t('secrets.placeholder')}
                  value={value}
                  onChange={(e) => setValue(e.target.value)}
                  className="pr-10"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
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
              <p className="text-xs text-muted-foreground">
                {t('secrets.savedTo')} <code>config/mcp-secrets.json</code>
              </p>
            </div>

            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </div>

          <DialogFooter className="gap-2">
            {status.configured && status.source === "secrets" && (
              <Button
                type="button"
                variant="destructive"
                onClick={handleDelete}
                disabled={isSubmitting}
              >
                {tc('actions.delete')}
              </Button>
            )}
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              {tc('actions.cancel')}
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? tc('actions.processing') : tc('actions.save')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function SecretsSection({
  server,
  onUpdate,
  t,
  tc,
}: {
  server: MCPServerInfo;
  onUpdate: () => Promise<void> | void;
  t: (key: string, options?: Record<string, unknown>) => string;
  tc: (key: string) => string;
}) {
  if (!server.required_env_vars || server.required_env_vars.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 pt-4 border-t">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
        <Key className="h-3 w-3 inline mr-1" />
        {t('requiredApiKeys')}
      </p>
      <div className="space-y-2">
        {server.required_env_vars.map((keyName) => {
          const status = server.secrets_status?.[keyName] || { configured: false, source: "none" };
          return (
            <div
              key={keyName}
              className="flex items-center justify-between p-2 rounded border bg-muted/20"
            >
              <div className="flex items-center gap-2">
                <code className="text-xs font-mono">{keyName}</code>
                {status.configured ? (
                  <Badge variant="outline-success" className="text-xs">
                    <Check className="h-3 w-3 mr-1" />
                    {status.source === "env" ? t('fromEnv') : t('configured')}
                  </Badge>
                ) : (
                  <Badge variant="outline-error" className="text-xs">
                    <X className="h-3 w-3 mr-1" />
                    {t('notSet')}
                  </Badge>
                )}
              </div>
              <SecretConfigDialog
                serverName={server.name}
                keyName={keyName}
                status={status}
                onSave={onUpdate}
                t={t}
                tc={tc}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}

const TOOLS_COLLAPSE_THRESHOLD = 3;

function ToolsList({
  tools,
  hasSecrets,
  t,
}: {
  tools: MCPToolInfo[];
  hasSecrets: boolean;
  t: (key: string, options?: Record<string, unknown>) => string;
}) {
  const [expanded, setExpanded] = React.useState(false);
  const shouldCollapse = tools.length > TOOLS_COLLAPSE_THRESHOLD;
  const visibleTools = shouldCollapse && !expanded
    ? tools.slice(0, TOOLS_COLLAPSE_THRESHOLD)
    : tools;
  const hiddenCount = tools.length - TOOLS_COLLAPSE_THRESHOLD;

  return (
    <div className={`space-y-2 ${hasSecrets ? "mt-4 pt-4 border-t" : ""}`}>
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
        {t('availableToolsCount', { count: tools.length })}
      </p>
      <div className="grid gap-2">
        {visibleTools.map((tool) => (
          <MCPToolCard key={tool.name} tool={tool} />
        ))}
      </div>
      {shouldCollapse && (
        <Button
          variant="ghost"
          size="sm"
          className="w-full text-xs text-muted-foreground hover:text-foreground"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? (
            <>
              <ChevronUp className="h-3 w-3 mr-1" />
              {t('showLess')}
            </>
          ) : (
            <>
              <ChevronDown className="h-3 w-3 mr-1" />
              {t('showMoreTools', { count: hiddenCount })}
            </>
          )}
        </Button>
      )}
    </div>
  );
}

function MCPServerCard({
  server,
  onDelete,
  onUpdate,
  isBuiltIn,
  t,
  tc,
}: {
  server: MCPServerInfo;
  onDelete: (name: string) => void;
  onUpdate: () => Promise<void> | void;
  isBuiltIn: boolean;
  t: (key: string, options?: Record<string, unknown>) => string;
  tc: (key: string) => string;
}) {
  const [isDiscovering, setIsDiscovering] = React.useState(false);

  // Check if server has unconfigured required keys
  const hasUnconfiguredKeys = server.required_env_vars?.some(
    (key) => !server.secrets_status?.[key]?.configured
  );

  const handleDiscover = async () => {
    setIsDiscovering(true);
    try {
      const result = await mcpApi.discoverTools(server.name);
      if (result.success) {
        toast.success(t('discover.success', { count: result.tools_count }));
        await onUpdate();
      } else {
        toast.error(result.error || t('discover.failed'));
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : t('discover.failed'));
    } finally {
      setIsDiscovering(false);
    }
  };

  return (
    <Card className={hasUnconfiguredKeys ? "border-yellow-500/50" : ""}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-md ${hasUnconfiguredKeys ? "bg-yellow-500/10 text-yellow-500" : "bg-purple-500/10 text-purple-500"}`}>
              <Plug className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-base">{server.display_name}</CardTitle>
              <p className="text-xs text-muted-foreground mt-0.5">{server.name}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {hasUnconfiguredKeys && (
              <Badge variant="outline-warning" className="text-xs">
                <Key className="h-3 w-3 mr-1" />
                {t('needsConfig')}
              </Badge>
            )}
            {isBuiltIn && (
              <Badge variant="outline" className="text-xs">
                <Lock className="h-3 w-3 mr-1" />
                {t('builtIn')}
              </Badge>
            )}
            {server.default_enabled && (
              <Badge variant="secondary" className="text-xs">
                {t('defaultEnabled')}
              </Badge>
            )}
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={handleDiscover}
              disabled={isDiscovering}
              title={server.tools.length > 0 ? t('discover.refreshTools') : t('discover.discoverTools')}
            >
              <RefreshCw className={`h-4 w-4 ${isDiscovering ? "animate-spin" : ""}`} />
            </Button>
            {isBuiltIn ? (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-muted-foreground cursor-not-allowed"
                disabled
                title={t('delete.cannotDelete')}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            ) : (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>{t('delete.title')}</AlertDialogTitle>
                    <AlertDialogDescription>
                      {t('delete.confirm', { name: server.display_name })}
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>{tc('actions.cancel')}</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={() => onDelete(server.name)}
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    >
                      {tc('actions.delete')}
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-sm text-muted-foreground mb-4">
          {server.description}
        </p>

        {/* API Keys Section */}
        <SecretsSection server={server} onUpdate={onUpdate} t={t} tc={tc} />

        {server.tools.length > 0 ? (
          <ToolsList
            tools={server.tools}
            hasSecrets={!!server.required_env_vars?.length}
            t={t}
          />
        ) : (
          <div className={`text-sm text-muted-foreground italic ${server.required_env_vars?.length ? "mt-4 pt-4 border-t" : ""}`}>
            {t('discover.noTools')}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function AddServerDialog({ onAdd, t, tc }: { onAdd: () => void; t: (key: string, options?: Record<string, unknown>) => string; tc: (key: string) => string }) {
  const [open, setOpen] = React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const [formData, setFormData] = React.useState({
    name: "",
    display_name: "",
    description: "",
    command: "uvx",
    default_enabled: false,
  });
  const [argRows, setArgRows] = React.useState<string[]>([""]);
  const [envRows, setEnvRows] = React.useState<{ key: string; value: string }[]>([{ key: "", value: "" }]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const args = argRows.map((s) => s.trim()).filter((s) => s.length > 0);

      const env: Record<string, string> = {};
      envRows.forEach(({ key, value }) => {
        const k = key.trim();
        if (k) env[k] = value.trim();
      });

      const serverName = formData.name;

      await mcpApi.createServer({
        name: serverName,
        display_name: formData.display_name,
        description: formData.description,
        command: formData.command,
        args,
        env,
        default_enabled: formData.default_enabled,
        tools: [],
      });

      setOpen(false);
      setFormData({ name: "", display_name: "", description: "", command: "uvx", default_enabled: false });
      setArgRows([""]);
      setEnvRows([{ key: "", value: "" }]);
      onAdd();

      // Fire-and-forget: auto-discover tools for the new server
      mcpApi.discoverTools(serverName).then((result) => {
        if (result.success && result.tools_count > 0) {
          toast.success(t('discover.autoDiscovered', { count: result.tools_count }));
          onAdd();
        }
      }).catch(() => {
        // Discovery failure is non-fatal; server was already created
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : t('create.error'));
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateArg = (index: number, value: string) => {
    const updated = [...argRows];
    updated[index] = value;
    setArgRows(updated);
  };
  const addArg = () => setArgRows([...argRows, ""]);
  const removeArg = (index: number) => {
    if (argRows.length <= 1) { setArgRows([""]); return; }
    setArgRows(argRows.filter((_, i) => i !== index));
  };

  const updateEnv = (index: number, field: "key" | "value", val: string) => {
    const updated = [...envRows];
    updated[index] = { ...updated[index], [field]: val };
    setEnvRows(updated);
  };
  const addEnv = () => setEnvRows([...envRows, { key: "", value: "" }]);
  const removeEnv = (index: number) => {
    if (envRows.length <= 1) { setEnvRows([{ key: "", value: "" }]); return; }
    setEnvRows(envRows.filter((_, i) => i !== index));
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          {t('addServer.addServer')}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{t('addServer.title')}</DialogTitle>
            <DialogDescription>
              {t('addServer.description')}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">{t('addServer.serverId')}</Label>
                <Input
                  id="name"
                  placeholder={t('addServer.serverIdPlaceholder')}
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
                <p className="text-xs text-muted-foreground">{t('addServer.serverIdHelp')}</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="display_name">{t('addServer.displayName')}</Label>
                <Input
                  id="display_name"
                  placeholder={t('addServer.displayNamePlaceholder')}
                  value={formData.display_name}
                  onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">{t('addServer.description2')}</Label>
              <Textarea
                id="description"
                placeholder={t('addServer.descriptionPlaceholder')}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={2}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="command">{t('addServer.command')}</Label>
              <Input
                id="command"
                placeholder={t('addServer.commandPlaceholder')}
                value={formData.command}
                onChange={(e) => setFormData({ ...formData, command: e.target.value })}
                required
              />
              <p className="text-xs text-muted-foreground">{t('addServer.commandHelp')}</p>
            </div>

            {/* Dynamic Args rows */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>{t('addServer.arguments')}</Label>
                <Button type="button" variant="ghost" size="sm" className="h-7 text-xs" onClick={addArg}>
                  <Plus className="h-3 w-3 mr-1" />
                  {tc('actions.add')}
                </Button>
              </div>
              <div className="space-y-2">
                {argRows.map((arg, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <Input
                      placeholder={t('addServer.argumentsPlaceholder')}
                      value={arg}
                      onChange={(e) => updateArg(i, e.target.value)}
                      className="flex-1"
                    />
                    <Button type="button" variant="ghost" size="icon" className="h-8 w-8 shrink-0 text-muted-foreground hover:text-destructive" onClick={() => removeArg(i)}>
                      <Minus className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">{t('addServer.argumentsHelp')}</p>
            </div>

            {/* Dynamic Env rows */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>{t('addServer.envVars')}</Label>
                <Button type="button" variant="ghost" size="sm" className="h-7 text-xs" onClick={addEnv}>
                  <Plus className="h-3 w-3 mr-1" />
                  {t('create.envAdd')}
                </Button>
              </div>
              <div className="space-y-2">
                {envRows.map((row, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <Input
                      placeholder={t('create.envKey')}
                      value={row.key}
                      onChange={(e) => updateEnv(i, "key", e.target.value)}
                      className="flex-1"
                    />
                    <span className="text-muted-foreground">=</span>
                    <Input
                      placeholder={t('create.envValue')}
                      value={row.value}
                      onChange={(e) => updateEnv(i, "value", e.target.value)}
                      className="flex-1"
                    />
                    <Button type="button" variant="ghost" size="icon" className="h-8 w-8 shrink-0 text-muted-foreground hover:text-destructive" onClick={() => removeEnv(i)}>
                      <Minus className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">{t('addServer.envVarsHelp')}</p>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="default_enabled"
                checked={formData.default_enabled}
                onCheckedChange={(checked) => setFormData({ ...formData, default_enabled: checked })}
              />
              <Label htmlFor="default_enabled">{t('addServer.enableByDefault')}</Label>
            </div>

            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              {tc('actions.cancel')}
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? t('addServer.adding') : t('addServer.addServer')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function MCPPage() {
  const { t } = useTranslation('mcp');
  const { t: tc } = useTranslation('common');
  const queryClient = useQueryClient();
  const { data: mcpData, isLoading } = useMCPServers();

  const handleDelete = async (name: string) => {
    try {
      await mcpApi.deleteServer(name);
      queryClient.invalidateQueries({ queryKey: ["mcp-servers"] });
    } catch (err) {
      console.error("Failed to delete server:", err);
    }
  };

  const handleAdd = async () => {
    await queryClient.invalidateQueries({ queryKey: ["mcp-servers"] });
  };

  return (
    <div className="container max-w-6xl py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">{t('title')}</h1>
          <p className="text-muted-foreground mt-1">
            {t('description')}
          </p>
        </div>
        <AddServerDialog onAdd={handleAdd} t={t} tc={tc} />
      </div>

      {/* Content */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plug className="h-5 w-5" />
            {t('availableServers')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <p className="text-muted-foreground">{tc('actions.loading')}</p>
            </div>
          ) : !mcpData || mcpData.servers.length === 0 ? (
            <EmptyState
              icon={Plug}
              title={t('list.empty')}
              description={t('list.emptyDescription')}
            />
          ) : (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  {t('mcpInfo')}
                </p>
                <Badge variant="outline">{t('serversCount', { count: mcpData.servers.length })}</Badge>
              </div>

              {(() => {
                const defaultServers = mcpData.servers.filter((s) => s.default_enabled);
                const optionalServers = mcpData.servers.filter((s) => !s.default_enabled);

                return (
                  <>
                    {defaultServers.length > 0 && (
                      <div>
                        <h3 className="font-medium mb-3 flex items-center gap-2">
                          <Badge variant="secondary" className="text-xs">{t('defaultEnabled')}</Badge>
                          <span className="text-sm text-muted-foreground">
                            ({defaultServers.length})
                          </span>
                        </h3>
                        <div className="grid gap-4 md:grid-cols-2">
                          {defaultServers.map((server) => (
                            <MCPServerCard
                              key={server.name}
                              server={server}
                              onDelete={handleDelete}
                              onUpdate={handleAdd}
                              isBuiltIn={BUILTIN_MCP_SERVERS.includes(server.name)}
                              t={t}
                              tc={tc}
                            />
                          ))}
                        </div>
                      </div>
                    )}

                    {optionalServers.length > 0 && (
                      <div>
                        <h3 className="font-medium mb-3 flex items-center gap-2">
                          {t('optionalServers')}
                          <span className="text-sm text-muted-foreground">
                            ({optionalServers.length})
                          </span>
                        </h3>
                        <div className="grid gap-4 md:grid-cols-2">
                          {optionalServers.map((server) => (
                            <MCPServerCard
                              key={server.name}
                              server={server}
                              onDelete={handleDelete}
                              onUpdate={handleAdd}
                              isBuiltIn={BUILTIN_MCP_SERVERS.includes(server.name)}
                              t={t}
                              tc={tc}
                            />
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                );
              })()}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
