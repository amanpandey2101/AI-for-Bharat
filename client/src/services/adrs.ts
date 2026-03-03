import api from "@/lib/axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000";

export interface ADR {
    adr_id: string;
    title: string;
    context: string;
    decision: string;
    consequences: string;
    status: string;
    created_at: string;
    updated_at: string;
    created_by: string;
}

export const getADRs = async (workspaceId: string) => {
    return api.get(`/workspaces/${workspaceId}/adrs`);
};

export const getADR = async (workspaceId: string, adrId: string) => {
    return api.get(`/workspaces/${workspaceId}/adrs/${adrId}`);
};

export const createADR = async (
    workspaceId: string,
    data: {
        title: string;
        context?: string;
        decision?: string;
        consequences?: string;
        status?: string;
    }
) => {
    return api.post(`/workspaces/${workspaceId}/adrs`, data);
};

export const draftADR = async (workspaceId: string, topic: string) => {
    return api.post(`/workspaces/${workspaceId}/adrs/draft`, { topic });
};

export const updateADR = async (
    workspaceId: string,
    adrId: string,
    data: Partial<{
        title: string;
        context: string;
        decision: string;
        consequences: string;
        status: string;
    }>
) => {
    return api.patch(`/workspaces/${workspaceId}/adrs/${adrId}`, data);
};

export const deleteADR = async (workspaceId: string, adrId: string) => {
    return api.delete(`/workspaces/${workspaceId}/adrs/${adrId}`);
};

export const exportADRUrl = (workspaceId: string, adrId: string, accessToken?: string | null) => {
    // Return the direct URL with token for cross-domain auth
    const tokenParam = accessToken ? `?token=${accessToken}` : "";
    return `${API_BASE_URL}/workspaces/${workspaceId}/adrs/${adrId}/export${tokenParam}`;
};
