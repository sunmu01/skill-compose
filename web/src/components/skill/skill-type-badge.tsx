import { Badge } from "@/components/ui/badge";

export function SkillTypeBadge({ skillType }: { skillType?: string }) {
  if (skillType === 'meta') {
    return (
      <Badge variant="outline-purple">
        Meta
      </Badge>
    );
  }
  return (
    <Badge variant="outline-info">
      User
    </Badge>
  );
}
