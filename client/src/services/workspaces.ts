import api from "@/lib/axios";

export interface ConnectedResource {
    platform: string;
    resource_id: string;
    resource_name: string;
    resource_type: string;
    connected_at: string;
}

export interface WorkspaceMember {
    user_id: string;
    role: string;
    joined_at: string;
}

export interface Workspace {
    workspace_id: string;
    name: string;
    description: string;
    owner_id: string;
    resources: ConnectedResource[];
    members: WorkspaceMember[];
    created_at: string;
    updated_at: string;
}

export const getWorkspaces = () =>
    api.get<{ workspaces: Workspace[]; total: number }>("/workspaces/");

export const getWorkspace = (id: string) =>
    api.get<{ workspace: Workspace }>(`/workspaces/${id}`);

export const createWorkspace = (name: string, description: string = "") =>
    api.post<{ workspace: Workspace }>("/workspaces/", { name, description });

export const updateWorkspace = (id: string, data: { name?: string; description?: string }) =>
    api.patch<{ workspace: Workspace }>(`/workspaces/${id}`, data);

export const deleteWorkspace = (id: string) =>
    api.delete(`/workspaces/${id}`);

export const addResource = (
    workspaceId: string,
    platform: string,
    resource_id: string,
    resource_name: string,
    resource_type: string = "repository"
) =>
    api.post<{ workspace: Workspace }>(`/workspaces/${workspaceId}/resources`, {
        platform,
        resource_id,
        resource_name,
        resource_type,
    });

export const removeResource = (
    workspaceId: string,
    platform: string,
    resource_id: string
) =>
    api.delete(`/workspaces/${workspaceId}/resources`, {
        data: { platform, resource_id },
    });

export const getWorkspaceResources = (workspaceId: string, platform?: string) => {
    const params: Record<string, string> = {};
    if (platform) params.platform = platform;
    return api.get<{ resources: ConnectedResource[]; total: number }>(
        `/workspaces/${workspaceId}/resources`,
        { params }
    );
};

export const getWorkspaceDecisions = (workspaceId: string, status?: string, limit = 50) => {
    const params: Record<string, string | number> = { limit };
    if (status) params.status = status;
    return api.get(`/workspaces/${workspaceId}/decisions`, { params });
};
