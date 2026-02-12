'use client';

import { usePathname } from 'next/navigation';
import { AppHeader } from './app-header';

export function ConditionalHeader() {
  const pathname = usePathname();

  // Hide header on published agent pages and fullscreen chat
  if (pathname.startsWith('/published/') || pathname === '/chat') {
    return null;
  }

  return <AppHeader />;
}
