'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Loader2, Save, Trash2, MessageSquare, Bot, Globe, Copy, Check, ExternalLink, AlertCircle, ChevronDown } from 'lucide-react';
import { useTranslation } from '@/i18n/client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MultiSelect, MultiSelectOptionGroup } from '@/components/ui/multi-select';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
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
} from '@/components/ui/alert-dialog';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { useAgentPreset, useUpdateAgentPreset, useDeleteAgentPreset, usePublishAgent, useUnpublishAgent } from '@/hooks/use-agents';
import { useExecutors } from '@/hooks/use-executors';
import { skillsApi, toolsApi, mcpApi, modelsApi } from '@/lib/api';
import { useChatStore } from '@/stores/chat-store';
import { useChatPanel } from '@/components/chat/chat-provider';

export default function AgentDetailPage() {
  const router = useRouter();
  const params = useParams();
  const presetId = params.id as string;

  const { data: preset, isLoading, error } = useAgentPreset(presetId);
  const updatePreset = useUpdateAgentPreset(presetId);
  const deletePreset = useDeleteAgentPreset();
  const publishAgent = usePublishAgent(presetId);
  const unpublishAgent = useUnpublishAgent(presetId);
  const { t } = useTranslation('agents');
  const { t: tc } = useTranslation('common');
  const [copiedUrl, setCopiedUrl] = useState<string | null>(null);
  const [showApiUsage, setShowApiUsage] = useState(false);
  const [showPublishDialog, setShowPublishDialog] = useState(false);
  const [publishModelProvider, setPublishModelProvider] = useState<string | null>(null);
  const [publishModelName, setPublishModelName] = useState<string | null>(null);
  const [publishResponseMode, setPublishResponseMode] = useState<'streaming' | 'non_streaming'>('streaming');
  const [isPublishing, setIsPublishing] = useState(false);
  const [showClearConversationDialog, setShowClearConversationDialog] = useState(false);

  // Chat store for applying preset
  const {
    messages,
    setSelectedSkills,
    setSelectedTools,
    setSelectedMcpServers,
    setMaxTurns,
    setSelectedAgentPreset,
    setSelectedModel,
    setSelectedExecutorId: setChatExecutorId,
    clearMessages,
    clearUploadedFiles,
  } = useChatStore();

  // Chat panel for opening it
  const chatPanel = useChatPanel();

  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [selectedSkills, setSelectedSkillsState] = useState<string[]>([]);
  const [selectedTools, setSelectedToolsState] = useState<string[]>([]);
  const [selectedMcpServers, setSelectedMcpServersState] = useState<string[]>([]);
  const [maxTurns, setMaxTurnsState] = useState(60);
  const [selectedModelProvider, setSelectedModelProvider] = useState<string | null>(null);
  const [selectedModelName, setSelectedModelNameState] = useState<string | null>(null);
  const [selectedExecutorId, setSelectedExecutorId] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [hasChanges, setHasChanges] = useState(false);

  // Fetch available options
  const { data: skillsData } = useQuery({
    queryKey: ['registry-skills-list'],
    queryFn: () => skillsApi.list(),
  });

  const { data: toolsData } = useQuery({
    queryKey: ['tools-list'],
    queryFn: () => toolsApi.list(),
  });

  const { data: mcpData } = useQuery({
    queryKey: ['mcp-servers'],
    queryFn: () => mcpApi.listServers(),
  });

  const { data: modelsData } = useQuery({
    queryKey: ['models-providers'],
    queryFn: () => modelsApi.listProviders(),
  });

  const { data: executorsData } = useExecutors();

  const skills = skillsData?.skills || [];
  const executors = executorsData?.executors || [];
  const tools = toolsData?.tools || [];
  const mcpServers = mcpData?.servers || [];
  const modelProviders = modelsData?.providers || [];

  // Organize skills into groups: meta skills first, then user skills
  const skillGroups: MultiSelectOptionGroup[] = useMemo(() => {
    const metaSkills = skills.filter((s) => s.skill_type === 'meta');
    const userSkills = skills.filter((s) => s.skill_type !== 'meta');

    const groups: MultiSelectOptionGroup[] = [];

    if (metaSkills.length > 0) {
      groups.push({
        label: t('create.skillGroups.meta'),
        options: metaSkills.map((skill) => ({
          value: skill.name,
          label: skill.name,
          description: skill.description?.slice(0, 50),
        })),
      });
    }

    if (userSkills.length > 0) {
      const sorted = [...userSkills].sort((a, b) => a.name.localeCompare(b.name));
      groups.push({
        label: t('create.skillGroups.user'),
        options: sorted.map((skill) => ({
          value: skill.name,
          label: skill.name,
          description: skill.description?.slice(0, 50),
        })),
      });
    }

    return groups;
  }, [skills, t]);

  // Initialize form with preset data
  useEffect(() => {
    if (preset) {
      setName(preset.name);
      setDescription(preset.description || '');
      setSystemPrompt(preset.system_prompt || '');
      setSelectedSkillsState(preset.skill_ids || []);
      // null means all tools enabled - select all available tools
      if (preset.builtin_tools === null && tools.length > 0) {
        setSelectedToolsState(tools.map(t => t.name));
      } else {
        setSelectedToolsState(preset.builtin_tools || []);
      }
      setSelectedMcpServersState(preset.mcp_servers || []);
      setMaxTurnsState(preset.max_turns);
      setSelectedModelProvider(preset.model_provider || null);
      setSelectedModelNameState(preset.model_name || null);
      setSelectedExecutorId(preset.executor_id || null);
      setHasChanges(false);
    }
  }, [preset]); // eslint-disable-line react-hooks/exhaustive-deps -- tools only needed for initial null->all expansion

  const handleFieldChange = <T,>(setter: React.Dispatch<React.SetStateAction<T>>, value: T) => {
    setter(value);
    setHasChanges(true);
  };

  const handleSave = async () => {
    if (!preset) return;

    setErrors({});

    // null = all tools enabled, [] = no tools, specific array = only those tools
    const allToolsSelected = tools.length > 0 && selectedTools.length === tools.length;
    const builtinToolsToSave = allToolsSelected ? null : selectedTools;

    try {
      await updatePreset.mutateAsync({
        name,
        description: description || undefined,
        system_prompt: systemPrompt || undefined,
        skill_ids: selectedSkills.length > 0 ? selectedSkills : [],
        builtin_tools: builtinToolsToSave,
        mcp_servers: selectedMcpServers.length > 0 ? selectedMcpServers : [],
        max_turns: maxTurns,
        // Always explicitly send model/executor so clearing to "Default"/"Local" works
        // (null in JSON triggers model_fields_set detection in backend)
        model_provider: selectedModelProvider ?? null,
        model_name: selectedModelName ?? null,
        executor_id: selectedExecutorId ?? null,
      });
      setHasChanges(false);
    } catch (error) {
      setErrors({
        submit: error instanceof Error ? error.message : t('edit.error'),
      });
    }
  };

  const handleDelete = async () => {
    if (!preset || preset.is_system) return;

    try {
      await deletePreset.mutateAsync(presetId);
      router.push('/agents');
    } catch (error) {
      setErrors({
        submit: error instanceof Error ? error.message : t('delete.error'),
      });
    }
  };

  const applyPresetToChat = () => {
    if (!preset) return;

    setSelectedSkills(preset.skill_ids || []);
    setMaxTurns(preset.max_turns);

    // null means all tools enabled
    if (preset.builtin_tools === null && tools.length > 0) {
      setSelectedTools(tools.map(t => t.name));
    } else if (preset.builtin_tools && preset.builtin_tools.length > 0) {
      setSelectedTools(preset.builtin_tools);
    } else {
      setSelectedTools([]);
    }
    setSelectedMcpServers(preset.mcp_servers || []);

    // Apply model selection from preset
    setSelectedModel(preset.model_provider || null, preset.model_name || null);

    // Apply executor from preset
    setChatExecutorId(preset.executor_id || null);

    setSelectedAgentPreset(preset.id);
    chatPanel.open(preset.skill_ids || []);
  };

  const handleApplyToChat = () => {
    if (!preset) return;

    if (messages.length > 0) {
      setShowClearConversationDialog(true);
    } else {
      applyPresetToChat();
    }
  };

  const handleConfirmClearAndApply = () => {
    clearMessages();
    clearUploadedFiles();
    applyPresetToChat();
    setShowClearConversationDialog(false);
  };

  // Open publish dialog with current model settings
  const handleOpenPublishDialog = () => {
    if (!preset) return;
    // Initialize with current preset values
    setPublishModelProvider(preset.model_provider || null);
    setPublishModelName(preset.model_name || null);
    setShowPublishDialog(true);
  };

  // Handle publish with selected model
  const handlePublishWithModel = async () => {
    if (!preset) return;
    setIsPublishing(true);

    try {
      // First update the model if changed
      const modelChanged =
        publishModelProvider !== preset.model_provider ||
        publishModelName !== preset.model_name;

      if (modelChanged) {
        await updatePreset.mutateAsync({
          model_provider: publishModelProvider ?? null,
          model_name: publishModelName ?? null,
        });
      }

      // Then publish with response mode
      await publishAgent.mutateAsync({ api_response_mode: publishResponseMode });
      setShowPublishDialog(false);
    } catch (error) {
      setErrors({
        submit: error instanceof Error ? error.message : t('publish.error'),
      });
    } finally {
      setIsPublishing(false);
    }
  };

  // Model select value helpers
  const modelSelectValue = selectedModelProvider && selectedModelName
    ? `${selectedModelProvider}/${selectedModelName}`
    : '__default__';

  const handleModelSelectChange = (value: string) => {
    if (value === '__default__') {
      setSelectedModelProvider(null);
      setSelectedModelNameState(null);
    } else {
      const [provider, ...modelParts] = value.split('/');
      setSelectedModelProvider(provider);
      setSelectedModelNameState(modelParts.join('/'));
    }
    setHasChanges(true);
  };

  const publishModelSelectValue = publishModelProvider && publishModelName
    ? `${publishModelProvider}/${publishModelName}`
    : '__default__';

  const handlePublishModelSelectChange = (value: string) => {
    if (value === '__default__') {
      setPublishModelProvider(null);
      setPublishModelName(null);
    } else {
      const [provider, ...modelParts] = value.split('/');
      setPublishModelProvider(provider);
      setPublishModelName(modelParts.join('/'));
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 max-w-2xl">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (error || !preset) {
    return (
      <div className="container mx-auto py-8 max-w-2xl">
        <div className="mb-6">
          <Link
            href="/agents"
            className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-4"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            {t('detail.backToAgents')}
          </Link>
        </div>
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
          <p className="font-medium">{t('detail.loadError')}</p>
          <p className="text-sm mt-1">{(error as Error)?.message || t('detail.notFound')}</p>
        </div>
      </div>
    );
  }

  const isProcessing = updatePreset.isPending || deletePreset.isPending;

  return (
    <div className="container mx-auto py-8 max-w-2xl">
      {/* Header */}
      <div className="mb-6">
        <Link
          href="/agents"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          {t('detail.backToAgents')}
        </Link>
        <div className="flex items-center gap-3">
          <Bot className="h-8 w-8 text-primary" />
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-3xl font-bold">{preset.name}</h1>
              {preset.is_system && <Badge variant="secondary">{t('type.system')}</Badge>}
            </div>
            {preset.description && (
              <p className="text-muted-foreground mt-1">{preset.description}</p>
            )}
          </div>
        </div>
      </div>

      {/* Apply to Chat Button */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold">{t('detail.testTitle')}</h3>
              <p className="text-sm text-muted-foreground">
                {t('detail.testDescription')}
              </p>
            </div>
            <Button onClick={handleApplyToChat}>
              <MessageSquare className="mr-2 h-4 w-4" />
              {t('applyToChat')}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Publish Card */}
      {!preset.is_system && (
        <Card className="mb-6">
          <CardContent className="pt-6">
            {preset.is_published ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Globe className="h-5 w-5 text-green-600" />
                    <div>
                      <h3 className="font-semibold">{t('detail.publishedTitle')}</h3>
                      <p className="text-sm text-muted-foreground">
                        {t('detail.publishedDescription')}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    onClick={() => unpublishAgent.mutate()}
                    disabled={unpublishAgent.isPending}
                  >
                    {unpublishAgent.isPending ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : null}
                    {t('unpublish.title')}
                  </Button>
                </div>
                <div className="space-y-2 text-sm">
                  {/* Mode Badge */}
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground shrink-0">{t('publish.responseMode.current')}:</span>
                    <Badge variant={preset.api_response_mode === 'streaming' ? 'info' : 'secondary'}>
                      {preset.api_response_mode === 'streaming' ? t('publish.responseMode.streaming') : t('publish.responseMode.nonStreaming')}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground shrink-0">{t('detail.webPage')}:</span>
                    <code className="bg-muted px-2 py-1 rounded text-xs flex-1 truncate">
                      {typeof window !== 'undefined' ? `${window.location.origin}/published/${preset.id}` : `/published/${preset.id}`}
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0"
                      onClick={() => {
                        const url = `${window.location.origin}/published/${preset.id}`;
                        navigator.clipboard.writeText(url);
                        setCopiedUrl('web');
                        setTimeout(() => setCopiedUrl(null), 2000);
                      }}
                    >
                      {copiedUrl === 'web' ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
                    </Button>
                    <a
                      href={`/published/${preset.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                        <ExternalLink className="h-3.5 w-3.5" />
                      </Button>
                    </a>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground shrink-0">{t('detail.apiLabel')}:</span>
                    <code className="bg-muted px-2 py-1 rounded text-xs flex-1 truncate">
                      {typeof window !== 'undefined'
                        ? `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:62610'}/api/v1/published/${preset.id}/${preset.api_response_mode === 'streaming' ? 'chat' : 'chat/sync'}`
                        : `/api/v1/published/${preset.id}/${preset.api_response_mode === 'streaming' ? 'chat' : 'chat/sync'}`}
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0"
                      onClick={() => {
                        const endpoint = preset.api_response_mode === 'streaming' ? 'chat' : 'chat/sync';
                        const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:62610'}/api/v1/published/${preset.id}/${endpoint}`;
                        navigator.clipboard.writeText(url);
                        setCopiedUrl('api');
                        setTimeout(() => setCopiedUrl(null), 2000);
                      }}
                    >
                      {copiedUrl === 'api' ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
                    </Button>
                  </div>
                  {/* API Usage */}
                  <div className="pt-1">
                    <button
                      onClick={() => setShowApiUsage(!showApiUsage)}
                      className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <ChevronDown className={`h-4 w-4 transition-transform ${showApiUsage ? 'rotate-180' : ''}`} />
                      <span className="text-xs font-medium">{t('publish.apiUsage.title')}</span>
                    </button>
                    {showApiUsage && (
                      <div className="mt-2 space-y-3">
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-muted-foreground">{t('publish.apiUsage.exampleRequest')}</span>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 px-2 text-xs"
                              onClick={() => {
                                const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:62610';
                                const isStreaming = preset.api_response_mode === 'streaming';
                                const endpoint = isStreaming ? 'chat' : 'chat/sync';
                                const curl = isStreaming
                                  ? `curl -N -X POST ${apiBase}/api/v1/published/${preset.id}/${endpoint} \\\n  -H "Content-Type: application/json" \\\n  -d '{"request": "Hello", "session_id": "your-session-id"}'`
                                  : `curl -X POST ${apiBase}/api/v1/published/${preset.id}/${endpoint} \\\n  -H "Content-Type: application/json" \\\n  -d '{"request": "Hello", "session_id": "your-session-id"}'`;
                                navigator.clipboard.writeText(curl);
                                setCopiedUrl('curl');
                                setTimeout(() => setCopiedUrl(null), 2000);
                              }}
                            >
                              {copiedUrl === 'curl' ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
                            </Button>
                          </div>
                          <pre className="bg-muted rounded p-3 text-xs overflow-x-auto whitespace-pre">
{preset.api_response_mode === 'streaming'
  ? `curl -N -X POST ${typeof window !== 'undefined' ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:62610') : 'http://localhost:62610'}/api/v1/published/${preset.id}/chat \\
  -H "Content-Type: application/json" \\
  -d '{"request": "Hello", "session_id": "your-session-id"}'`
  : `curl -X POST ${typeof window !== 'undefined' ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:62610') : 'http://localhost:62610'}/api/v1/published/${preset.id}/chat/sync \\
  -H "Content-Type: application/json" \\
  -d '{"request": "Hello", "session_id": "your-session-id"}'`}
                          </pre>
                          <p className="text-xs text-muted-foreground mt-1">
                            {preset.api_response_mode === 'streaming'
                              ? t('publish.apiUsage.streamingNote')
                              : t('publish.apiUsage.nonStreamingNote')}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {t('publish.apiUsage.sessionIdNote')}
                          </p>
                        </div>
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-muted-foreground">{t('publish.apiUsage.sessionHistory')}</span>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 px-2 text-xs"
                              onClick={() => {
                                const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:62610';
                                const curl = `curl ${apiBase}/api/v1/published/${preset.id}/sessions/your-session-id`;
                                navigator.clipboard.writeText(curl);
                                setCopiedUrl('session');
                                setTimeout(() => setCopiedUrl(null), 2000);
                              }}
                            >
                              {copiedUrl === 'session' ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
                            </Button>
                          </div>
                          <pre className="bg-muted rounded p-3 text-xs overflow-x-auto whitespace-pre">
{`curl ${typeof window !== 'undefined' ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:62610') : 'http://localhost:62610'}/api/v1/published/${preset.id}/sessions/your-session-id`}
                          </pre>
                        </div>
                        <div className="flex items-center gap-1 pt-1">
                          <ExternalLink className="h-3 w-3 text-muted-foreground" />
                          <a
                            href={`${process.env.NEXT_PUBLIC_DOCS_URL || 'http://localhost:62630'}/how-to/publish-agent`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-primary hover:underline"
                          >
                            {t('publish.apiUsage.docsLink')}
                          </a>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">{t('publish.title')}</h3>
                  <p className="text-sm text-muted-foreground">
                    {t('detail.publishDescription')}
                  </p>
                </div>
                <Button onClick={handleOpenPublishDialog}>
                  <Globe className="mr-2 h-4 w-4" />
                  {t('publish.title')}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Configuration Form */}
      <Card>
        <CardHeader>
          <CardTitle>{t('detail.configuration')}</CardTitle>
          <CardDescription>
            {t('detail.configDescription')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Name */}
            <div className="space-y-2">
              <Label htmlFor="name">{t('detail.name')}</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => handleFieldChange(setName, e.target.value)}
                disabled={isProcessing}
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">{t('detail.description')}</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => handleFieldChange(setDescription, e.target.value)}
                rows={2}
                disabled={isProcessing}
              />
            </div>

            {/* System Prompt */}
            <div className="space-y-2">
              <Label htmlFor="system-prompt">{t('create.systemPromptLabel')}</Label>
              <Textarea
                id="system-prompt"
                placeholder={t('detail.systemPromptPlaceholder')}
                value={systemPrompt}
                onChange={(e) => handleFieldChange(setSystemPrompt, e.target.value)}
                rows={4}
                disabled={isProcessing}
              />
              <p className="text-xs text-muted-foreground">
                {t('detail.systemPromptHelp')}
              </p>
            </div>

            {/* Skills */}
            <div className="space-y-2">
              <Label>{t('detail.skills')}</Label>
              <MultiSelect
                options={[]}
                groups={skillGroups}
                selected={selectedSkills}
                onChange={(value) => handleFieldChange(setSelectedSkillsState, value)}
                placeholder={t('create.skillsPlaceholder')}
                emptyText={t('create.skillsEmpty')}
                disabled={isProcessing}
                searchable
                searchPlaceholder={t('create.skillsFilterPlaceholder')}
              />
            </div>

            {/* Built-in Tools */}
            <div className="space-y-2">
              <Label>{t('detail.tools')}</Label>
              <MultiSelect
                options={tools.map((tool) => ({
                  value: tool.name,
                  label: tool.name,
                  description: tool.description?.slice(0, 50),
                }))}
                selected={selectedTools}
                onChange={(value) => handleFieldChange(setSelectedToolsState, value)}
                placeholder={t('create.toolsPlaceholder')}
                emptyText={t('create.toolsEmpty')}
                disabled={isProcessing}
              />
            </div>

            {/* MCP Servers */}
            <div className="space-y-2">
              <Label>{t('detail.mcpServers')}</Label>
              <MultiSelect
                options={mcpServers.map((server) => ({
                  value: server.name,
                  label: server.display_name,
                  description: server.description?.slice(0, 50),
                }))}
                selected={selectedMcpServers}
                onChange={(value) => handleFieldChange(setSelectedMcpServersState, value)}
                placeholder={t('create.mcpPlaceholder')}
                emptyText={t('create.mcpEmpty')}
                disabled={isProcessing}
              />
            </div>

            {/* Max Turns */}
            <div className="space-y-2">
              <Label htmlFor="max-turns">{t('detail.maxTurns')}</Label>
              <Input
                id="max-turns"
                type="number"
                min={1}
                max={60000}
                value={maxTurns}
                onChange={(e) => handleFieldChange(setMaxTurnsState, parseInt(e.target.value) || 60)}
                className="w-24"
                disabled={isProcessing}
              />
            </div>

            {/* Model Selection */}
            {modelProviders.length > 0 && (
              <div className="space-y-2">
                <Label>{t('create.modelLabel')}</Label>
                <Select
                  value={modelSelectValue}
                  onValueChange={handleModelSelectChange}
                  disabled={isProcessing}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={t('detail.modelDefault')} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__default__">{t('detail.modelDefault')}</SelectItem>
                    {modelProviders.map((provider) => (
                      <SelectGroup key={provider.name}>
                        <SelectLabel>{provider.name.charAt(0).toUpperCase() + provider.name.slice(1)}</SelectLabel>
                        {provider.models.map((model) => (
                          <SelectItem key={model.key} value={model.key}>
                            {model.display_name}
                          </SelectItem>
                        ))}
                      </SelectGroup>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  {t('detail.modelHelp')}
                </p>
              </div>
            )}

            {/* Executor Selection */}
            {executors.length > 0 && (
              <div className="space-y-2">
                <Label>{t('create.executorLabel')}</Label>
                <Select
                  value={selectedExecutorId || '__local__'}
                  onValueChange={(value) => {
                    setSelectedExecutorId(value === '__local__' ? null : value);
                    setHasChanges(true);
                  }}
                  disabled={isProcessing}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={t('create.executorLocal')} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__local__">{t('create.executorLocal')}</SelectItem>
                    {executors.map((executor) => (
                      <SelectItem
                        key={executor.id}
                        value={executor.id}
                        disabled={executor.status !== 'online'}
                      >
                        {executor.name}
                        {executor.status !== 'online' && ` (${executor.status})`}
                        {executor.gpu_required && ' [GPU]'}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  {t('create.executorHelp')}
                </p>
              </div>
            )}

            {/* Submit Error */}
            {errors.submit && (
              <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
                <p className="text-sm">{errors.submit}</p>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-4 pt-4 border-t">
              <Button
                onClick={handleSave}
                disabled={isProcessing || !hasChanges}
              >
                {updatePreset.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {t('edit.saving')}
                  </>
                ) : (
                  <>
                    <Save className="mr-2 h-4 w-4" />
                    {t('detail.saveChanges')}
                  </>
                )}
              </Button>
              {!preset.is_system && (
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button
                      variant="destructive"
                      disabled={isProcessing}
                    >
                      {deletePreset.isPending ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          {t('delete.deleting')}
                        </>
                      ) : (
                        <>
                          <Trash2 className="mr-2 h-4 w-4" />
                          {tc('actions.delete')}
                        </>
                      )}
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>{t('delete.title')}</AlertDialogTitle>
                      <AlertDialogDescription>
                        {t('delete.confirm', { name: preset.name })} {t('delete.description')}
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>{tc('actions.cancel')}</AlertDialogCancel>
                      <AlertDialogAction
                        onClick={handleDelete}
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
        </CardContent>
      </Card>

      {/* Metadata */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">{t('detail.metadataTitle')}</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <div className="flex justify-between">
            <span>ID:</span>
            <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{preset.id}</code>
          </div>
          <div className="flex justify-between">
            <span>{t('model.title')}:</span>
            <span>
              {preset.model_provider && preset.model_name
                ? `${preset.model_provider}/${preset.model_name}`
                : t('detail.modelDefault')}
            </span>
          </div>
          <div className="flex justify-between">
            <span>{t('overview.createdAt')}:</span>
            <span>{new Date(preset.created_at).toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span>{t('overview.updatedAt')}:</span>
            <span>{new Date(preset.updated_at).toLocaleString()}</span>
          </div>
        </CardContent>
      </Card>

      {/* Clear Conversation AlertDialog */}
      <AlertDialog open={showClearConversationDialog} onOpenChange={setShowClearConversationDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t('detail.clearConversationTitle')}</AlertDialogTitle>
            <AlertDialogDescription>
              {t('detail.clearConversationConfirm')}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{tc('actions.cancel')}</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmClearAndApply}>
              {tc('actions.confirm')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Publish Dialog */}
      <Dialog open={showPublishDialog} onOpenChange={setShowPublishDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('publish.title')}</DialogTitle>
            <DialogDescription>
              {t('publish.dialogDescription')}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Model Selection */}
            {modelProviders.length > 0 && (
              <div className="space-y-2">
                <Label>{t('create.modelLabel')}</Label>
                <Select
                  value={publishModelSelectValue}
                  onValueChange={handlePublishModelSelectChange}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={t('detail.modelDefault')} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__default__">{t('detail.modelDefault')}</SelectItem>
                    {modelProviders.map((provider) => (
                      <SelectGroup key={provider.name}>
                        <SelectLabel>{provider.name.charAt(0).toUpperCase() + provider.name.slice(1)}</SelectLabel>
                        {provider.models.map((model) => (
                          <SelectItem key={model.key} value={model.key}>
                            {model.display_name}
                          </SelectItem>
                        ))}
                      </SelectGroup>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  {t('publish.modelHelp')}
                </p>
              </div>
            )}

            {/* Info if no model selected */}
            {!publishModelProvider && !publishModelName && (
              <div className="flex items-start gap-2 p-3 rounded-md bg-muted text-sm">
                <AlertCircle className="h-4 w-4 mt-0.5 shrink-0 text-muted-foreground" />
                <span className="text-muted-foreground">
                  {t('publish.noModelWarning')}
                </span>
              </div>
            )}

            {/* API Response Mode Selection */}
            <div className="space-y-3">
              <Label>{t('publish.responseMode.title')}</Label>
              <RadioGroup
                value={publishResponseMode}
                onValueChange={(v) => setPublishResponseMode(v as 'streaming' | 'non_streaming')}
                className="space-y-2"
              >
                <div className="flex items-start space-x-3 p-3 rounded-md border hover:bg-muted/50 cursor-pointer">
                  <RadioGroupItem value="streaming" id="streaming" className="mt-1" />
                  <div className="flex-1">
                    <Label htmlFor="streaming" className="font-medium cursor-pointer">
                      {t('publish.responseMode.streaming')}
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      {t('publish.responseMode.streamingDescription')}
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3 p-3 rounded-md border hover:bg-muted/50 cursor-pointer">
                  <RadioGroupItem value="non_streaming" id="non_streaming" className="mt-1" />
                  <div className="flex-1">
                    <Label htmlFor="non_streaming" className="font-medium cursor-pointer">
                      {t('publish.responseMode.nonStreaming')}
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      {t('publish.responseMode.nonStreamingDescription')}
                    </p>
                  </div>
                </div>
              </RadioGroup>
              <p className="text-xs text-muted-foreground">
                {t('publish.responseMode.immutableNote')}
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowPublishDialog(false)}
              disabled={isPublishing}
            >
              {tc('actions.cancel')}
            </Button>
            <Button
              onClick={handlePublishWithModel}
              disabled={isPublishing}
            >
              {isPublishing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t('publish.publishing')}
                </>
              ) : (
                <>
                  <Globe className="mr-2 h-4 w-4" />
                  {t('publish.title')}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
