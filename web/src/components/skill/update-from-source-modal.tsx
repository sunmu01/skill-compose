"use client";

import React, { useState, useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { skillsApi } from "@/lib/api";
import { toast } from "sonner";
import { useTranslation } from "@/i18n/client";
import {
  Github,
  FileArchive,
  FolderOpen,
  Link,
  Upload,
  AlertTriangle,
  CheckCircle,
  Loader2,
} from "lucide-react";

interface UpdateFromSourceModalProps {
  skillName: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onComplete: () => void;
}

const isValidGitHubUrl = (url: string): boolean => {
  const pattern = /^https:\/\/github\.com\/[\w.-]+\/[\w.-]+(\/tree\/[\w.-]+(\/.*)?)?$/;
  return pattern.test(url);
};

export function UpdateFromSourceModal({
  skillName,
  open,
  onOpenChange,
  onComplete,
}: UpdateFromSourceModalProps) {
  const { t } = useTranslation("skills");

  // GitHub tab state
  const [githubUrl, setGithubUrl] = useState("");
  const [isGithubLoading, setIsGithubLoading] = useState(false);

  // File tab state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isFileLoading, setIsFileLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Folder tab state
  const [selectedFolder, setSelectedFolder] = useState<{
    name: string;
    files: File[];
  } | null>(null);
  const [isFolderDragging, setIsFolderDragging] = useState(false);
  const [isFolderLoading, setIsFolderLoading] = useState(false);
  const folderInputRef = useRef<HTMLInputElement>(null);

  const resetState = () => {
    setGithubUrl("");
    setIsGithubLoading(false);
    setSelectedFile(null);
    setIsDragging(false);
    setIsFileLoading(false);
    setSelectedFolder(null);
    setIsFolderDragging(false);
    setIsFolderLoading(false);
  };

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) resetState();
    onOpenChange(newOpen);
  };

  const handleResult = (result: { new_version: string | null; message: string; changes: string[] | null }) => {
    if (!result.new_version) {
      toast.info(t("updateFromSource.noChanges"));
    } else {
      const changesStr = result.changes?.length
        ? `: ${result.changes.join(", ")}`
        : "";
      toast.success(`${result.message}${changesStr}`);
      onComplete();
    }
    handleOpenChange(false);
  };

  // --- GitHub ---
  const handleGithubSubmit = async () => {
    setIsGithubLoading(true);
    try {
      const result = await skillsApi.updateFromSourceGitHub(skillName, githubUrl);
      handleResult(result);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      toast.error(msg);
    } finally {
      setIsGithubLoading(false);
    }
  };

  // --- File ---
  const handleFileSelect = (file: File) => {
    if (!file.name.endsWith(".skill") && !file.name.endsWith(".zip")) {
      toast.error(t("updateFromSource.invalidFileType"));
      return;
    }
    setSelectedFile(file);
  };

  const handleFileSubmit = async () => {
    if (!selectedFile) return;
    setIsFileLoading(true);
    try {
      const result = await skillsApi.updateFromSourceFile(skillName, selectedFile);
      handleResult(result);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      toast.error(msg);
    } finally {
      setIsFileLoading(false);
    }
  };

  // --- Folder ---
  const handleFolderSelect = (name: string, files: File[]) => {
    setSelectedFolder({ name, files });
  };

  const handleFolderInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const firstPath = (files[0] as any).webkitRelativePath as string;
    const folderName = firstPath.split("/")[0];

    const fileArray: File[] = [];
    for (let i = 0; i < files.length; i++) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const file = files[i] as any;
      const relativePath = file.webkitRelativePath as string;
      const newFile = new File([file], relativePath, { type: file.type });
      fileArray.push(newFile);
    }
    handleFolderSelect(folderName, fileArray);
  };

  const handleFolderDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsFolderDragging(false);

    const items = e.dataTransfer.items;
    if (!items || items.length === 0) return;

    const entry = items[0]?.webkitGetAsEntry?.();
    if (!entry?.isDirectory) {
      toast.error(t("updateFromSource.dropFolderOnly"));
      return;
    }

    const folderName = entry.name;
    const files: File[] = [];

    const readDirectory = async (
      dirEntry: FileSystemDirectoryEntry,
      path: string
    ) => {
      const reader = dirEntry.createReader();
      const entries = await new Promise<FileSystemEntry[]>((resolve) => {
        reader.readEntries((entries) => resolve(entries));
      });

      for (const ent of entries) {
        const entryPath = path ? `${path}/${ent.name}` : ent.name;
        if (ent.isFile) {
          const file = await new Promise<File>((resolve) => {
            (ent as FileSystemFileEntry).file((f) => {
              const newFile = new File(
                [f],
                `${folderName}/${entryPath}`,
                { type: f.type }
              );
              resolve(newFile);
            });
          });
          files.push(file);
        } else if (ent.isDirectory) {
          await readDirectory(ent as FileSystemDirectoryEntry, entryPath);
        }
      }
    };

    await readDirectory(entry as FileSystemDirectoryEntry, "");
    handleFolderSelect(folderName, files);
  };

  const handleFolderSubmit = async () => {
    if (!selectedFolder) return;
    setIsFolderLoading(true);
    try {
      const result = await skillsApi.updateFromSourceFolder(
        skillName,
        selectedFolder.files
      );
      handleResult(result);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      toast.error(msg);
    } finally {
      setIsFolderLoading(false);
    }
  };

  const isAnyLoading = isGithubLoading || isFileLoading || isFolderLoading;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[520px]">
        <DialogHeader>
          <DialogTitle>{t("updateFromSource.title")}</DialogTitle>
          <DialogDescription>
            {t("updateFromSource.description", { name: skillName })}
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="github" className="mt-2">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="github" disabled={isAnyLoading}>
              <Github className="h-4 w-4 mr-1.5" />
              {t("updateFromSource.tabs.github")}
            </TabsTrigger>
            <TabsTrigger value="file" disabled={isAnyLoading}>
              <FileArchive className="h-4 w-4 mr-1.5" />
              {t("updateFromSource.tabs.file")}
            </TabsTrigger>
            <TabsTrigger value="folder" disabled={isAnyLoading}>
              <FolderOpen className="h-4 w-4 mr-1.5" />
              {t("updateFromSource.tabs.folder")}
            </TabsTrigger>
          </TabsList>

          {/* GitHub Tab */}
          <TabsContent value="github" className="space-y-4 mt-4">
            <div className="space-y-2">
              <div className="relative">
                <Link className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder={t("updateFromSource.githubPlaceholder")}
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  className="pl-10"
                  disabled={isGithubLoading}
                />
              </div>
              {githubUrl && !isValidGitHubUrl(githubUrl) && (
                <div className="flex items-center gap-2 text-sm text-amber-600 dark:text-amber-400">
                  <AlertTriangle className="h-4 w-4 shrink-0" />
                  <span>{t("updateFromSource.invalidGithubUrl")}</span>
                </div>
              )}
            </div>
            <Button
              className="w-full"
              onClick={handleGithubSubmit}
              disabled={!githubUrl.trim() || !isValidGitHubUrl(githubUrl) || isGithubLoading}
            >
              {isGithubLoading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Github className="h-4 w-4 mr-2" />
              )}
              {isGithubLoading
                ? t("updateFromSource.updating")
                : t("updateFromSource.updateButton")}
            </Button>
          </TabsContent>

          {/* File Tab */}
          <TabsContent value="file" className="space-y-4 mt-4">
            <div
              className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                isDragging
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50"
              } ${isFileLoading ? "opacity-50 pointer-events-none" : "cursor-pointer"}`}
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={(e) => {
                e.preventDefault();
                setIsDragging(false);
              }}
              onDrop={(e) => {
                e.preventDefault();
                setIsDragging(false);
                const files = e.dataTransfer.files;
                if (files.length > 0) handleFileSelect(files[0]);
              }}
              onClick={() => !isFileLoading && fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".skill,.zip"
                onChange={(e) => {
                  if (e.target.files?.[0]) handleFileSelect(e.target.files[0]);
                }}
                className="hidden"
                disabled={isFileLoading}
              />
              {selectedFile ? (
                <div className="flex items-center justify-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="font-medium">{selectedFile.name}</span>
                </div>
              ) : (
                <div className="space-y-2">
                  <Upload className="h-8 w-8 mx-auto text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    {t("updateFromSource.dropFile")}
                  </p>
                </div>
              )}
            </div>
            <Button
              className="w-full"
              onClick={handleFileSubmit}
              disabled={!selectedFile || isFileLoading}
            >
              {isFileLoading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <FileArchive className="h-4 w-4 mr-2" />
              )}
              {isFileLoading
                ? t("updateFromSource.updating")
                : t("updateFromSource.updateButton")}
            </Button>
          </TabsContent>

          {/* Folder Tab */}
          <TabsContent value="folder" className="space-y-4 mt-4">
            <div
              className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                isFolderDragging
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50"
              } ${isFolderLoading ? "opacity-50 pointer-events-none" : "cursor-pointer"}`}
              onDragOver={(e) => {
                e.preventDefault();
                setIsFolderDragging(true);
              }}
              onDragLeave={(e) => {
                e.preventDefault();
                setIsFolderDragging(false);
              }}
              onDrop={handleFolderDrop}
              onClick={() => !isFolderLoading && folderInputRef.current?.click()}
            >
              <input
                ref={folderInputRef}
                type="file"
                // @ts-expect-error webkitdirectory is not in the types
                webkitdirectory=""
                directory=""
                multiple
                onChange={handleFolderInputChange}
                className="hidden"
                disabled={isFolderLoading}
              />
              {selectedFolder ? (
                <div className="flex items-center justify-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="font-medium">
                    {selectedFolder.name} ({selectedFolder.files.length} files)
                  </span>
                </div>
              ) : (
                <div className="space-y-2">
                  <FolderOpen className="h-8 w-8 mx-auto text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    {t("updateFromSource.dropFolder")}
                  </p>
                </div>
              )}
            </div>
            <Button
              className="w-full"
              onClick={handleFolderSubmit}
              disabled={!selectedFolder || isFolderLoading}
            >
              {isFolderLoading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <FolderOpen className="h-4 w-4 mr-2" />
              )}
              {isFolderLoading
                ? t("updateFromSource.updating")
                : t("updateFromSource.updateButton")}
            </Button>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
