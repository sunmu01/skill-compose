'use client';

import { RefreshCw, Upload, Download, FolderUp, ArrowUpDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { browserApi } from '@/lib/api';
import { useTranslation } from '@/i18n/client';
import { SortOption } from './file-browser';

interface FileToolbarProps {
  currentPath: string;
  parentPath: string | null;
  onRefresh: () => void;
  onNavigateUp: () => void;
  onUploadClick: () => void;
  isRefreshing?: boolean;
  sortBy: SortOption;
  onSortChange: (sort: SortOption) => void;
}

export function FileToolbar({
  currentPath,
  parentPath,
  onRefresh,
  onNavigateUp,
  onUploadClick,
  isRefreshing,
  sortBy,
  onSortChange,
}: FileToolbarProps) {
  const { t } = useTranslation('files');

  const handleDownloadFolder = () => {
    if (currentPath) {
      const url = browserApi.getDownloadZipUrl(currentPath);
      window.open(url, '_blank');
    }
  };

  return (
    <div className="flex items-center gap-2">
      <Select value={sortBy} onValueChange={(v) => onSortChange(v as SortOption)}>
        <SelectTrigger className="h-8 w-[180px] text-sm">
          <ArrowUpDown className="h-3.5 w-3.5 mr-2 shrink-0" />
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="name-asc">{t('sort.nameAsc')}</SelectItem>
          <SelectItem value="name-desc">{t('sort.nameDesc')}</SelectItem>
          <SelectItem value="modified-newest">{t('sort.modifiedNewest')}</SelectItem>
          <SelectItem value="modified-oldest">{t('sort.modifiedOldest')}</SelectItem>
          <SelectItem value="size-largest">{t('sort.sizeLargest')}</SelectItem>
          <SelectItem value="size-smallest">{t('sort.sizeSmallest')}</SelectItem>
        </SelectContent>
      </Select>

      {parentPath !== null && (
        <Button variant="outline" size="sm" onClick={onNavigateUp}>
          <FolderUp className="h-4 w-4 mr-2" />
          Up
        </Button>
      )}

      <Button variant="outline" size="sm" onClick={onRefresh} disabled={isRefreshing}>
        <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
        Refresh
      </Button>

      <Button variant="outline" size="sm" onClick={onUploadClick}>
        <Upload className="h-4 w-4 mr-2" />
        Upload
      </Button>

      {currentPath && (
        <Button variant="outline" size="sm" onClick={handleDownloadFolder}>
          <Download className="h-4 w-4 mr-2" />
          Download Folder
        </Button>
      )}
    </div>
  );
}
