import api from "@/lib/axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000";

export const sendMessage = async (workspaceId: string, message: string, sessionId?: string | null) => {
    return api.post(`/chat/workspaces/${workspaceId}`, {
        message,
        session_id: sessionId,
    });
};

export const sendMessageStream = async (workspaceId: string, message: string, sessionId?: string | null, accessToken?: string | null) => {
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
    };
    if (accessToken) {
        headers["Authorization"] = `Bearer ${accessToken}`;
    }

    return fetch(`${API_BASE_URL}/chat/workspaces/${workspaceId}`, {
        method: "POST",
        headers,
        body: JSON.stringify({
            message,
            session_id: sessionId,
        }),
        credentials: "include",
    });
};
