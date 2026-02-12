'use client';

import { File, Folder, FileText, FileCode, FileImage, FileJson, Download } from 'lucide-react';
import { BrowserFileEntry } from '@/lib/api';
import { formatFileSize, formatDateTime } from '@/lib/formatters';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface FileEntryProps {
  entry: BrowserFileEntry;
  isSelected: boolean;
  onSelect: () => void;
  onOpen: () => void;
  onDownload?: () => void;
}

function getFileIcon(entry: BrowserFileEntry) {
  if (entry.type === 'directory') {
    return <Folder className="h-5 w-5 text-yellow-500" />;
  }

  const ext = entry.extension?.toLowerCase();

  if (entry.is_image) {
    return <FileImage className="h-5 w-5 text-purple-500" />;
  }

  switch (ext) {
    case '.py':
    case '.js':
    case '.ts':
    case '.tsx':
    case '.jsx':
    case '.go':
    case '.rs':
    case '.java':
    case '.c':
    case '.cpp':
    case '.h':
    case '.rb':
    case '.php':
      return <FileCode className="h-5 w-5 text-green-500" />;
    case '.json':
    case '.yaml':
    case '.yml':
    case '.toml':
      return <FileJson className="h-5 w-5 text-orange-500" />;
    case '.md':
    case '.txt':
    case '.doc':
    case '.docx':
      return <FileText className="h-5 w-5 text-blue-500" />;
    default:
      return <File className="h-5 w-5 text-muted-foreground" />;
  }
}

export function FileEntry({ entry, isSelected, onSelect, onOpen, onDownload }: FileEntryProps) {
  const handleClick = () => {
    // Folders open on single click, files get selected
    if (entry.type === 'directory') {
      onOpen();
    } else {
      onSelect();
    }
  };

  const handleDoubleClick = () => {
    // Double click opens files (for preview)
    if (entry.type === 'file') {
      onOpen();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      onOpen();
    }
  };

  return (
    <div
      className={cn(
        'flex items-center gap-3 p-2 rounded-md cursor-pointer transition-colors group',
        isSelected
          ? 'bg-primary/10 ring-1 ring-primary/30'
          : 'hover:bg-muted/50'
      )}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
    >
      {getFileIcon(entry)}

      <div className="flex-1 min-w-0">
        <div className="font-medium truncate">{entry.name}</div>
        <div className="text-xs text-muted-foreground">
          {entry.type === 'directory'
            ? 'Folder'
            : entry.size !== null
              ? formatFileSize(entry.size)
              : 'Unknown size'}
        </div>
      </div>

      <div className="text-xs text-muted-foreground hidden sm:block">
        {formatDateTime(entry.modified_at)}
      </div>

      {entry.type === 'file' && onDownload && (
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={(e) => {
            e.stopPropagation();
            onDownload();
          }}
        >
          <Download className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}
