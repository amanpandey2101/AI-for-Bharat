import api from "@/lib/axios";

export const login = async (email: string, password: string) => {
  return api.post("/auth/login", { email, password });
};
