import axios from "axios";

const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000",
    withCredentials: true,
    headers: {
        "Content-Type": "application/json",
    },
});

api.interceptors.request.use(
    (config) => {
        console.log(`[API] ➡️ ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`, {
            headers: config.headers,
            withCredentials: config.withCredentials,
        });
        return config;
    },
    (error) => {
        console.error("[API] ❌ Request setup error:", error);
        return Promise.reject(error);
    }
);

api.interceptors.response.use(
    (response) => {
        console.log(`[API] ✅ ${response.status} ${response.config.method?.toUpperCase()} ${response.config.url}`, response.data);
        return response;
    },
    (error) => {
        const status = error.response?.status;
        const url = error.config?.url;
        const data = error.response?.data;

        console.error(`[API] ❌ ${status} ${error.config?.method?.toUpperCase()} ${url}`, {
            data,
            message: error.message,
        });

        if (status === 401) {
            console.warn("[API] 🔒 401 Unauthorized — cookie may be missing or blocked by browser cross-site policy");
        }

        return Promise.reject(error);
    }
);

export default api;