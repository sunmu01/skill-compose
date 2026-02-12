'use client';

import { X, Download, FileWarning } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { BrowserFileEntry, browserApi, BrowserFilePreview as PreviewData } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Spinner } from '@/components/ui/spinner';
import { getLanguageFromFilename, formatFileSize } from '@/lib/formatters';
import { useFilePreview } from '@/hooks/use-browser';

interface FilePreviewProps {
  file: BrowserFileEntry;
  onClose: () => void;
}

export function FilePreview({ file, onClose }: FilePreviewProps) {
  const { data: preview, isLoading, error } = useFilePreview(file.path);

  const handleDownload = () => {
    const url = browserApi.getDownloadUrl(file.path);
    window.open(url, '_blank');
  };

  const language = getLanguageFromFilename(file.name);

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex-shrink-0 py-3 px-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-medium truncate">
            {file.name}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={handleDownload}>
              <Download className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
        {file.size !== null && (
          <p className="text-xs text-muted-foreground">
            {formatFileSize(file.size)}
          </p>
        )}
      </CardHeader>

      <CardContent className="flex-1 overflow-auto px-4 pb-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <Spinner size="md" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <FileWarning className="h-12 w-12 mb-4 opacity-50" />
            <p className="text-sm">{error instanceof Error ? error.message : 'Failed to load preview'}</p>
          </div>
        ) : preview?.type === 'image' ? (
          <div className="flex items-center justify-center h-full">
            <img
              src={`data:${preview.mime_type};base64,${preview.content}`}
              alt={file.name}
              className="max-w-full max-h-full object-contain rounded-md"
            />
          </div>
        ) : preview?.type === 'text' ? (
          <div className="rounded-md h-full code-preview-scrollbar">
            <SyntaxHighlighter
              language={language}
              style={oneDark}
              customStyle={{
                margin: 0,
                padding: '12px',
                fontSize: '12px',
                borderRadius: '6px',
                minHeight: '100%',
                maxHeight: '100%',
                overflow: 'auto',
              }}
              showLineNumbers
              wrapLongLines={false}
            >
              {preview.content || '(empty file)'}
            </SyntaxHighlighter>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <FileWarning className="h-12 w-12 mb-4 opacity-50" />
            <p className="text-sm">Preview not available for this file type</p>
            <Button variant="outline" size="sm" className="mt-4" onClick={handleDownload}>
              <Download className="h-4 w-4 mr-2" />
              Download file
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
