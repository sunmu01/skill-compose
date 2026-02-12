"use client";

import { AlertCircle } from "lucide-react";
import type { ErrorData } from "@/types/stream-events";

interface ErrorBannerProps {
  data: ErrorData;
}

export function ErrorBanner({ data }: ErrorBannerProps) {
  return (
    <div className="flex items-start gap-2 p-3 my-1.5 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-md">
      <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-500 shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-red-700 dark:text-red-400">Error</div>
        <div className="text-sm text-red-600 dark:text-red-400 whitespace-pre-wrap">
          {data.message}
        </div>
      </div>
    </div>
  );
}
