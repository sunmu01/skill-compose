'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Plus, Search, Upload, ArrowUpDown, LayoutGrid, List } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ErrorBanner } from '@/components/ui/error-banner';
import { SkillList } from '@/components/skill/skill-list';
import { UnregisteredSkillsBanner } from '@/components/skill/unregistered-skills-banner';
import { useSkills, useCategories } from '@/hooks/use-skills';
import { useTranslation } from '@/i18n/client';
import { SKILL_VIEW_MODE_KEY } from '@/lib/constants';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export type ViewMode = 'grid' | 'list';

export default function SkillsPage() {
  const { t } = useTranslation('skills');
  const { t: tc } = useTranslation('common');

  const [searchQuery, setSearchQuery] = useState('');
  const [sortIndex, setSortIndex] = useState('0');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');

  // Load viewMode from localStorage on mount (avoid SSR hydration mismatch)
  useEffect(() => {
    const stored = localStorage.getItem(SKILL_VIEW_MODE_KEY);
    if (stored === 'list' || stored === 'grid') {
      setViewMode(stored);
    }
  }, []);

  const handleViewModeChange = (mode: ViewMode) => {
    setViewMode(mode);
    localStorage.setItem(SKILL_VIEW_MODE_KEY, mode);
  };

  const SORT_OPTIONS = [
    { label: t('list.sortOptions.recentlyUpdated'), sort_by: 'updated_at', sort_order: 'desc' },
    { label: t('list.sortOptions.name'), sort_by: 'name', sort_order: 'asc' },
    { label: t('list.sortOptions.nameDesc'), sort_by: 'name', sort_order: 'desc' },
    { label: t('list.sortOptions.newest'), sort_by: 'created_at', sort_order: 'desc' },
    { label: t('list.sortOptions.oldest'), sort_by: 'created_at', sort_order: 'asc' },
  ];

  const sort = SORT_OPTIONS[Number(sortIndex)] || SORT_OPTIONS[0];

  const { data, isLoading, error } = useSkills({
    category: selectedCategory || undefined,
    sort_by: sort.sort_by,
    sort_order: sort.sort_order,
  });
  const { data: allCategories } = useCategories();

  const filteredSkills = data?.skills.filter(
    (skill) =>
      skill.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      skill.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col min-h-screen">
      {/* Main Content */}
      <main className="flex-1 container px-4 py-8">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold">{t('title')}</h1>
            <p className="text-muted-foreground mt-1">
              {t('description')}
            </p>
          </div>
          <div className="flex gap-2">
            <Link href="/import">
              <Button variant="outline">
                <Upload className="mr-2 h-4 w-4" />
                {tc('actions.import')}
              </Button>
            </Link>
            <Link href="/skills/new">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                {tc('actions.create')}
              </Button>
            </Link>
          </div>
        </div>

        {/* Search, Sort, Category, and View Toggle */}
        <div className="flex flex-col gap-4 mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={t('list.searchPlaceholder')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            {/* Category Filter */}
            <Select
              value={selectedCategory || '__all__'}
              onValueChange={(val) => setSelectedCategory(val === '__all__' ? '' : val)}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder={t('list.allCategories')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">{t('list.allCategories')}</SelectItem>
                {(allCategories || []).map((cat) => (
                  <SelectItem key={cat} value={cat}>
                    {cat}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={sortIndex} onValueChange={setSortIndex}>
              <SelectTrigger className="w-[180px]">
                <ArrowUpDown className="mr-2 h-4 w-4" />
                <SelectValue placeholder={t('list.sortBy')} />
              </SelectTrigger>
              <SelectContent>
                {SORT_OPTIONS.map((opt, i) => (
                  <SelectItem key={i} value={String(i)}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {/* View Mode Toggle */}
            <div className="flex border rounded-md">
              <Button
                variant={viewMode === 'grid' ? 'default' : 'ghost'}
                size="icon"
                className="h-9 w-9 rounded-r-none"
                onClick={() => handleViewModeChange('grid')}
                title={t('list.viewGrid')}
              >
                <LayoutGrid className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === 'list' ? 'default' : 'ghost'}
                size="icon"
                className="h-9 w-9 rounded-l-none"
                onClick={() => handleViewModeChange('list')}
                title={t('list.viewList')}
              >
                <List className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Unregistered Skills Banner */}
        <UnregisteredSkillsBanner />

        {/* Error State */}
        {error && (
          <ErrorBanner title={tc('errors.generic')} message={(error as Error).message} className="mb-6" />
        )}

        {/* Skills Grid/List */}
        <SkillList skills={filteredSkills || []} isLoading={isLoading} viewMode={viewMode} />

        {/* Stats */}
        {data && (
          <div className="mt-8 text-sm text-muted-foreground">
            {t('list.title')}: {filteredSkills?.length || 0} / {data.total}
          </div>
        )}
      </main>
    </div>
  );
}
