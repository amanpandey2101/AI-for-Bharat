import axios from "axios";

const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000",
    withCredentials: true,
    headers: {
        "Content-Type": "application/json",
    },
});

// Allow setting the access token externally (from NextAuth session)
let _accessToken: string | null = null;

export function setAccessToken(token: string | null) {
    _accessToken = token;
}

api.interceptors.request.use(
    (config) => {
        // Attach backend access token if available
        if (_accessToken) {
            config.headers["Authorization"] = `Bearer ${_accessToken}`;
            console.log(`[API] ➡️ ${config.method?.toUpperCase()} ${config.url} (token attached)`);
        } else {
            console.log(`[API] ➡️ ${config.method?.toUpperCase()} ${config.url} (no token)`);
        }
        return config;
    },
    (error) => {
        console.error("[API] ❌ Request setup error:", error);
        return Promise.reject(error);
    }
);

api.interceptors.response.use(
    (response) => {
        console.log(`[API] ✅ ${response.status} ${response.config.method?.toUpperCase()} ${response.config.url}`);
        return response;
    },
    (error) => {
        const status = error.response?.status;
        const url = error.config?.url;

        console.error(`[API] ❌ ${status} ${error.config?.method?.toUpperCase()} ${url}`, {
            data: error.response?.data,
            message: error.message,
        });

        return Promise.reject(error);
    }
);

export default api;