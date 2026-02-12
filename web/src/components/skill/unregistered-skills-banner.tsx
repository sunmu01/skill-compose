'use client';

import { useState } from 'react';
import { Info, X, Download, CheckSquare, Square } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Spinner } from '@/components/ui/spinner';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { useUnregisteredSkills, skillKeys } from '@/hooks/use-skills';
import { skillsApi } from '@/lib/api';
import { useQueryClient } from '@tanstack/react-query';

export function UnregisteredSkillsBanner() {
  const { data, isLoading } = useUnregisteredSkills();
  const [dismissed, setDismissed] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<{
    total_imported: number;
    total_failed: number;
    results: Array<{ name: string; success: boolean; error?: string }>;
  } | null>(null);
  const queryClient = useQueryClient();

  if (isLoading || dismissed || !data || data.total === 0) {
    return null;
  }

  const skills = data.skills;
  const allSelected = selected.size === skills.length;

  const toggleSelect = (name: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  const toggleAll = () => {
    if (allSelected) {
      setSelected(new Set());
    } else {
      setSelected(new Set(skills.map((s) => s.name)));
    }
  };

  const openDialog = () => {
    setSelected(new Set(skills.map((s) => s.name)));
    setImportResult(null);
    setDialogOpen(true);
  };

  const handleImport = async () => {
    if (selected.size === 0) return;
    setImporting(true);
    try {
      const result = await skillsApi.importLocal(Array.from(selected));
      setImportResult(result);
      if (result.total_imported > 0) {
        queryClient.invalidateQueries({ queryKey: skillKeys.lists() });
        queryClient.invalidateQueries({ queryKey: [...skillKeys.all, 'unregistered'] });
      }
      if (result.total_failed === 0) {
        // All succeeded - close dialog and hide banner
        setDialogOpen(false);
        setDismissed(true);
      }
    } catch {
      setImportResult({
        total_imported: 0,
        total_failed: selected.size,
        results: Array.from(selected).map((name) => ({
          name,
          success: false,
          error: 'Network error',
        })),
      });
    } finally {
      setImporting(false);
    }
  };

  return (
    <>
      <div className="rounded-lg border border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950/50 p-4 flex items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <Info className="h-5 w-5 text-blue-600 dark:text-blue-400 shrink-0" />
          <p className="text-sm text-blue-800 dark:text-blue-200">
            <span className="font-medium">{data.total} unregistered skill{data.total !== 1 ? 's' : ''}</span> found on disk.
            These exist in the skills directory but are not in the database.
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="outline" size="sm" onClick={openDialog}>
            <Download className="mr-2 h-4 w-4" />
            View & Import
          </Button>
          <button
            onClick={() => setDismissed(true)}
            className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>Import Local Skills</DialogTitle>
            <DialogDescription>
              Select skills to import into the database. These skills exist on disk but are not registered.
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto space-y-1 min-h-0">
            {/* Select All */}
            <button
              type="button"
              onClick={toggleAll}
              className="flex items-center gap-3 w-full px-3 py-2 rounded-md hover:bg-muted text-sm font-medium"
            >
              {allSelected ? (
                <CheckSquare className="h-4 w-4 text-primary" />
              ) : (
                <Square className="h-4 w-4 text-muted-foreground" />
              )}
              Select All ({skills.length})
            </button>

            <div className="border-t my-1" />

            {/* Skill list */}
            {skills.map((skill) => (
              <button
                key={skill.name}
                type="button"
                onClick={() => toggleSelect(skill.name)}
                className="flex items-center gap-3 w-full px-3 py-2 rounded-md hover:bg-muted text-left"
              >
                {selected.has(skill.name) ? (
                  <CheckSquare className="h-4 w-4 text-primary shrink-0" />
                ) : (
                  <Square className="h-4 w-4 text-muted-foreground shrink-0" />
                )}
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium truncate">{skill.name}</span>
                    {skill.skill_type === 'meta' && (
                      <Badge variant="secondary" className="text-xs">meta</Badge>
                    )}
                  </div>
                  {skill.description && (
                    <p className="text-xs text-muted-foreground truncate">{skill.description}</p>
                  )}
                </div>
              </button>
            ))}
          </div>

          {/* Import results */}
          {importResult && importResult.total_failed > 0 && (
            <div className="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm">
              <p className="font-medium text-destructive">
                {importResult.total_imported} imported, {importResult.total_failed} failed
              </p>
              {importResult.results
                .filter((r) => !r.success)
                .map((r) => (
                  <p key={r.name} className="text-destructive/80 mt-1">
                    {r.name}: {r.error}
                  </p>
                ))}
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleImport}
              disabled={selected.size === 0 || importing}
            >
              {importing && <Spinner size="sm" className="mr-2" />}
              Import {selected.size > 0 ? `(${selected.size})` : ''}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
