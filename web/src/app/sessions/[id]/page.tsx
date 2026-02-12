'use client';

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { MessageSquare, ArrowLeft, Trash2, Clock } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';
import { ErrorBanner } from '@/components/ui/error-banner';
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
import { usePublishedSessionDetail, useDeletePublishedSession } from '@/hooks/use-published-sessions';
import { useQuery } from '@tanstack/react-query';
import { agentPresetsApi } from '@/lib/api';
import { ChatMessageItem } from '@/components/chat/chat-message';
import type { ChatMessage } from '@/stores/chat-store';
import type { StreamEventRecord } from '@/types/stream-events';
import { useTranslation } from '@/i18n/client';
import { formatDateTime } from '@/lib/formatters';

// ---------- convert raw session messages → ChatMessage[] with streamEvents ----------

interface RawMessage {
  role: string;
  content: string | Array<Record<string, unknown>>;
}

function sessionMessagesToChatMessages(raw: RawMessage[]): ChatMessage[] {
  const result: ChatMessage[] = [];
  let events: StreamEventRecord[] = [];
  let pendingAssistantId: string | null = null;
  let toolIdToName: Record<string, string> = {};
  let eventCounter = 0;

  const nextId = () => `evt-${eventCounter++}`;
  const now = Date.now();

  const flushAssistant = () => {
    if (pendingAssistantId !== null) {
      result.push({
        id: pendingAssistantId,
        role: 'assistant',
        content: '',
        timestamp: now,
        streamEvents: events.length > 0 ? [...events] : undefined,
      });
      events = [];
      toolIdToName = {};
      pendingAssistantId = null;
    }
  };

  for (let i = 0; i < raw.length; i++) {
    const msg = raw[i];

    if (msg.role === 'user') {
      // Check if this is a tool_result message (sent back by the system)
      if (Array.isArray(msg.content)) {
        const hasToolResult = msg.content.some(
          (b) => typeof b === 'object' && b !== null && b.type === 'tool_result'
        );
        if (hasToolResult) {
          for (const block of msg.content) {
            if (typeof block === 'object' && block !== null && block.type === 'tool_result') {
              const toolUseId = typeof block.tool_use_id === 'string' ? block.tool_use_id : '';
              const toolName = toolIdToName[toolUseId] || 'tool';
              const resultContent = typeof block.content === 'string'
                ? block.content
                : JSON.stringify(block.content);
              events.push({
                id: nextId(),
                timestamp: now,
                type: 'tool_result',
                data: {
                  toolName,
                  toolResult: resultContent,
                  success: !block.is_error,
                },
              });
            }
          }
          continue;
        }
      }

      // Regular user message — flush any pending assistant first
      flushAssistant();

      let userText = '';
      if (typeof msg.content === 'string') {
        userText = msg.content;
      } else if (Array.isArray(msg.content)) {
        const texts: string[] = [];
        for (const block of msg.content) {
          if (typeof block === 'object' && block !== null && block.type === 'text' && typeof block.text === 'string') {
            texts.push(block.text);
          }
        }
        userText = texts.join('\n');
      }

      result.push({
        id: `msg-${i}`,
        role: 'user',
        content: userText,
        timestamp: now,
      });
      continue;
    }

    if (msg.role === 'assistant') {
      flushAssistant();
      pendingAssistantId = `msg-${i}`;

      if (typeof msg.content === 'string') {
        if (msg.content) {
          events.push({
            id: nextId(),
            timestamp: now,
            type: 'assistant',
            data: { content: msg.content },
          });
        }
      } else if (Array.isArray(msg.content)) {
        for (const block of msg.content) {
          if (typeof block !== 'object' || block === null) continue;

          if (block.type === 'text' && typeof block.text === 'string') {
            if (block.text) {
              events.push({
                id: nextId(),
                timestamp: now,
                type: 'assistant',
                data: { content: block.text },
              });
            }
          } else if (block.type === 'tool_use') {
            const toolName = typeof block.name === 'string' ? block.name : 'tool';
            const toolId = typeof block.id === 'string' ? block.id : '';
            if (toolId) toolIdToName[toolId] = toolName;

            events.push({
              id: nextId(),
              timestamp: now,
              type: 'tool_call',
              data: {
                toolName,
                toolInput: (typeof block.input === 'object' && block.input !== null)
                  ? block.input as Record<string, unknown>
                  : undefined,
              },
            });
          }
        }
      }
      continue;
    }
  }

  flushAssistant();
  return result;
}

// ---------- main page ----------
export default function SessionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.id as string;
  const { t } = useTranslation('sessions');
  const { t: tc } = useTranslation('common');

  const { data: session, isLoading, error } = usePublishedSessionDetail(sessionId);
  const deleteMutation = useDeletePublishedSession();

  const { data: agent } = useQuery({
    queryKey: ['agent', session?.agent_id],
    queryFn: () => agentPresetsApi.get(session!.agent_id),
    enabled: !!session?.agent_id,
  });

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(sessionId);
      toast.success(t('delete.success'));
      router.push('/sessions');
    } catch {
      toast.error(t('delete.error'));
    }
  };

  const chatMessages = React.useMemo(
    () => sessionMessagesToChatMessages((session?.messages || []) as RawMessage[]),
    [session?.messages]
  );

  return (
    <div className="flex flex-col min-h-screen">
      <main className="flex-1 container px-4 py-8 pb-24 max-w-4xl mx-auto">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 mb-6 text-sm text-muted-foreground">
          <Link href="/sessions" className="flex items-center gap-1 hover:text-foreground transition-colors">
            <ArrowLeft className="h-4 w-4" />
            {t('title')}
          </Link>
          <span>/</span>
          <span className="truncate max-w-[200px]">{sessionId}</span>
        </div>

        {error && (
          <ErrorBanner title={tc('errors.generic')} message={(error as Error).message} className="mb-6" />
        )}

        {isLoading && <LoadingSkeleton variant="detail" />}

        {session && (
          <>
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
              <div>
                <h1 className="text-2xl font-bold flex items-center gap-2">
                  <MessageSquare className="h-6 w-6" />
                  {t('detail.title')}
                </h1>
                <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-muted-foreground">
                  {agent && <Badge variant="outline">{agent.name}</Badge>}
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatDateTime(session.created_at)}
                  </span>
                  <span>{t('card.messageCount', { count: (session.messages || []).length })}</span>
                </div>
              </div>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Trash2 className="h-4 w-4 mr-1" />
                    {tc('actions.delete')}
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>{t('delete.title')}</AlertDialogTitle>
                    <AlertDialogDescription>{t('delete.confirm')}</AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>{tc('actions.cancel')}</AlertDialogCancel>
                    <AlertDialogAction onClick={handleDelete}>
                      {tc('actions.delete')}
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>

            {/* Messages — reuse ChatMessageItem from chat panel */}
            <div className="space-y-3">
              {chatMessages.length === 0 ? (
                <p className="text-center text-muted-foreground py-12">{t('detail.noMessages')}</p>
              ) : (
                chatMessages.map((msg) => (
                  <ChatMessageItem
                    key={msg.id}
                    message={msg}
                    hideTraceLink
                  />
                ))
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
