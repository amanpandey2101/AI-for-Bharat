import api from "@/lib/axios";

export interface Integration {
    platform: string;
    status: string;
    platform_username: string | null;
    connected_resources: number;
    resources: {
        id: string;
        name: string;
        webhook_active: boolean;
    }[];
    created_at: string;
}

export interface Repo {
    id: string;
    full_name: string;
    name: string;
    private?: boolean;
    owner?: string;
    url?: string;
}

export interface SlackChannel {
    id: string;
    name: string;
    is_private: boolean;
    num_members: number;
}

export interface JiraProject {
    id: string;
    key: string;
    name: string;
    url?: string;
}

export const getIntegrations = async () => {
    return api.get<{ integrations: Integration[] }>("/integrations/");
};

export const getGitHubRepos = async () => {
    return api.get<{ repos: Repo[] }>("/integrations/github/repos");
};

export const selectGitHubRepos = async (
    resource_ids: string[],
    resource_names: string[]
) => {
    return api.post("/integrations/github/repos", {
        resource_ids,
        resource_names,
    });
};

export const getGitLabRepos = async () => {
    return api.get<{ repos: Repo[] }>("/integrations/gitlab/repos");
};

export const selectGitLabRepos = async (
    resource_ids: string[],
    resource_names: string[]
) => {
    return api.post("/integrations/gitlab/repos", {
        resource_ids,
        resource_names,
    });
};

export const getSlackChannels = async () => {
    return api.get<{ channels: SlackChannel[] }>("/integrations/slack/channels");
};

export const selectSlackChannels = async (
    resource_ids: string[],
    resource_names: string[]
) => {
    return api.post("/integrations/slack/channels", {
        resource_ids,
        resource_names,
    });
};

export const getJiraProjects = async () => {
    return api.get<{ projects: JiraProject[] }>("/integrations/jira/projects");
};

export const selectJiraProjects = async (
    resource_ids: string[],
    resource_names: string[]
) => {
    return api.post("/integrations/jira/projects", {
        resource_ids,
        resource_names,
    });
};

export const disconnectPlatform = async (platform: string) => {
    return api.delete(`/integrations/${platform}`);
};
