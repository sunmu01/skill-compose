'use client';

import { ChevronRight, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Breadcrumb {
  name: string;
  path: string;
}

interface FileBreadcrumbsProps {
  breadcrumbs: Breadcrumb[];
  onNavigate: (path: string) => void;
}

export function FileBreadcrumbs({ breadcrumbs, onNavigate }: FileBreadcrumbsProps) {
  return (
    <nav className="flex items-center gap-1 text-sm">
      {breadcrumbs.map((crumb, index) => (
        <div key={crumb.path} className="flex items-center">
          {index > 0 && (
            <ChevronRight className="h-4 w-4 text-muted-foreground mx-1" />
          )}
          {index === breadcrumbs.length - 1 ? (
            <span className="font-medium text-foreground flex items-center gap-1">
              {index === 0 && <Home className="h-4 w-4" />}
              {crumb.name}
            </span>
          ) : (
            <Button
              variant="ghost"
              size="sm"
              className="h-auto px-1 py-0.5 text-muted-foreground hover:text-foreground"
              onClick={() => onNavigate(crumb.path)}
            >
              {index === 0 && <Home className="h-4 w-4 mr-1" />}
              {crumb.name}
            </Button>
          )}
        </div>
      ))}
    </nav>
  );
}
