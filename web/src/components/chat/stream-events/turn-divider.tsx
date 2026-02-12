"use client";

import { Badge } from "@/components/ui/badge";
import type { TurnStartData } from "@/types/stream-events";

interface TurnDividerProps {
  data: TurnStartData;
}

export function TurnDivider({ data }: TurnDividerProps) {
  return (
    <div className="flex items-center gap-2 py-2">
      <div className="flex-1 h-px bg-border" />
      <Badge variant="outline" className="text-xs font-normal">
        Turn {data.turn}/{data.maxTurns}
      </Badge>
      <div className="flex-1 h-px bg-border" />
    </div>
  );
}
