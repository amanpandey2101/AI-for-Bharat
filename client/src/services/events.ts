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
    limit: number = 50
) => {
    const params: Record<string, string | number> = { limit };
    if (platform) params.platform = platform;
    return api.get<{ count: number; events: ActivityEvent[] }>(`/workspaces/${workspaceId}/events`, { params });
};
