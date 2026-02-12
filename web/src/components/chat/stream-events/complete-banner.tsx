"use client";

import { CheckCircle2, XCircle } from "lucide-react";
import type { CompleteData } from "@/types/stream-events";

interface CompleteBannerProps {
  data: CompleteData;
}

export function CompleteBanner({ data }: CompleteBannerProps) {
  const failed = data.success === false;

  if (failed) {
    return (
      <div className="flex items-center gap-2 py-2 mt-2">
        <div className="flex-1 h-px bg-red-200 dark:bg-red-800" />
        <div className="flex items-center gap-2 px-3 py-1 bg-red-50 dark:bg-red-950/50 rounded-full border border-red-200 dark:border-red-800">
          <XCircle className="h-4 w-4 text-red-600 dark:text-red-500" />
          <span className="text-xs font-medium text-red-700 dark:text-red-400">
            Failed
          </span>
          <span className="text-xs text-red-600 dark:text-red-500">
            ({data.totalTurns} turn{data.totalTurns !== 1 ? 's' : ''})
          </span>
        </div>
        <div className="flex-1 h-px bg-red-200 dark:bg-red-800" />
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 py-2 mt-2">
      <div className="flex-1 h-px bg-green-200 dark:bg-green-800" />
      <div className="flex items-center gap-2 px-3 py-1 bg-green-50 dark:bg-green-950/50 rounded-full border border-green-200 dark:border-green-800">
        <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-500" />
        <span className="text-xs font-medium text-green-700 dark:text-green-400">
          Complete
        </span>
        <span className="text-xs text-green-600 dark:text-green-500">
          ({data.totalTurns} turn{data.totalTurns !== 1 ? 's' : ''})
        </span>
      </div>
      <div className="flex-1 h-px bg-green-200 dark:bg-green-800" />
    </div>
  );
}
