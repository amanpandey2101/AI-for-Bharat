import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000";

const api = axios.create({
    baseURL: API_BASE_URL,
    withCredentials: true,
});

export const sendMessage = async (workspaceId: string, message: string, sessionId?: string | null) => {
    return api.post(`/chat/workspaces/${workspaceId}`, {
        message,
        session_id: sessionId,
    });
};

export const sendMessageStream = async (workspaceId: string, message: string, sessionId?: string | null) => {
    return fetch(`${API_BASE_URL}/chat/workspaces/${workspaceId}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            message,
            session_id: sessionId,
        }),
        // Ensure credentials are sent for CORS/cookies if needed
        credentials: "include"
    });
};

