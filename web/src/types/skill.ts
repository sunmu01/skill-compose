/**
 * TypeScript types for Skill Registry
 */

export type SkillType = 'user' | 'meta';

export interface Skill {
  id: string;
  name: string;
  description: string | null;
  owner_id: string | null;
  created_at: string;
  updated_at: string;
  current_version: string | null;
  skill_type: SkillType;
  tags: string[];
  icon_url: string | null;
  source: string | null;  // Import source URL (e.g., GitHub URL)
  author: string | null;  // Author or organization name
  category: string | null;  // Skill category
  is_pinned: boolean;  // Whether skill is pinned to top
}

export interface SkillVersion {
  id: string;
  skill_id: string;
  version: string;
  parent_version: string | null;
  skill_md: string | null;
  schema_json: Record<string, unknown> | null;
  manifest_json: SkillManifest | null;
  created_at: string;
  created_by: string | null;
  commit_message: string | null;
}

export interface SkillManifest {
  name: string;
  version: string;
  description: string;
  author?: string;
  license?: string;
  dependencies?: {
    mcp?: string[];
    tools?: string[];
    skills?: string[];
  };
  triggers?: string[];
  tags?: string[];
  created?: string;
  updated?: string;
}

export interface SkillFile {
  id: string;
  version_id: string;
  file_path: string;
  file_type: 'resource' | 'script' | 'test' | 'other';
  content_hash: string | null;
  size_bytes: number | null;
  created_at: string;
}

export interface SkillTest {
  id: string;
  version_id: string;
  name: string;
  description: string | null;
  input_data: Record<string, unknown> | null;
  expected_output: Record<string, unknown> | null;
  is_golden: boolean;
  created_at: string;
}

export interface SkillChangelog {
  id: string;
  skill_id: string;
  version_from: string | null;
  version_to: string | null;
  change_type: 'create' | 'update' | 'rollback' | 'delete';
  diff_content: string | null;
  changed_by: string | null;
  changed_at: string;
  comment: string | null;
}

// API Response types
export interface SkillListResponse {
  skills: Skill[];
  total: number;
  offset: number;
  limit: number;
}

export interface SkillDetailResponse extends Skill {
  versions?: SkillVersion[];
}

export interface VersionListResponse {
  versions: SkillVersion[];
  total: number;
}

// API Request types
export interface CreateSkillRequest {
  name: string;
  description?: string;
  skill_type?: SkillType;
  tags?: string[];
}

export interface CreateVersionRequest {
  version?: string;
  skill_md?: string;
  schema_json?: Record<string, unknown>;
  manifest_json?: SkillManifest;
  commit_message?: string;
  files_content?: Record<string, string>;
}

export interface UpdateSkillRequest {
  description?: string;
  tags?: string[];
  category?: string | null;
  status?: string;
  source?: string;
  author?: string;
}

// Tool types
export type ToolCategory = 'skill_management' | 'code_execution' | 'code_exploration' | 'mcp';

export interface Tool {
  id: string;
  name: string;
  description: string;
  category: ToolCategory;
  input_schema: Record<string, unknown>;
}

export interface ToolCategoryInfo {
  id: string;
  name: string;
  description: string;
  icon: string;
}

export interface ToolListResponse {
  tools: Tool[];
  categories: Record<string, ToolCategoryInfo>;
  total: number;
}
