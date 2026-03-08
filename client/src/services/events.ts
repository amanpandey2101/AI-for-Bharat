import api from "@/lib/axios";

export interface ActivityEvent {
    event_id: string;
    platform: string;
    event_type: string;
    title: string;
    status: string;
    timestamp: string;
    author: string | null;
    repository: string;
}

export const getEvents = async (
    workspaceId: string,
    platform?: string,
    limit: number = 20,
    offset: number = 0
) => {
    const params: Record<string, string | number> = { limit, offset };
    if (platform && platform !== "all") params.platform = platform;
    return api.get<{ count: number; total: number; has_more: boolean; events: ActivityEvent[] }>(`/workspaces/${workspaceId}/events`, { params });
};
