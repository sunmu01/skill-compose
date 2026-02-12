"use client";

import React from "react";
import { ChevronDown, ChevronRight, Wrench } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { ToolCallData } from "@/types/stream-events";

interface ToolCallCardProps {
  data: ToolCallData;
  defaultExpanded?: boolean;
}

export function ToolCallCard({ data, defaultExpanded = false }: ToolCallCardProps) {
  const [expanded, setExpanded] = React.useState(defaultExpanded);
  const hasInput = data.toolInput && Object.keys(data.toolInput).length > 0;

  return (
    <div className="border rounded-md my-1.5 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-2 bg-muted/50 hover:bg-muted/70 transition-colors text-left"
      >
        {hasInput ? (
          expanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
          )
        ) : (
          <Wrench className="h-4 w-4 text-muted-foreground shrink-0" />
        )}
        <Badge variant="purple" className="text-xs">
          {data.toolName}
        </Badge>
        {!hasInput && (
          <span className="text-xs text-muted-foreground">(no input)</span>
        )}
      </button>
      {expanded && hasInput && (
        <div className="px-3 py-2 bg-muted/30 border-t">
          <div className="text-xs text-muted-foreground mb-1">Input:</div>
          <pre className="text-xs bg-background rounded p-2 overflow-x-auto max-h-48 overflow-y-auto">
            {JSON.stringify(data.toolInput, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
