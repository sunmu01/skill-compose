"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Spinner } from "@/components/ui/spinner";
import { ExternalLink } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { skillsApi, tracesApi } from "@/lib/api";
import type { TraceListItem, TraceDetail } from "@/lib/api";

interface EvolveSkillModalProps {
  skillName: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onComplete: () => void;
}

export function EvolveSkillModal({
  skillName,
  open,
  onOpenChange,
  onComplete,
}: EvolveSkillModalProps) {
  const [traces, setTraces] = React.useState<TraceListItem[]>([]);
  const [selectedTraceIds, setSelectedTraceIds] = React.useState<Set<string>>(new Set());
  const [feedback, setFeedback] = React.useState("");
  const [tracesLoading, setTracesLoading] = React.useState(false);
  const [evolving, setEvolving] = React.useState(false);
  const [evolveError, setEvolveError] = React.useState<string | null>(null);
  const [evolveResult, setEvolveResult] = React.useState<string | null>(null);
  const [evolveTaskId, setEvolveTaskId] = React.useState<string | null>(null);
  const [evolveTraceId, setEvolveTraceId] = React.useState<string | null>(null);
  const [evolveStatus, setEvolveStatus] = React.useState<string | null>(null);
  const [viewingTraceId, setViewingTraceId] = React.useState<string | null>(null);
  const [viewingTraceDetail, setViewingTraceDetail] = React.useState<TraceDetail | null>(null);
  const [traceDetailLoading, setTraceDetailLoading] = React.useState(false);

  const hasTraces = selectedTraceIds.size > 0;
  const hasFeedback = feedback.trim().length > 0;
  const canSubmit = hasTraces || hasFeedback;

  // Load traces when modal opens
  React.useEffect(() => {
    if (!open) return;

    const loadTraces = async () => {
      setTracesLoading(true);
      try {
        const response = await tracesApi.list({ skill_name: skillName, limit: 100 });
        setTraces(response.traces);
        setSelectedTraceIds(new Set());
      } catch (err) {
        console.error('Failed to load traces:', err);
        setTraces([]);
      } finally {
        setTracesLoading(false);
      }
    };

    loadTraces();
  }, [open, skillName]);

  // Poll for evolve task status
  React.useEffect(() => {
    if (!evolveTaskId || !evolving) return;

    const pollInterval = setInterval(async () => {
      try {
        const status = await skillsApi.getEvolveTaskStatus(evolveTaskId);
        setEvolveStatus(status.status);
        if (status.trace_id) {
          setEvolveTraceId(status.trace_id);
        }

        if (status.status === 'completed') {
          clearInterval(pollInterval);
          setEvolving(false);
          setEvolveResult(`Evolution complete! New version: ${status.new_version || 'created'}`);
          setEvolveTaskId(null);
          onComplete();
        } else if (status.status === 'failed') {
          clearInterval(pollInterval);
          setEvolving(false);
          setEvolveError(status.error || 'Evolution failed');
          setEvolveTaskId(null);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 3000);

    return () => clearInterval(pollInterval);
  }, [evolveTaskId, evolving, onComplete]);

  const handleEvolve = async () => {
    if (!canSubmit) return;

    setEvolving(true);
    setEvolveError(null);
    setEvolveResult(null);
    setEvolveStatus('pending');

    try {
      const result = await skillsApi.evolveViaTraces(skillName, {
        traceIds: hasTraces ? Array.from(selectedTraceIds) : undefined,
        feedback: hasFeedback ? feedback.trim() : undefined,
      });
      setEvolveTaskId(result.task_id);
    } catch (err) {
      setEvolving(false);
      setEvolveError(err instanceof Error ? err.message : "Failed to start evolution");
    }
  };

  const handleClose = () => {
    onOpenChange(false);
    setTraces([]);
    setSelectedTraceIds(new Set());
    setFeedback("");
    setEvolveError(null);
    setEvolveResult(null);
    setEvolveTaskId(null);
    setEvolveTraceId(null);
    setEvolveStatus(null);
    setViewingTraceId(null);
    setViewingTraceDetail(null);
  };

  const handleViewTrace = async (traceId: string) => {
    if (viewingTraceId === traceId) {
      setViewingTraceId(null);
      setViewingTraceDetail(null);
      return;
    }
    setViewingTraceId(traceId);
    setTraceDetailLoading(true);
    try {
      const detail = await tracesApi.get(traceId);
      setViewingTraceDetail(detail);
    } catch (err) {
      console.error('Failed to load trace detail:', err);
      setViewingTraceDetail(null);
    } finally {
      setTraceDetailLoading(false);
    }
  };

  const toggleTraceSelection = (traceId: string) => {
    const newSelected = new Set(selectedTraceIds);
    if (newSelected.has(traceId)) {
      newSelected.delete(traceId);
    } else {
      newSelected.add(traceId);
    }
    setSelectedTraceIds(newSelected);
  };

  const toggleAllTraces = () => {
    if (selectedTraceIds.size === traces.length) {
      setSelectedTraceIds(new Set());
    } else {
      setSelectedTraceIds(new Set(traces.map(t => t.id)));
    }
  };

  // Build submit button label
  const getButtonLabel = () => {
    if (evolving) return "Evolving...";
    const parts: string[] = [];
    if (hasTraces) parts.push(`${selectedTraceIds.size} Trace${selectedTraceIds.size !== 1 ? 's' : ''}`);
    if (hasFeedback) parts.push("Feedback");
    if (parts.length === 0) return "Evolve Skill";
    return `Evolve from ${parts.join(" + ")}`;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[700px] max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>Evolve Skill</DialogTitle>
          <DialogDescription>
            Select execution traces and/or provide feedback to improve this skill. The AI will analyze the inputs and automatically evolve the skill.
          </DialogDescription>
        </DialogHeader>
        <div className="flex-1 overflow-auto py-4 px-1 space-y-4">
          {/* Traces section */}
          <div>
            <h3 className="text-sm font-medium mb-2">Execution Traces (optional)</h3>
            {tracesLoading ? (
              <div className="flex items-center justify-center py-4">
                <Spinner size="lg" />
                <span className="ml-2 text-muted-foreground">Loading traces...</span>
              </div>
            ) : traces.length === 0 ? (
              <div className="text-center py-4 border rounded-lg bg-muted/30">
                <p className="text-sm text-muted-foreground">
                  No execution traces found for this skill. You can still evolve using feedback below.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center gap-2 pb-2 border-b">
                  <input
                    type="checkbox"
                    checked={selectedTraceIds.size === traces.length}
                    onChange={toggleAllTraces}
                    className="h-4 w-4 rounded border-gray-300"
                    disabled={evolving}
                  />
                  <span className="text-sm font-medium">
                    Select all ({selectedTraceIds.size}/{traces.length} selected)
                  </span>
                </div>
                {traces.map((trace) => (
                  <div key={trace.id} className="space-y-2">
                    <div
                      className={`flex items-start gap-3 p-3 rounded-lg border ${
                        selectedTraceIds.has(trace.id) ? 'border-primary bg-primary/5' : 'border-border'
                      } ${viewingTraceId === trace.id ? 'ring-2 ring-blue-300' : ''}`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedTraceIds.has(trace.id)}
                        onChange={() => toggleTraceSelection(trace.id)}
                        className="h-4 w-4 mt-1 rounded border-gray-300"
                        disabled={evolving}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <Badge variant={trace.success ? 'success' : 'error'}>
                            {trace.success ? 'Success' : 'Failed'}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {new Date(trace.created_at).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-sm mt-1 truncate" title={trace.request}>
                          {trace.request}
                        </p>
                        <div className="flex gap-4 mt-1 text-xs text-muted-foreground">
                          <span>Turns: {trace.total_turns}</span>
                          <span>Tokens: {trace.total_input_tokens + trace.total_output_tokens}</span>
                          {trace.duration_ms && <span>Duration: {(trace.duration_ms / 1000).toFixed(1)}s</span>}
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant={viewingTraceId === trace.id ? "secondary" : "ghost"}
                        onClick={() => handleViewTrace(trace.id)}
                        disabled={evolving}
                      >
                        {viewingTraceId === trace.id ? 'Hide' : 'View'}
                      </Button>
                    </div>
                    {viewingTraceId === trace.id && (
                      <div className="ml-7 p-3 bg-muted rounded-lg text-sm space-y-3">
                        {traceDetailLoading ? (
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Spinner size="md" />
                            <span>Loading trace details...</span>
                          </div>
                        ) : viewingTraceDetail ? (
                          <>
                            <div>
                              <h4 className="font-medium text-xs text-muted-foreground mb-1">Request</h4>
                              <p className="text-sm">{viewingTraceDetail.request}</p>
                            </div>
                            {viewingTraceDetail.answer && (
                              <div>
                                <h4 className="font-medium text-xs text-muted-foreground mb-1">Answer</h4>
                                <p className="text-sm whitespace-pre-wrap">{viewingTraceDetail.answer}</p>
                              </div>
                            )}
                            {viewingTraceDetail.error && (
                              <div>
                                <h4 className="font-medium text-xs text-red-600 mb-1">Error</h4>
                                <p className="text-sm text-red-600">{viewingTraceDetail.error}</p>
                              </div>
                            )}
                            {viewingTraceDetail.steps && viewingTraceDetail.steps.length > 0 && (
                              <div>
                                <h4 className="font-medium text-xs text-muted-foreground mb-1">
                                  Execution Steps ({viewingTraceDetail.steps.length})
                                </h4>
                                <div className="space-y-2 max-h-60 overflow-auto">
                                  {viewingTraceDetail.steps.map((step, idx) => (
                                    <div key={idx} className="p-2 bg-background rounded border text-xs">
                                      <div className="flex items-center gap-2 mb-1">
                                        <Badge variant="outline" className="text-xs">
                                          {step.role}
                                        </Badge>
                                        {step.tool_name && (
                                          <span className="font-mono text-blue-600">{step.tool_name}</span>
                                        )}
                                      </div>
                                      {step.content && (
                                        <p className="text-muted-foreground truncate" title={step.content}>
                                          {step.content.substring(0, 200)}{step.content.length > 200 ? '...' : ''}
                                        </p>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </>
                        ) : (
                          <p className="text-muted-foreground">Failed to load trace details</p>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Feedback section */}
          <div>
            <h3 className="text-sm font-medium mb-2">Feedback (optional)</h3>
            <Textarea
              placeholder="Describe what needs to be improved, fixed, or added to this skill..."
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              rows={4}
              disabled={evolving}
            />
          </div>

          {/* Status / Error / Result */}
          {evolving && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Spinner size="md" />
                <span>
                  {evolveStatus === 'pending' && 'Starting evolution task...'}
                  {evolveStatus === 'running' && 'Agent is analyzing and evolving the skill...'}
                  {!evolveStatus && 'Evolving skill...'}
                </span>
              </div>
              {evolveTraceId && (
                <a
                  href={`/traces/${evolveTraceId}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:underline"
                >
                  Trace ID: {evolveTraceId}
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
          )}
          {evolveError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md dark:bg-red-950 dark:border-red-800">
              <p className="text-red-600 text-sm dark:text-red-400">{evolveError}</p>
            </div>
          )}
          {evolveResult && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-md dark:bg-green-950 dark:border-green-800">
              <p className="text-green-800 text-sm font-medium mb-2 dark:text-green-200">Evolution Complete!</p>
              <pre className="text-xs text-green-700 whitespace-pre-wrap max-h-48 overflow-auto dark:text-green-300">
                {evolveResult}
              </pre>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={evolving}>
            {evolveResult ? "Close" : "Cancel"}
          </Button>
          {!evolveResult && (
            <Button
              onClick={handleEvolve}
              disabled={evolving || !canSubmit}
            >
              {getButtonLabel()}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Keep backward-compatible alias
export const EvolveTraceModal = EvolveSkillModal;
