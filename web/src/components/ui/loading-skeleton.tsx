import { cn } from '@/lib/utils';

interface LoadingSkeletonProps {
  variant?: 'card-grid' | 'list' | 'detail';
  count?: number;
  className?: string;
}

export function LoadingSkeleton({ variant = 'card-grid', count = 3, className }: LoadingSkeletonProps) {
  if (variant === 'card-grid') {
    return (
      <div className={cn('grid gap-4 md:grid-cols-2 lg:grid-cols-3', className)}>
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            className="rounded-lg border bg-card p-6 animate-pulse"
          >
            <div className="h-5 bg-muted rounded w-32 mb-3" />
            <div className="h-4 bg-muted rounded w-48 mb-4" />
            <div className="h-4 bg-muted rounded w-full" />
          </div>
        ))}
      </div>
    );
  }

  if (variant === 'list') {
    return (
      <div className={cn('space-y-4', className)}>
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            className="rounded-lg border bg-card p-4 animate-pulse"
          >
            <div className="h-4 bg-muted rounded w-1/3 mb-2" />
            <div className="h-3 bg-muted rounded w-2/3" />
          </div>
        ))}
      </div>
    );
  }

  // detail
  return (
    <div className={cn('space-y-6 animate-pulse', className)}>
      <div className="h-8 bg-muted rounded w-48" />
      <div className="h-4 bg-muted rounded w-64" />
      <div className="grid grid-cols-2 gap-4">
        <div className="h-20 bg-muted rounded" />
        <div className="h-20 bg-muted rounded" />
      </div>
      <div className="h-40 bg-muted rounded" />
    </div>
  );
}
