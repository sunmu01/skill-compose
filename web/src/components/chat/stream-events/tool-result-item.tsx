"use client";

import React from "react";
import { Check, ChevronDown, ChevronRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { ToolResultData } from "@/types/stream-events";

interface ToolResultItemProps {
  data: ToolResultData;
  defaultExpanded?: boolean;
}

export function ToolResultItem({ data, defaultExpanded = false }: ToolResultItemProps) {
  const [expanded, setExpanded] = React.useState(defaultExpanded);
  const hasResult = data.toolResult && data.toolResult.length > 0;
  const isLongResult = hasResult && data.toolResult!.length > 200;

  // For short results, show inline. For long results, show expandable.
  if (!hasResult) {
    return (
      <div className="flex items-center gap-2 py-1 px-3 text-xs">
        <Check className="h-3.5 w-3.5 text-green-600 dark:text-green-500 shrink-0" />
        <Badge variant="outline-success" className="text-xs">
          {data.toolName}
        </Badge>
        <span className="text-muted-foreground">completed</span>
      </div>
    );
  }

  if (!isLongResult) {
    return (
      <div className="flex items-start gap-2 py-1 px-3 text-xs">
        <Check className="h-3.5 w-3.5 text-green-600 dark:text-green-500 shrink-0 mt-0.5" />
        <Badge variant="outline-success" className="text-xs shrink-0">
          {data.toolName}
        </Badge>
        <span className="text-muted-foreground break-all">{data.toolResult}</span>
      </div>
    );
  }

  return (
    <div className="border rounded-md my-1 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-1.5 bg-green-50 dark:bg-green-950/30 hover:bg-green-100 dark:hover:bg-green-950/50 transition-colors text-left"
      >
        {expanded ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
        )}
        <Check className="h-3.5 w-3.5 text-green-600 dark:text-green-500 shrink-0" />
        <Badge variant="outline-success" className="text-xs">
          {data.toolName}
        </Badge>
        <span className="text-xs text-muted-foreground truncate flex-1">
          {data.toolResult!.slice(0, 60)}...
        </span>
      </button>
      {expanded && (
        <div className="px-3 py-2 bg-muted/30 border-t">
          <pre className="text-xs bg-background rounded p-2 overflow-x-auto max-h-48 overflow-y-auto whitespace-pre-wrap">
            {data.toolResult!.length > 3000
              ? data.toolResult!.slice(0, 3000) + "\n\n... (truncated)"
              : data.toolResult}
          </pre>
        </div>
      )}
    </div>
  );
}
