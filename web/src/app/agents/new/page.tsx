'use client';

import { useState, useEffect, useRef, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Loader2, FileText, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
import { useCreateAgentPreset } from '@/hooks/use-agents';
import { useExecutors } from '@/hooks/use-executors';
import { skillsApi, toolsApi, mcpApi, modelsApi } from '@/lib/api';
import { AgentBuilderChat } from '@/components/agents/agent-builder-chat';
import { useTranslation } from '@/i18n/client';

export default function NewAgentPage() {
  const router = useRouter();
  const createPreset = useCreateAgentPreset();
  const { t } = useTranslation('agents');
  const { t: tc } = useTranslation('common');

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [selectedTools, setSelectedTools] = useState<string[]>([]);
  const [selectedMcpServers, setSelectedMcpServers] = useState<string[]>([]);
  const [maxTurns, setMaxTurns] = useState(60);
  const [selectedModelProvider, setSelectedModelProvider] = useState<string | null>(null);
  const [selectedModelName, setSelectedModelName] = useState<string | null>(null);
  const [selectedExecutorId, setSelectedExecutorId] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const toolsInitialized = useRef(false);
  const mcpInitialized = useRef(false);
  const skillsInitialized = useRef(false);

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

  // Default: all meta skills selected
  useEffect(() => {
    if (skills.length > 0 && !skillsInitialized.current) {
      skillsInitialized.current = true;
      const metaSkillNames = skills
        .filter((s) => s.skill_type === 'meta')
        .map((s) => s.name);
      setSelectedSkills(metaSkillNames);
    }
  }, [skills]);

  // Default: all built-in tools selected
  useEffect(() => {
    if (tools.length > 0 && !toolsInitialized.current) {
      toolsInitialized.current = true;
      setSelectedTools(tools.map((t) => t.name));
    }
  }, [tools]);

  // Default: fetch and time MCP servers selected
  useEffect(() => {
    if (mcpServers.length > 0 && !mcpInitialized.current) {
      mcpInitialized.current = true;
      const defaults = mcpServers
        .filter((s) => ['time', 'tavily'].includes(s.name))
        .map((s) => s.name);
      setSelectedMcpServers(defaults);
    }
  }, [mcpServers]);

  const validateName = (value: string): string | null => {
    if (!value) return t('create.nameRequired');
    if (value.length < 2) return t('create.nameMinLength');
    if (value.length > 128) return t('create.nameMaxLength');
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const nameError = validateName(name);
    if (nameError) {
      setErrors({ name: nameError });
      return;
    }

    setErrors({});

    try {
      const preset = await createPreset.mutateAsync({
        name,
        description: description || undefined,
        system_prompt: systemPrompt || undefined,
        skill_ids: selectedSkills.length > 0 ? selectedSkills : undefined,
        builtin_tools: selectedTools.length > 0 ? selectedTools : undefined,
        mcp_servers: selectedMcpServers.length > 0 ? selectedMcpServers : undefined,
        max_turns: maxTurns,
        model_provider: selectedModelProvider || undefined,
        model_name: selectedModelName || undefined,
        executor_id: selectedExecutorId || undefined,
      });
      router.push(`/agents/${preset.id}`);
    } catch (error) {
      setErrors({
        submit: error instanceof Error ? error.message : t('create.error'),
      });
    }
  };

  // Model select value helpers
  const modelSelectValue = selectedModelProvider && selectedModelName
    ? `${selectedModelProvider}/${selectedModelName}`
    : '__default__';

  const handleModelSelectChange = (value: string) => {
    if (value === '__default__') {
      setSelectedModelProvider(null);
      setSelectedModelName(null);
    } else {
      const [provider, ...modelParts] = value.split('/');
      setSelectedModelProvider(provider);
      setSelectedModelName(modelParts.join('/'));
    }
  };

  const isProcessing = createPreset.isPending;

  return (
    <div className="container mx-auto py-8 max-w-3xl">
      {/* Header */}
      <div className="mb-6">
        <Link
          href="/agents"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          {t('create.backToAgents')}
        </Link>
        <h1 className="text-3xl font-bold">{t('create.title')}</h1>
        <p className="text-muted-foreground mt-1">
          {t('create.subtitle')}
        </p>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="chat" className="w-full">
        <TabsList className="grid w-full grid-cols-2 mb-6">
          <TabsTrigger value="chat" className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />
            {t('create.tabChat')}
          </TabsTrigger>
          <TabsTrigger value="form" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            {t('create.tabManual')}
          </TabsTrigger>
        </TabsList>

        {/* Chat Mode */}
        <TabsContent value="chat">
          <Card>
            <CardHeader>
              <CardTitle>{t('create.chatTitle')}</CardTitle>
              <CardDescription>
                {t('create.chatDescription')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AgentBuilderChat />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Form Mode */}
        <TabsContent value="form">
          <Card>
            <CardHeader>
              <CardTitle>{t('create.formTitle')}</CardTitle>
              <CardDescription>
                {t('create.formDescription')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Name */}
                <div className="space-y-2">
                  <Label htmlFor="name">
                    {t('create.name')} <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="name"
                    placeholder={t('create.namePlaceholderForm')}
                    value={name}
                    onChange={(e) => {
                      setName(e.target.value);
                      setErrors((prev) => ({ ...prev, name: '' }));
                    }}
                    className={errors.name ? 'border-destructive' : ''}
                    disabled={isProcessing}
                  />
                  {errors.name && (
                    <p className="text-xs text-destructive">{errors.name}</p>
                  )}
                </div>

                {/* Description */}
                <div className="space-y-2">
                  <Label htmlFor="description">{t('create.description')}</Label>
                  <Textarea
                    id="description"
                    placeholder={t('create.descriptionPlaceholderForm')}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={2}
                    disabled={isProcessing}
                  />
                </div>

                {/* System Prompt */}
                <div className="space-y-2">
                  <Label htmlFor="system-prompt">{t('create.systemPromptLabel')}</Label>
                  <Textarea
                    id="system-prompt"
                    placeholder={t('create.systemPromptPlaceholderForm')}
                    value={systemPrompt}
                    onChange={(e) => setSystemPrompt(e.target.value)}
                    rows={4}
                    disabled={isProcessing}
                  />
                  <p className="text-xs text-muted-foreground">
                    {t('create.systemPromptHelp')}
                  </p>
                </div>

                {/* Skills */}
                <div className="space-y-2">
                  <Label>{t('create.skills')}</Label>
                  <MultiSelect
                    options={[]}
                    groups={skillGroups}
                    selected={selectedSkills}
                    onChange={setSelectedSkills}
                    placeholder={t('create.skillsPlaceholder')}
                    emptyText={t('create.skillsEmpty')}
                    disabled={isProcessing}
                    searchable
                    searchPlaceholder={t('create.skillsFilterPlaceholder')}
                  />
                </div>

                {/* Built-in Tools */}
                <div className="space-y-2">
                  <Label>{t('create.tools')}</Label>
                  <MultiSelect
                    options={tools.map((tool) => ({
                      value: tool.name,
                      label: tool.name,
                      description: tool.description?.slice(0, 50),
                    }))}
                    selected={selectedTools}
                    onChange={setSelectedTools}
                    placeholder={t('create.toolsPlaceholder')}
                    emptyText={t('create.toolsEmpty')}
                    disabled={isProcessing}
                  />
                </div>

                {/* MCP Servers */}
                <div className="space-y-2">
                  <Label>{t('create.mcpServers')}</Label>
                  <MultiSelect
                    options={mcpServers.map((server) => ({
                      value: server.name,
                      label: server.display_name,
                      description: server.description?.slice(0, 50),
                    }))}
                    selected={selectedMcpServers}
                    onChange={setSelectedMcpServers}
                    placeholder={t('create.mcpPlaceholder')}
                    emptyText={t('create.mcpEmpty')}
                    disabled={isProcessing}
                  />
                </div>

                {/* Max Turns */}
                <div className="space-y-2">
                  <Label htmlFor="max-turns">{t('create.maxTurns')}</Label>
                  <Input
                    id="max-turns"
                    type="number"
                    min={1}
                    max={60000}
                    value={maxTurns}
                    onChange={(e) => setMaxTurns(parseInt(e.target.value) || 60)}
                    className="w-24"
                    disabled={isProcessing}
                  />
                  <p className="text-xs text-muted-foreground">
                    {t('create.maxTurnsHelp')}
                  </p>
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
                        <SelectValue placeholder={t('create.modelDefault')} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__default__">{t('create.modelDefault')}</SelectItem>
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
                      {t('create.modelHelp')}
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
                <div className="flex gap-4">
                  <Button type="submit" disabled={isProcessing}>
                    {isProcessing ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        {t('create.creating')}
                      </>
                    ) : (
                      t('create.createButton')
                    )}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => router.back()}
                    disabled={isProcessing}
                  >
                    {tc('actions.cancel')}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
