'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from 'next-themes';
import { useState, useEffect } from 'react';
import { ChatProvider } from '@/components/chat/chat-provider';
import { initI18next } from '@/i18n/client';

export function Providers({ children }: { children: React.ReactNode }) {
  // Initialize i18next on mount
  useEffect(() => {
    initI18next();
  }, []);

  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <QueryClientProvider client={queryClient}>
        <ChatProvider>
          {children}
        </ChatProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
