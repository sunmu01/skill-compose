'use client';

import { BrowserFileEntry, browserApi } from '@/lib/api';
import { FileEntry } from './file-entry';
import { Folder } from 'lucide-react';

interface FileListProps {
  entries: BrowserFileEntry[];
  selectedPath: string | null;
  onSelect: (entry: BrowserFileEntry) => void;
  onNavigate: (path: string) => void;
}

export function FileList({ entries, selectedPath, onSelect, onNavigate }: FileListProps) {
  if (entries.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <Folder className="h-12 w-12 mb-4 opacity-50" />
        <p>This folder is empty</p>
      </div>
    );
  }

  const handleOpen = (entry: BrowserFileEntry) => {
    if (entry.type === 'directory') {
      onNavigate(entry.path);
    } else {
      onSelect(entry);
    }
  };

  const handleDownload = (entry: BrowserFileEntry) => {
    const url = browserApi.getDownloadUrl(entry.path);
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-1">
      {entries.map((entry) => (
        <FileEntry
          key={entry.path}
          entry={entry}
          isSelected={selectedPath === entry.path}
          onSelect={() => onSelect(entry)}
          onOpen={() => handleOpen(entry)}
          onDownload={entry.type === 'file' ? () => handleDownload(entry) : undefined}
        />
      ))}
    </div>
  );
}
