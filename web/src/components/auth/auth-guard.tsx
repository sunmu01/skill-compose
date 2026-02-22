'use client';

/**
 * [INPUT]: 依赖 auth.ts 的 isAuthenticated
 * [OUTPUT]: 对外提供 AuthGuard 组件
 * [POS]: components/auth 的路由守护组件，被 providers.tsx 包裹在最外层
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { isAuthenticated } from '@/lib/auth';

const PUBLIC_PATHS = ['/login', '/published'];

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    const isPublic = PUBLIC_PATHS.some(p => pathname.startsWith(p));
    if (!isPublic && !isAuthenticated()) {
      router.replace('/login');
      return;
    }
    setChecked(true);
  }, [pathname, router]);

  // 公开路径直接渲染，无需等待检查
  const isPublic = PUBLIC_PATHS.some(p => pathname.startsWith(p));
  if (isPublic) return <>{children}</>;

  // 认证检查完成前不渲染（避免闪烁）
  if (!checked) return null;

  return <>{children}</>;
}
