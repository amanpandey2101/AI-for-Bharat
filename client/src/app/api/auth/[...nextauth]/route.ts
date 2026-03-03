import NextAuth, { NextAuthOptions } from "next-auth";
import GithubProvider from "next-auth/providers/github";
import CredentialsProvider from "next-auth/providers/credentials";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000";

export const authOptions: NextAuthOptions = {
    providers: [
        GithubProvider({
            clientId: process.env.GITHUB_CLIENT_ID!,
            clientSecret: process.env.GITHUB_CLIENT_SECRET!,
            // Request wider scopes for repo + webhook management
            authorization: {
                params: {
                    scope: "repo admin:repo_hook read:org user:email",
                },
            },
        }),
        CredentialsProvider({
            name: "Credentials",
            credentials: {
                email: { label: "Email", type: "email" },
                password: { label: "Password", type: "password" },
            },
            async authorize(credentials) {
                try {
                    const res = await fetch(`${API_BASE_URL}/auth/login`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            email: credentials?.email,
                            password: credentials?.password,
                        }),
                    });

                    const data = await res.json();

                    if (!res.ok || !data.success) {
                        throw new Error(data.message || "Invalid credentials");
                    }

                    return {
                        id: data.user_id || data.access_token,
                        email: credentials?.email,
                        accessToken: data.access_token,
                    };
                } catch (error: unknown) {
                    const message = error instanceof Error ? error.message : "Login failed";
                    throw new Error(message);
                }
            },
        }),
    ],

    callbacks: {
        async jwt({ token, user, account }) {
            if (user) {
                token.accessToken = (user as { accessToken?: string }).accessToken;
            }

            // For GitHub OAuth — sync user with backend and store both tokens
            if (account?.provider === "github" && account.access_token) {
                // Store the GitHub access token for integration use
                token.githubAccessToken = account.access_token;

                try {
                    const res = await fetch(`${API_BASE_URL}/auth/github/nextauth-callback`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            github_access_token: account.access_token,
                        }),
                    });

                    if (res.ok) {
                        const data = await res.json();
                        token.accessToken = data.access_token;
                        token.userId = data.user_id;
                        token.name = data.name;
                        token.email = data.email;
                        token.picture = data.avatar_url;
                    }
                } catch (e) {
                    console.error("[NextAuth] Failed to sync GitHub user with backend:", e);
                }
            }

            return token;
        },

        async session({ session, token }) {
            if (session.user) {
                (session as { accessToken?: string }).accessToken = token.accessToken as string;
                (session as { githubAccessToken?: string }).githubAccessToken = token.githubAccessToken as string;
                session.user.name = token.name as string;
                session.user.email = token.email as string;
                session.user.image = token.picture as string;
                (session.user as { id?: string }).id = token.userId as string || token.sub;
            }
            return session;
        },
    },

    pages: {
        signIn: "/login",
    },

    session: {
        strategy: "jwt",
        maxAge: 24 * 60 * 60, // 24 hours
    },

    secret: process.env.NEXTAUTH_SECRET,
};

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };
