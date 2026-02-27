import api from "@/lib/axios";

export const login = async (email: string, password: string) => {
  return api.post("/auth/login", { email, password });
};

export const getMe = async () => {
  return api.get("/auth/me")
}

export const register = async (email: string, password: string, name: string
) => {
  return api.post("/auth/register", { email, password, name });

}
