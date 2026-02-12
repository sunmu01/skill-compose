'use client';

import { FileBrowser } from '@/components/files/file-browser';
import { useTranslation } from '@/i18n/client';

export default function FilesPage() {
  const { t } = useTranslation('files');

  return (
    <div className="container mx-auto py-6 px-4">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">{t('title')}</h1>
        <p className="text-muted-foreground">
          {t('description')}
        </p>
      </div>

      <FileBrowser />
    </div>
  );
}
