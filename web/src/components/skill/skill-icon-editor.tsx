'use client';

import { useState, useRef } from 'react';
import Image from 'next/image';
import {
  Upload,
  Trash2,
  FileText,
  Settings2,
  Loader2,
  MessageSquareText,
  Download,
  Network,
  SearchCheck,
  FolderPlus,
  Users,
  TrendingUp,
  FileCheck,
  RefreshCw,
  Lightbulb,
  Blocks,
  ClipboardList,
  Wand2,
  Grid3X3,
  // Additional icons for the picker
  File,
  Folder,
  Database,
  Cloud,
  Code,
  Terminal,
  Cpu,
  Zap,
  Star,
  Heart,
  BookOpen,
  Bookmark,
  Tag,
  Hash,
  AtSign,
  Mail,
  Send,
  MessageCircle,
  Bell,
  Calendar,
  Clock,
  Timer,
  Play,
  Pause,
  Music,
  Image as ImageIcon,
  Video,
  Camera,
  Mic,
  Volume2,
  Wifi,
  Bluetooth,
  Battery,
  Power,
  Settings,
  Wrench,
  Hammer,
  Scissors,
  Pencil,
  Pen,
  Edit3,
  Type,
  Bold,
  Link,
  Unlink,
  Paperclip,
  Archive,
  Trash,
  Copy,
  Clipboard,
  Check,
  X,
  Plus,
  Minus,
  AlertCircle,
  Info,
  HelpCircle,
  Eye,
  EyeOff,
  Lock,
  Unlock,
  Key,
  Shield,
  User,
  UserPlus,
  Globe,
  Map,
  MapPin,
  Navigation,
  Compass,
  Home,
  Building,
  Store,
  ShoppingCart,
  CreditCard,
  DollarSign,
  TrendingDown,
  BarChart,
  PieChart,
  Activity,
  Target,
  Award,
  Gift,
  Package,
  Box,
  Truck,
  Plane,
  Car,
  Bike,
  Train,
  Ship,
  Rocket,
  Sparkles,
  Sun,
  Moon,
  CloudRain,
  Snowflake,
  Wind,
  Umbrella,
  Coffee,
  Pizza,
  Apple,
  Leaf,
  Flower,
  Bug,
  Ghost,
  Skull,
  Smile,
  Frown,
  Meh,
  ThumbsUp,
  ThumbsDown,
  type LucideIcon,
} from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { skillsApi } from '@/lib/api';
import type { Skill } from '@/types/skill';

interface SkillIconEditorProps {
  skill: Skill;
}

// Mapping of skill names to their default Lucide icons
const SKILL_ICONS: Record<string, LucideIcon> = {
  'skill-creator': Wand2,
  'skill-evolver': TrendingUp,
  'skill-updater': RefreshCw,
  'mcp-builder': Blocks,
  'wechat2md': MessageSquareText,
  'download-video-from-url': Download,
  'ragflow': Network,
  'trace-qa': SearchCheck,
  'topic-collector': FolderPlus,
  'topic-generator': Lightbulb,
  'topic-reviewer': ClipboardList,
  'doc-coauthoring': Users,
  'article-review': FileCheck,
};

// Available icons for the picker (organized by category)
const ICON_OPTIONS: { name: string; icon: LucideIcon }[] = [
  // Creation & Editing
  { name: 'Wand2', icon: Wand2 },
  { name: 'Sparkles', icon: Sparkles },
  { name: 'Lightbulb', icon: Lightbulb },
  { name: 'Pencil', icon: Pencil },
  { name: 'Pen', icon: Pen },
  { name: 'Edit3', icon: Edit3 },
  { name: 'Plus', icon: Plus },
  // Files & Documents
  { name: 'File', icon: File },
  { name: 'FileText', icon: FileText },
  { name: 'FileCheck', icon: FileCheck },
  { name: 'Folder', icon: Folder },
  { name: 'FolderPlus', icon: FolderPlus },
  { name: 'Archive', icon: Archive },
  { name: 'Clipboard', icon: Clipboard },
  { name: 'ClipboardList', icon: ClipboardList },
  { name: 'BookOpen', icon: BookOpen },
  { name: 'Bookmark', icon: Bookmark },
  // Communication
  { name: 'MessageSquareText', icon: MessageSquareText },
  { name: 'MessageCircle', icon: MessageCircle },
  { name: 'Mail', icon: Mail },
  { name: 'Send', icon: Send },
  { name: 'Bell', icon: Bell },
  // Tech & Development
  { name: 'Code', icon: Code },
  { name: 'Terminal', icon: Terminal },
  { name: 'Cpu', icon: Cpu },
  { name: 'Database', icon: Database },
  { name: 'Network', icon: Network },
  { name: 'Cloud', icon: Cloud },
  { name: 'Blocks', icon: Blocks },
  { name: 'Box', icon: Box },
  { name: 'Package', icon: Package },
  // Actions
  { name: 'Download', icon: Download },
  { name: 'Upload', icon: Upload },
  { name: 'RefreshCw', icon: RefreshCw },
  { name: 'Play', icon: Play },
  { name: 'Zap', icon: Zap },
  { name: 'Rocket', icon: Rocket },
  { name: 'Target', icon: Target },
  // Analysis & Search
  { name: 'SearchCheck', icon: SearchCheck },
  { name: 'Eye', icon: Eye },
  { name: 'Activity', icon: Activity },
  { name: 'BarChart', icon: BarChart },
  { name: 'PieChart', icon: PieChart },
  { name: 'TrendingUp', icon: TrendingUp },
  { name: 'TrendingDown', icon: TrendingDown },
  // Organization
  { name: 'Tag', icon: Tag },
  { name: 'Hash', icon: Hash },
  { name: 'Link', icon: Link },
  { name: 'Paperclip', icon: Paperclip },
  { name: 'Calendar', icon: Calendar },
  { name: 'Clock', icon: Clock },
  // People & Collaboration
  { name: 'User', icon: User },
  { name: 'Users', icon: Users },
  { name: 'UserPlus', icon: UserPlus },
  // Status & Feedback
  { name: 'Check', icon: Check },
  { name: 'Star', icon: Star },
  { name: 'Award', icon: Award },
  { name: 'ThumbsUp', icon: ThumbsUp },
  { name: 'AlertCircle', icon: AlertCircle },
  { name: 'Info', icon: Info },
  { name: 'HelpCircle', icon: HelpCircle },
  // Security
  { name: 'Lock', icon: Lock },
  { name: 'Key', icon: Key },
  { name: 'Shield', icon: Shield },
  // Tools
  { name: 'Settings', icon: Settings },
  { name: 'Settings2', icon: Settings2 },
  { name: 'Wrench', icon: Wrench },
  { name: 'Hammer', icon: Hammer },
  // Media
  { name: 'Image', icon: ImageIcon },
  { name: 'Video', icon: Video },
  { name: 'Camera', icon: Camera },
  { name: 'Music', icon: Music },
  { name: 'Mic', icon: Mic },
  // Navigation
  { name: 'Globe', icon: Globe },
  { name: 'Map', icon: Map },
  { name: 'MapPin', icon: MapPin },
  { name: 'Compass', icon: Compass },
  { name: 'Home', icon: Home },
  // Nature & Weather
  { name: 'Sun', icon: Sun },
  { name: 'Moon', icon: Moon },
  { name: 'Leaf', icon: Leaf },
  { name: 'Bug', icon: Bug },
  // Misc
  { name: 'Heart', icon: Heart },
  { name: 'Gift', icon: Gift },
  { name: 'Coffee', icon: Coffee },
  { name: 'Smile', icon: Smile },
];

// Helper to get the full icon URL with cache busting
function getIconUrl(iconUrl: string | null, updatedAt?: string): string | null {
  if (!iconUrl) return null;
  let url = iconUrl;
  if (!iconUrl.startsWith('http://') && !iconUrl.startsWith('https://')) {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:62610';
    const cleanBaseUrl = baseUrl.replace(/\/api\/v1\/?$/, '').replace(/\/$/, '');
    url = `${cleanBaseUrl}${iconUrl}`;
  }
  // Add cache busting param
  if (updatedAt) {
    const cacheBuster = new Date(updatedAt).getTime();
    url += `?v=${cacheBuster}`;
  }
  return url;
}

// Convert Lucide icon to SVG File by rendering to DOM and extracting
async function iconToSvgFile(IconComponent: LucideIcon, color: string = '#3B82F6'): Promise<File> {
  // Create a temporary container
  const tempDiv = document.createElement('div');
  tempDiv.style.position = 'absolute';
  tempDiv.style.left = '-9999px';
  document.body.appendChild(tempDiv);

  // Import dynamically to avoid SSR issues
  const { createRoot } = await import('react-dom/client');
  const React = await import('react');

  return new Promise((resolve) => {
    const root = createRoot(tempDiv);
    root.render(
      React.createElement(IconComponent, {
        size: 128,
        color: color,
        strokeWidth: 1.5,
      })
    );

    // Wait for render, then extract SVG
    setTimeout(() => {
      const svgElement = tempDiv.querySelector('svg');
      if (svgElement) {
        // Add xmlns if not present
        if (!svgElement.getAttribute('xmlns')) {
          svgElement.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
        }
        const svgString = svgElement.outerHTML;
        const blob = new Blob([svgString], { type: 'image/svg+xml' });
        const file = new globalThis.File([blob], 'icon.svg', { type: 'image/svg+xml' });

        // Cleanup
        root.unmount();
        document.body.removeChild(tempDiv);

        resolve(file);
      } else {
        // Cleanup on failure
        root.unmount();
        document.body.removeChild(tempDiv);
        // Return empty file
        resolve(new globalThis.File([''], 'icon.svg', { type: 'image/svg+xml' }));
      }
    }, 50);
  });
}

export function SkillIconEditor({ skill }: SkillIconEditorProps) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [selecting, setSelecting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pickerOpen, setPickerOpen] = useState(false);

  const iconUrl = getIconUrl(skill.icon_url, skill.updated_at);
  const isMeta = skill.skill_type === 'meta';

  const refreshSkill = () => {
    queryClient.invalidateQueries({ queryKey: ['skill', skill.name] });
    queryClient.invalidateQueries({ queryKey: ['skills'] });
  };

  const handleUpload = async (file: File) => {
    setError(null);
    setUploading(true);
    try {
      await skillsApi.uploadIcon(skill.name, file);
      refreshSkill();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleSelectIcon = async (iconOption: { name: string; icon: LucideIcon }) => {
    setError(null);
    setSelecting(true);
    setPickerOpen(false);

    try {
      // Create SVG file from the icon
      const color = isMeta ? '#3B82F6' : '#6B7280'; // blue for meta, gray for user
      const svgFile = await iconToSvgFile(iconOption.icon, color);
      await skillsApi.uploadIcon(skill.name, svgFile);
      refreshSkill();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Selection failed');
    } finally {
      setSelecting(false);
    }
  };

  const handleDelete = async () => {
    setError(null);
    setDeleting(true);
    try {
      await skillsApi.deleteIcon(skill.name);
      refreshSkill();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delete failed');
    } finally {
      setDeleting(false);
    }
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleUpload(file);
    }
    // Reset input so same file can be selected again
    e.target.value = '';
  };

  const isLoading = uploading || selecting || deleting;

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-medium text-muted-foreground">Icon</h4>

      {/* Icon Preview */}
      <div className="flex items-start gap-4">
        <div className={`relative w-16 h-16 border rounded-lg flex items-center justify-center overflow-hidden flex-shrink-0 ${isMeta ? 'bg-primary/10' : 'bg-muted/50'}`}>
          {iconUrl ? (
            <Image
              src={iconUrl}
              alt={`${skill.name} icon`}
              fill
              className="object-contain p-1"
              unoptimized
            />
          ) : (
            (() => {
              const SkillIcon = SKILL_ICONS[skill.name] || (isMeta ? Settings2 : FileText);
              return <SkillIcon className={`h-8 w-8 ${isMeta ? 'text-primary' : 'text-muted-foreground'}`} />;
            })()
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col gap-2">
          <div className="flex gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept=".png,.jpg,.jpeg,.webp,.svg"
              onChange={onFileChange}
              className="hidden"
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
            >
              {uploading ? (
                <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
              ) : (
                <Upload className="h-4 w-4 mr-1.5" />
              )}
              Upload
            </Button>

            {/* Icon Picker */}
            <Dialog open={pickerOpen} onOpenChange={setPickerOpen}>
              <DialogTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={isLoading}
                >
                  {selecting ? (
                    <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
                  ) : (
                    <Grid3X3 className="h-4 w-4 mr-1.5" />
                  )}
                  Choose
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>Choose Icon</DialogTitle>
                </DialogHeader>
                <div className="grid grid-cols-8 gap-1 max-h-72 overflow-y-auto p-1">
                  {ICON_OPTIONS.map((option) => {
                    const Icon = option.icon;
                    return (
                      <button
                        key={option.name}
                        className="p-2 rounded hover:bg-muted transition-colors"
                        onClick={() => handleSelectIcon(option)}
                        title={option.name}
                      >
                        <Icon className="h-5 w-5" />
                      </button>
                    );
                  })}
                </div>
              </DialogContent>
            </Dialog>

            {iconUrl && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleDelete}
                disabled={isLoading}
                className="text-destructive hover:text-destructive"
              >
                {deleting ? (
                  <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4 mr-1.5" />
                )}
                Delete
              </Button>
            )}
          </div>
          <p className="text-xs text-muted-foreground">
            Upload image or choose an icon
          </p>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}
    </div>
  );
}
