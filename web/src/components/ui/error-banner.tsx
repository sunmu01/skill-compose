import { cn } from '@/lib/utils';

interface ErrorBannerProps {
  title?: string;
  message: string;
  className?: string;
}

export function ErrorBanner({ title = 'Error', message, className }: ErrorBannerProps) {
  return (
    <div className={cn(
      'rounded-lg border border-destructive/50 bg-destructive/10 p-4 dark:bg-destructive/20',
      className
    )}>
      <p className="font-medium text-destructive">{title}</p>
      <p className="text-sm text-destructive/80 mt-1">{message}</p>
    </div>
  );
}
