"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Upload, FileArchive, CheckCircle, XCircle, ArrowLeft, AlertTriangle, Copy, Github, Link, Folder, FolderOpen } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";
import { transferApi } from "@/lib/api";
import { useTranslation } from '@/i18n/client';

interface ImportResult {
  success: boolean;
  skill_name: string;
  version: string;
  message: string;
  conflict?: boolean;
  existing_skill?: string;
  existing_version?: string;
  skipped_files?: string[];
}

export default function ImportPage() {
  const router = useRouter();
  const { t } = useTranslation('import');
  const { t: tc } = useTranslation('common');
  const [activeTab, setActiveTab] = React.useState("github");

  // File upload state
  const [isDragging, setIsDragging] = React.useState(false);
  const [isUploading, setIsUploading] = React.useState(false);
  const [uploadError, setUploadError] = React.useState<string | null>(null);
  const [importResult, setImportResult] = React.useState<ImportResult | null>(null);
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  // GitHub import state
  const [githubUrl, setGithubUrl] = React.useState("");
  const [isGithubImporting, setIsGithubImporting] = React.useState(false);
  const [githubError, setGithubError] = React.useState<string | null>(null);
  const [githubResult, setGithubResult] = React.useState<ImportResult | null>(null);

  // Folder upload state
  const [isFolderDragging, setIsFolderDragging] = React.useState(false);
  const [isFolderUploading, setIsFolderUploading] = React.useState(false);
  const [folderError, setFolderError] = React.useState<string | null>(null);
  const [folderResult, setFolderResult] = React.useState<ImportResult | null>(null);
  const [selectedFolder, setSelectedFolder] = React.useState<{ name: string; files: File[] } | null>(null);
  const folderInputRef = React.useRef<HTMLInputElement>(null);

  // Conflict dialog state (shared between all tabs)
  const [conflictDialogOpen, setConflictDialogOpen] = React.useState(false);
  const [conflictInfo, setConflictInfo] = React.useState<{
    skillName: string;
    existingVersion: string;
    source: "file" | "github" | "folder";
  } | null>(null);

  // URL validation - supports:
  // - https://github.com/owner/repo
  // - https://github.com/owner/repo/tree/branch
  // - https://github.com/owner/repo/tree/branch/path
  const isValidGitHubUrl = (url: string): boolean => {
    const pattern = /^https:\/\/github\.com\/[\w.-]+\/[\w.-]+(\/tree\/[\w.-]+(\/.*)?)?$/;
    return pattern.test(url);
  };

  const getGitHubUrlHint = (url: string): string | null => {
    if (!url || isValidGitHubUrl(url)) return null;
    if (!url.startsWith("http")) return t('github.hints.httpsRequired');
    if (!url.includes("github.com")) return t('github.hints.githubRequired');
    if (url.startsWith("http://github.com")) return t('github.hints.useHttps');
    const parts = url.replace("https://github.com/", "").split("/");
    if (parts.length < 2 || !parts[1]) return t('github.hints.ownerRepoRequired');
    if (parts.length > 2 && parts[2] !== "tree") return t('github.hints.treeFormat');
    if (parts[2] === "tree" && (!parts[3] || !parts[3].trim())) return t('github.hints.branchRequired');
    return t('github.hints.expectedFormat');
  };

  // File upload handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileSelect = (file: File) => {
    setUploadError(null);
    setImportResult(null);
    setConflictInfo(null);

    if (!file.name.endsWith('.skill') && !file.name.endsWith('.zip')) {
      setUploadError(t('file.invalidFile'));
      return;
    }

    setSelectedFile(file);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadError(null);
    setImportResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:62610';

      // First, check for conflicts
      const checkResponse = await fetch(`${apiUrl}/api/v1/registry/import?check_only=true`, {
        method: 'POST',
        body: formData,
      });

      if (!checkResponse.ok) {
        const errorData = await checkResponse.json().catch(() => null);
        throw new Error(errorData?.detail || `Check failed: ${checkResponse.statusText}`);
      }

      const checkResult: ImportResult = await checkResponse.json();

      if (checkResult.conflict) {
        // Show conflict dialog
        setConflictInfo({
          skillName: checkResult.existing_skill || checkResult.skill_name,
          existingVersion: checkResult.existing_version || "unknown",
          source: "file",
        });
        setConflictDialogOpen(true);
        setIsUploading(false);
        return;
      }

      // No conflict, proceed with import
      await doFileImport();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : t('status.genericError'));
      setIsUploading(false);
    }
  };

  const doFileImport = async (conflictAction?: string) => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:62610';
      const url = conflictAction
        ? `${apiUrl}/api/v1/registry/import?conflict_action=${conflictAction}`
        : `${apiUrl}/api/v1/registry/import`;

      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const detail = errorData?.detail;
        if (typeof detail === 'object' && detail.message) {
          throw new Error(detail.message);
        }
        throw new Error(detail || `Import failed: ${response.statusText}`);
      }

      const result: ImportResult = await response.json();
      setImportResult(result);
      setSelectedFile(null);
      setConflictDialogOpen(false);
      setConflictInfo(null);

      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : t('status.genericError'));
    } finally {
      setIsUploading(false);
    }
  };

  // GitHub import handlers
  const handleGitHubImport = async () => {
    if (!githubUrl.trim()) return;

    setIsGithubImporting(true);
    setGithubError(null);
    setGithubResult(null);

    try {
      // First, check for conflicts
      const checkResult = await transferApi.importFromGitHub({
        url: githubUrl.trim(),
        checkOnly: true,
      });

      if (checkResult.conflict) {
        setConflictInfo({
          skillName: checkResult.existing_skill || checkResult.skill_name,
          existingVersion: checkResult.existing_version || "unknown",
          source: "github",
        });
        setConflictDialogOpen(true);
        setIsGithubImporting(false);
        return;
      }

      // No conflict, proceed with import
      await doGitHubImport();
    } catch (err) {
      setGithubError(err instanceof Error ? err.message : t('status.githubError'));
      setIsGithubImporting(false);
    }
  };

  const doGitHubImport = async (conflictAction?: string) => {
    setIsGithubImporting(true);
    setGithubError(null);

    try {
      const result = await transferApi.importFromGitHub({
        url: githubUrl.trim(),
        conflictAction,
      });

      setGithubResult(result);
      setGithubUrl("");
      setConflictDialogOpen(false);
      setConflictInfo(null);
    } catch (err) {
      setGithubError(err instanceof Error ? err.message : t('status.githubError'));
    } finally {
      setIsGithubImporting(false);
    }
  };

  // Folder upload handlers
  const handleFolderDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsFolderDragging(true);
  };

  const handleFolderDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsFolderDragging(false);
  };

  const handleFolderDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsFolderDragging(false);

    const items = e.dataTransfer.items;
    if (!items || items.length === 0) return;

    // Get the first item as a file system entry
    const item = items[0];
    const entry = item.webkitGetAsEntry?.();

    if (!entry) {
      setFolderError(t('folder.errors.cannotRead'));
      return;
    }

    if (!entry.isDirectory) {
      setFolderError(t('folder.errors.notFolder'));
      return;
    }

    // Read all files from the directory
    const files: File[] = [];
    const folderName = entry.name;

    const readDirectory = async (dirEntry: FileSystemDirectoryEntry, path: string): Promise<void> => {
      return new Promise((resolve, reject) => {
        const reader = dirEntry.createReader();
        const readEntries = () => {
          reader.readEntries(async (entries) => {
            if (entries.length === 0) {
              resolve();
              return;
            }
            for (const entry of entries) {
              if (entry.isFile) {
                const fileEntry = entry as FileSystemFileEntry;
                const file = await new Promise<File>((res, rej) => {
                  fileEntry.file(
                    (f) => {
                      // Create a new File with the relative path as name
                      const relativePath = path ? `${path}/${f.name}` : f.name;
                      const newFile = new File([f], `${folderName}/${relativePath}`, { type: f.type });
                      res(newFile);
                    },
                    rej
                  );
                });
                files.push(file);
              } else if (entry.isDirectory) {
                const subPath = path ? `${path}/${entry.name}` : entry.name;
                await readDirectory(entry as FileSystemDirectoryEntry, subPath);
              }
            }
            // Continue reading (readEntries returns max 100 entries at a time)
            readEntries();
          }, reject);
        };
        readEntries();
      });
    };

    try {
      await readDirectory(entry as FileSystemDirectoryEntry, "");
      handleFolderSelect(folderName, files);
    } catch (err) {
      setFolderError(t('folder.errors.readFailed'));
    }
  };

  const handleFolderInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    // Extract folder name from the first file's webkitRelativePath
    const firstPath = (files[0] as any).webkitRelativePath as string;
    const folderName = firstPath.split("/")[0];

    // Convert FileList to array and set proper names with relative paths
    const fileArray: File[] = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i] as any;
      const relativePath = file.webkitRelativePath as string;
      // Create new File with the relative path as name
      const newFile = new File([file], relativePath, { type: file.type });
      fileArray.push(newFile);
    }

    handleFolderSelect(folderName, fileArray);
  };

  const handleFolderSelect = (folderName: string, files: File[]) => {
    setFolderError(null);
    setFolderResult(null);
    setConflictInfo(null);

    // Check if SKILL.md exists in the folder root
    const hasSkillMd = files.some((f) => {
      const parts = f.name.split("/");
      // SKILL.md should be at folder/SKILL.md (second level)
      return parts.length === 2 && parts[1].toUpperCase() === "SKILL.MD";
    });

    if (!hasSkillMd) {
      setFolderError(t('folder.errors.noSkillMd'));
      return;
    }

    setSelectedFolder({ name: folderName, files });
  };

  const handleFolderUpload = async () => {
    if (!selectedFolder) return;

    setIsFolderUploading(true);
    setFolderError(null);
    setFolderResult(null);

    try {
      const formData = new FormData();
      selectedFolder.files.forEach((file) => {
        formData.append("files", file);
      });

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:62610";

      // First, check for conflicts
      const checkResponse = await fetch(`${apiUrl}/api/v1/registry/import-folder?check_only=true`, {
        method: "POST",
        body: formData,
      });

      if (!checkResponse.ok) {
        const errorData = await checkResponse.json().catch(() => null);
        throw new Error(errorData?.detail || `Check failed: ${checkResponse.statusText}`);
      }

      const checkResult: ImportResult = await checkResponse.json();

      if (checkResult.conflict) {
        setConflictInfo({
          skillName: checkResult.existing_skill || checkResult.skill_name,
          existingVersion: checkResult.existing_version || "unknown",
          source: "folder" as const,
        });
        setConflictDialogOpen(true);
        setIsFolderUploading(false);
        return;
      }

      // No conflict, proceed with import
      await doFolderImport();
    } catch (err) {
      setFolderError(err instanceof Error ? err.message : t('status.genericError'));
      setIsFolderUploading(false);
    }
  };

  const doFolderImport = async (conflictAction?: string) => {
    if (!selectedFolder) return;

    setIsFolderUploading(true);
    setFolderError(null);

    try {
      const formData = new FormData();
      selectedFolder.files.forEach((file) => {
        formData.append("files", file);
      });

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:62610";
      const url = conflictAction
        ? `${apiUrl}/api/v1/registry/import-folder?conflict_action=${conflictAction}`
        : `${apiUrl}/api/v1/registry/import-folder`;

      const response = await fetch(url, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const detail = errorData?.detail;
        if (typeof detail === "object" && detail.message) {
          throw new Error(detail.message);
        }
        throw new Error(detail || `Import failed: ${response.statusText}`);
      }

      const result: ImportResult = await response.json();
      setFolderResult(result);
      setSelectedFolder(null);
      setConflictDialogOpen(false);
      setConflictInfo(null);

      // Reset folder input
      if (folderInputRef.current) {
        folderInputRef.current.value = "";
      }
    } catch (err) {
      setFolderError(err instanceof Error ? err.message : t('status.genericError'));
    } finally {
      setIsFolderUploading(false);
    }
  };

  const handleFolderReset = () => {
    setSelectedFolder(null);
    setFolderError(null);
    setFolderResult(null);
    setConflictInfo(null);
    if (folderInputRef.current) {
      folderInputRef.current.value = "";
    }
  };

  // Shared handlers
  const handleCreateCopy = async () => {
    if (conflictInfo?.source === "file") {
      await doFileImport("copy");
    } else if (conflictInfo?.source === "folder") {
      await doFolderImport("copy");
    } else {
      await doGitHubImport("copy");
    }
  };

  const handleCancelConflict = () => {
    setConflictDialogOpen(false);
    setConflictInfo(null);
  };

  const handleFileReset = () => {
    setSelectedFile(null);
    setUploadError(null);
    setImportResult(null);
    setConflictInfo(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleGitHubReset = () => {
    setGithubUrl("");
    setGithubError(null);
    setGithubResult(null);
    setConflictInfo(null);
  };

  const isImporting = isUploading || isGithubImporting || isFolderUploading;

  return (
    <div className="container mx-auto py-8 max-w-2xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">{t('title')}</h1>
          <p className="text-muted-foreground mt-1">
            {t('description')}
          </p>
        </div>
        <Button variant="outline" onClick={() => router.push("/skills")}>
          <ArrowLeft className="h-4 w-4 mr-1" />
          {t('backToSkills')}
        </Button>
      </div>

      {/* Import Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3 mb-4">
          <TabsTrigger value="github" className="flex items-center gap-2">
            <Github className="h-4 w-4" />
            {t('tabs.github')}
          </TabsTrigger>
          <TabsTrigger value="file" className="flex items-center gap-2">
            <Upload className="h-4 w-4" />
            {t('tabs.file')}
          </TabsTrigger>
          <TabsTrigger value="folder" className="flex items-center gap-2">
            <Folder className="h-4 w-4" />
            {t('tabs.folder')}
          </TabsTrigger>
        </TabsList>

        {/* GitHub Import Tab */}
        <TabsContent value="github">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Github className="h-5 w-5" />
                {t('github.title')}
              </CardTitle>
              <CardDescription>
                {t('github.description')}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* URL Input */}
              <div className="space-y-2">
                <Label htmlFor="github-url">{t('github.urlLabel')}</Label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Link className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="github-url"
                      placeholder={t('github.placeholder')}
                      value={githubUrl}
                      onChange={(e) => {
                        setGithubUrl(e.target.value);
                        setGithubError(null);
                      }}
                      className="pl-10"
                      disabled={isGithubImporting}
                    />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">
                  {t('github.examples')}
                </p>
              </div>

              {/* Validation hint */}
              {githubUrl && getGitHubUrlHint(githubUrl) && (
                <div className="flex items-start gap-2 text-sm text-amber-600 dark:text-amber-400">
                  <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <span>{getGitHubUrlHint(githubUrl)}</span>
                </div>
              )}

              {/* Error Message */}
              {githubError && (
                <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg dark:bg-red-950 dark:border-red-800">
                  <XCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-red-800 dark:text-red-200">{t('status.importFailed')}</p>
                    <p className="text-sm text-red-600 dark:text-red-400">{githubError}</p>
                  </div>
                </div>
              )}

              {/* Success Message */}
              {githubResult && githubResult.success && (
                <div className="flex items-start gap-3 p-4 bg-green-50 border border-green-200 rounded-lg dark:bg-green-950 dark:border-green-800">
                  <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-medium text-green-800 dark:text-green-200">{t('status.importSuccess')}</p>
                    <p className="text-sm text-green-600 mt-1 dark:text-green-400">{githubResult.message}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="outline-success">
                        {githubResult.skill_name}
                      </Badge>
                      <Badge variant="outline-info">
                        v{githubResult.version}
                      </Badge>
                    </div>
                    {githubResult.skipped_files && githubResult.skipped_files.length > 0 && (
                      <div className="flex items-start gap-2 mt-3 p-2 bg-amber-50 border border-amber-200 rounded text-sm dark:bg-amber-950 dark:border-amber-800">
                        <AlertTriangle className="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" />
                        <div className="text-amber-700 dark:text-amber-300">
                          <p>{t('status.skippedFiles', { count: githubResult.skipped_files.length })}</p>
                          <p className="text-xs mt-1 opacity-80">{t('status.skippedFilesList', { files: githubResult.skipped_files.join(', ') })}</p>
                        </div>
                      </div>
                    )}
                    <Button
                      variant="link"
                      className="p-0 h-auto mt-2 text-green-700"
                      onClick={() => router.push(`/skills/${githubResult.skill_name}`)}
                    >
                      {t('status.viewSkill')}
                    </Button>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3">
                {!githubResult && (
                  <>
                    <Button
                      onClick={handleGitHubImport}
                      disabled={!githubUrl.trim() || !isValidGitHubUrl(githubUrl) || isGithubImporting}
                      className="flex-1"
                    >
                      {isGithubImporting ? (
                        <>
                          <Spinner size="md" className="mr-2 text-white" />
                          {t('status.importing')}
                        </>
                      ) : (
                        <>
                          <Github className="h-4 w-4 mr-2" />
                          {t('github.button')}
                        </>
                      )}
                    </Button>
                    {githubUrl && (
                      <Button variant="outline" onClick={handleGitHubReset} disabled={isGithubImporting}>
                        {tc('actions.clear')}
                      </Button>
                    )}
                  </>
                )}
                {githubResult && githubResult.success && (
                  <Button variant="outline" onClick={handleGitHubReset} className="flex-1">
                    {t('status.importAnother')}
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* File Upload Tab */}
        <TabsContent value="file">
          <Card>
            <CardHeader>
              <CardTitle>{t('file.title')}</CardTitle>
              <CardDescription>
                {t('file.description')}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Drop Zone */}
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  isDragging
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/50'
                } ${isUploading ? 'opacity-50 pointer-events-none' : 'cursor-pointer'}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => !isUploading && fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".skill,.zip"
                  onChange={handleFileInputChange}
                  className="hidden"
                  disabled={isUploading}
                />

                {selectedFile ? (
                  <div className="space-y-3">
                    <FileArchive className="h-12 w-12 mx-auto text-primary" />
                    <div>
                      <p className="font-medium">{selectedFile.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {(selectedFile.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <Upload className="h-12 w-12 mx-auto text-muted-foreground" />
                    <div>
                      <p className="font-medium">{t('file.dropHere')}</p>
                      <p className="text-sm text-muted-foreground">
                        {t('file.orClickToBrowse')}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Error Message */}
              {uploadError && (
                <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg dark:bg-red-950 dark:border-red-800">
                  <XCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-red-800 dark:text-red-200">{t('status.importFailed')}</p>
                    <p className="text-sm text-red-600 dark:text-red-400">{uploadError}</p>
                  </div>
                </div>
              )}

              {/* Success Message */}
              {importResult && importResult.success && (
                <div className="flex items-start gap-3 p-4 bg-green-50 border border-green-200 rounded-lg dark:bg-green-950 dark:border-green-800">
                  <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-medium text-green-800 dark:text-green-200">{t('status.importSuccess')}</p>
                    <p className="text-sm text-green-600 mt-1 dark:text-green-400">{importResult.message}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="outline-success">
                        {importResult.skill_name}
                      </Badge>
                      <Badge variant="outline-info">
                        v{importResult.version}
                      </Badge>
                    </div>
                    {importResult.skipped_files && importResult.skipped_files.length > 0 && (
                      <div className="flex items-start gap-2 mt-3 p-2 bg-amber-50 border border-amber-200 rounded text-sm dark:bg-amber-950 dark:border-amber-800">
                        <AlertTriangle className="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" />
                        <div className="text-amber-700 dark:text-amber-300">
                          <p>{t('status.skippedFiles', { count: importResult.skipped_files.length })}</p>
                          <p className="text-xs mt-1 opacity-80">{t('status.skippedFilesList', { files: importResult.skipped_files.join(', ') })}</p>
                        </div>
                      </div>
                    )}
                    <Button
                      variant="link"
                      className="p-0 h-auto mt-2 text-green-700"
                      onClick={() => router.push(`/skills/${importResult.skill_name}`)}
                    >
                      {t('status.viewSkill')}
                    </Button>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3">
                {selectedFile && !importResult && (
                  <>
                    <Button
                      onClick={handleFileUpload}
                      disabled={isUploading}
                      className="flex-1"
                    >
                      {isUploading ? (
                        <>
                          <Spinner size="md" className="mr-2 text-white" />
                          {t('status.importing')}
                        </>
                      ) : (
                        <>
                          <Upload className="h-4 w-4 mr-2" />
                          {t('file.button')}
                        </>
                      )}
                    </Button>
                    <Button variant="outline" onClick={handleFileReset} disabled={isUploading}>
                      {tc('actions.cancel')}
                    </Button>
                  </>
                )}
                {importResult && importResult.success && (
                  <Button variant="outline" onClick={handleFileReset} className="flex-1">
                    {t('status.importAnother')}
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Folder Upload Tab */}
        <TabsContent value="folder">
          <Card>
            <CardHeader>
              <CardTitle>{t('folder.title')}</CardTitle>
              <CardDescription>
                {t('folder.description')}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Drop Zone */}
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  isFolderDragging
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/50"
                } ${isFolderUploading ? "opacity-50 pointer-events-none" : "cursor-pointer"}`}
                onDragOver={handleFolderDragOver}
                onDragLeave={handleFolderDragLeave}
                onDrop={handleFolderDrop}
                onClick={() => !isFolderUploading && folderInputRef.current?.click()}
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
                  disabled={isFolderUploading}
                />

                {selectedFolder ? (
                  <div className="space-y-3">
                    <FolderOpen className="h-12 w-12 mx-auto text-primary" />
                    <div>
                      <p className="font-medium">{selectedFolder.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {t('folder.filesCount', { count: selectedFolder.files.length })}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <Folder className="h-12 w-12 mx-auto text-muted-foreground" />
                    <div>
                      <p className="font-medium">{t('folder.dropHere')}</p>
                      <p className="text-sm text-muted-foreground">{t('folder.orClickToBrowse')}</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Error Message */}
              {folderError && (
                <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg dark:bg-red-950 dark:border-red-800">
                  <XCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-red-800 dark:text-red-200">{t('status.importFailed')}</p>
                    <p className="text-sm text-red-600 dark:text-red-400">{folderError}</p>
                  </div>
                </div>
              )}

              {/* Success Message */}
              {folderResult && folderResult.success && (
                <div className="flex items-start gap-3 p-4 bg-green-50 border border-green-200 rounded-lg dark:bg-green-950 dark:border-green-800">
                  <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-medium text-green-800 dark:text-green-200">
                      {t('status.importSuccess')}
                    </p>
                    <p className="text-sm text-green-600 mt-1 dark:text-green-400">
                      {folderResult.message}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="outline-success">{folderResult.skill_name}</Badge>
                      <Badge variant="outline-info">v{folderResult.version}</Badge>
                    </div>
                    {folderResult.skipped_files && folderResult.skipped_files.length > 0 && (
                      <div className="flex items-start gap-2 mt-3 p-2 bg-amber-50 border border-amber-200 rounded text-sm dark:bg-amber-950 dark:border-amber-800">
                        <AlertTriangle className="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" />
                        <div className="text-amber-700 dark:text-amber-300">
                          <p>{t('status.skippedFiles', { count: folderResult.skipped_files.length })}</p>
                          <p className="text-xs mt-1 opacity-80">{t('status.skippedFilesList', { files: folderResult.skipped_files.join(', ') })}</p>
                        </div>
                      </div>
                    )}
                    <Button
                      variant="link"
                      className="p-0 h-auto mt-2 text-green-700"
                      onClick={() => router.push(`/skills/${folderResult.skill_name}`)}
                    >
                      {t('status.viewSkill')}
                    </Button>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3">
                {selectedFolder && !folderResult && (
                  <>
                    <Button
                      onClick={handleFolderUpload}
                      disabled={isFolderUploading}
                      className="flex-1"
                    >
                      {isFolderUploading ? (
                        <>
                          <Spinner size="md" className="mr-2 text-white" />
                          {t('status.importing')}
                        </>
                      ) : (
                        <>
                          <Upload className="h-4 w-4 mr-2" />
                          {t('folder.button')}
                        </>
                      )}
                    </Button>
                    <Button variant="outline" onClick={handleFolderReset} disabled={isFolderUploading}>
                      {tc('actions.cancel')}
                    </Button>
                  </>
                )}
                {folderResult && folderResult.success && (
                  <Button variant="outline" onClick={handleFolderReset} className="flex-1">
                    {t('status.importAnother')}
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Info Card */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">{t('about.title')}</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p dangerouslySetInnerHTML={{ __html: t('about.description') }} />
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li dangerouslySetInnerHTML={{ __html: t('about.skillMd') }} />
            <li dangerouslySetInnerHTML={{ __html: t('about.scripts') }} />
            <li dangerouslySetInnerHTML={{ __html: t('about.references') }} />
            <li dangerouslySetInnerHTML={{ __html: t('about.assets') }} />
            <li dangerouslySetInnerHTML={{ __html: t('about.schema') }} />
          </ul>
          <p className="pt-2">
            {t('about.conflictNote')}
          </p>
        </CardContent>
      </Card>

      {/* Conflict Dialog */}
      <Dialog open={conflictDialogOpen} onOpenChange={setConflictDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              {t('conflict.title')}
            </DialogTitle>
            <DialogDescription dangerouslySetInnerHTML={{
              __html: t('conflict.description', {
                name: conflictInfo?.skillName ?? '',
                version: conflictInfo?.existingVersion ?? '',
                interpolation: { escapeValue: false }
              })
            }} />
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm text-muted-foreground">
              {t('conflict.question')}
            </p>
          </div>
          <DialogFooter className="flex-col sm:flex-row gap-2">
            <Button
              variant="outline"
              onClick={handleCancelConflict}
              disabled={isImporting}
              className="sm:flex-1"
            >
              {tc('actions.cancel')}
            </Button>
            <Button
              onClick={handleCreateCopy}
              disabled={isImporting}
              className="sm:flex-1"
            >
              {isImporting ? (
                <>
                  <Spinner size="md" className="mr-2 text-white" />
                  {t('conflict.creating')}
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4 mr-2" />
                  {t('conflict.createCopy')}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
