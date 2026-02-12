'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, File, AlertCircle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useUploadFile } from '@/hooks/use-browser';

interface UploadDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  targetPath: string;
}

export function UploadDialog({ open, onOpenChange, targetPath }: UploadDialogProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const [uploadErrors, setUploadErrors] = useState<Record<string, string>>({});
  const uploadMutation = useUploadFile();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles((prev) => [...prev, ...acceptedFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
  });

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
    const fileName = files[index]?.name;
    if (fileName) {
      setUploadErrors((prev) => {
        const next = { ...prev };
        delete next[fileName];
        return next;
      });
    }
  };

  const handleUpload = async () => {
    setUploadErrors({});

    for (const file of files) {
      setUploadProgress((prev) => ({ ...prev, [file.name]: 0 }));

      try {
        await uploadMutation.mutateAsync({ targetPath, file });
        setUploadProgress((prev) => ({ ...prev, [file.name]: 100 }));
      } catch (error) {
        setUploadErrors((prev) => ({
          ...prev,
          [file.name]: error instanceof Error ? error.message : 'Upload failed',
        }));
      }
    }

    // Clear successful uploads
    const hasErrors = Object.keys(uploadErrors).length > 0;
    if (!hasErrors) {
      setTimeout(() => {
        setFiles([]);
        setUploadProgress({});
        onOpenChange(false);
      }, 500);
    }
  };

  const handleClose = () => {
    if (!uploadMutation.isPending) {
      setFiles([]);
      setUploadProgress({});
      setUploadErrors({});
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Upload Files</DialogTitle>
          <DialogDescription>
            Upload files to: {targetPath || 'Root'}
          </DialogDescription>
        </DialogHeader>

        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
            transition-colors
            ${isDragActive
              ? 'border-primary bg-primary/5'
              : 'border-muted-foreground/25 hover:border-primary/50'
            }
          `}
        >
          <input {...getInputProps()} />
          <Upload className="h-10 w-10 mx-auto mb-4 text-muted-foreground" />
          {isDragActive ? (
            <p>Drop the files here...</p>
          ) : (
            <p className="text-muted-foreground">
              Drag & drop files here, or click to select
            </p>
          )}
        </div>

        {files.length > 0 && (
          <div className="mt-4 space-y-2 max-h-48 overflow-auto">
            {files.map((file, index) => (
              <div
                key={`${file.name}-${index}`}
                className="flex items-center gap-2 p-2 rounded-md bg-muted/50"
              >
                <File className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{file.name}</p>
                  {uploadProgress[file.name] !== undefined && (
                    <Progress value={uploadProgress[file.name]} className="h-1 mt-1" />
                  )}
                  {uploadErrors[file.name] && (
                    <p className="text-xs text-destructive flex items-center gap-1 mt-1">
                      <AlertCircle className="h-3 w-3" />
                      {uploadErrors[file.name]}
                    </p>
                  )}
                </div>
                {!uploadMutation.isPending && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={() => removeFile(index)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}

        <div className="flex justify-end gap-2 mt-4">
          <Button variant="outline" onClick={handleClose} disabled={uploadMutation.isPending}>
            Cancel
          </Button>
          <Button
            onClick={handleUpload}
            disabled={files.length === 0 || uploadMutation.isPending}
          >
            {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
