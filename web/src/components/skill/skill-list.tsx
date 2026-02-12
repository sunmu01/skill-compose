'use client';

import { FileText, Pin } from 'lucide-react';
import { SkillCard } from './skill-card';
import { SkillListItem } from './skill-list-item';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { Badge } from '@/components/ui/badge';
import type { Skill } from '@/types/skill';
import type { ViewMode } from '@/app/skills/page';
import { useTranslation } from '@/i18n/client';

interface SkillListProps {
  skills: Skill[];
  isLoading?: boolean;
  viewMode?: ViewMode;
}

export function SkillList({ skills, isLoading, viewMode = 'grid' }: SkillListProps) {
  const { t } = useTranslation('skills');

  if (isLoading) {
    return <LoadingSkeleton variant="card-grid" count={6} />;
  }

  if (skills.length === 0) {
    return (
      <EmptyState
        icon={FileText}
        title={t('list.empty')}
        description={t('list.emptyDescription')}
      />
    );
  }

  // Separate user and meta skills (treat undefined as 'user')
  const userSkills = skills.filter((s) => !s.skill_type || s.skill_type !== 'meta');
  const metaSkills = skills.filter((s) => s.skill_type === 'meta');

  // Sort meta skills: skill-creator first, then skill-updater, then skill-evolver
  const metaSkillOrder = ['skill-creator', 'skill-updater', 'skill-evolver'];
  const sortedMetaSkills = [...metaSkills].sort((a, b) => {
    const aIndex = metaSkillOrder.indexOf(a.name);
    const bIndex = metaSkillOrder.indexOf(b.name);
    if (aIndex === -1 && bIndex === -1) return a.name.localeCompare(b.name);
    if (aIndex === -1) return 1;
    if (bIndex === -1) return -1;
    return aIndex - bIndex;
  });

  // Separate pinned and unpinned user skills (backend already sorts pinned first,
  // but we separate them here for visual grouping)
  const pinnedUserSkills = userSkills.filter((s) => s.is_pinned);
  const unpinnedUserSkills = userSkills.filter((s) => !s.is_pinned);

  const renderGrid = (items: Skill[]) => (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {items.map((skill) => (
        <SkillCard key={skill.id} skill={skill} />
      ))}
    </div>
  );

  const renderList = (items: Skill[]) => (
    <div className="space-y-2">
      {items.map((skill) => (
        <SkillListItem key={skill.id} skill={skill} />
      ))}
    </div>
  );

  const renderItems = viewMode === 'grid' ? renderGrid : renderList;

  return (
    <div className="space-y-8">
      {/* Meta Skills - shown first */}
      {sortedMetaSkills.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-4 text-muted-foreground">{t('list.metaSkills')}</h2>
          {renderItems(sortedMetaSkills)}
        </div>
      )}

      {/* Pinned User Skills */}
      {pinnedUserSkills.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Pin className="h-4 w-4" />
            {t('list.pinned')}
          </h2>
          {renderItems(pinnedUserSkills)}
        </div>
      )}

      {/* User Skills */}
      {unpinnedUserSkills.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-4">{t('list.userSkills')}</h2>
          {renderItems(unpinnedUserSkills)}
        </div>
      )}
    </div>
  );
}
