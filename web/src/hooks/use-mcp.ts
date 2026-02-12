'use client';

import { useQuery } from '@tanstack/react-query';
import { mcpApi } from '@/lib/api';

// Query keys
export const mcpKeys = {
  all: ['mcp'] as const,
  servers: () => [...mcpKeys.all, 'servers'] as const,
  server: (name: string) => [...mcpKeys.all, 'server', name] as const,
};

// List all MCP servers
export function useMCPServers() {
  return useQuery({
    queryKey: mcpKeys.servers(),
    queryFn: () => mcpApi.listServers(),
  });
}

// Get MCP server detail
export function useMCPServer(name: string) {
  return useQuery({
    queryKey: mcpKeys.server(name),
    queryFn: () => mcpApi.getServer(name),
    enabled: !!name,
  });
}
