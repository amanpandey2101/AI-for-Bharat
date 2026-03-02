import api from "@/lib/axios";

export interface Decision {
    decision_id: string;
    title: string;
    description: string;
    rationale: string;
    repository: string;
    platform: string;
    status: string;
    confidence: number;
    confidence_factors: {
        overall: number;
        evidence_quality: number;
        evidence_quantity: number;
        participant_authority: number;
        temporal_consistency: number;
        outcome_validation: number;
    };
    participants: string[];
    tags: string[];
    created_at: string;
    evidence_count: number;
}

export interface DecisionDetail extends Decision {
    alternatives_considered: string[];
    intent: Evidence[];
    execution: Evidence[];
    authority: Evidence[];
    outcomes: Evidence[];
    source_event_ids: string[];
    related_decisions: string[];
}

export interface Evidence {
    source_type: string;
    source_id: string;
    content: string;
    author: string;
    timestamp: string;
    confidence_contribution: number;
    url?: string;
}

export interface DecisionStats {
    total_decisions: number;
    by_status: Record<string, number>;
    by_platform: Record<string, number>;
    avg_confidence: number;
    pending_validation: number;
}

export const getDecisions = async (
    status?: string,
    repository?: string,
    limit: number = 50
) => {
    const params: Record<string, string | number> = { limit };
    if (status) params.status = status;
    if (repository) params.repository = repository;
    return api.get<{ decisions: Decision[]; total: number }>("/decisions/", {
        params,
    });
};

export const getDecision = async (id: string) => {
    return api.get<{ decision: DecisionDetail }>(`/decisions/${id}`);
};

export const validateDecision = async (
    id: string,
    status: "validated" | "disputed",
    comment?: string
) => {
    return api.post(`/decisions/${id}/validate`, { status, comment });
};

export const getDecisionStats = async () => {
    return api.get<DecisionStats>("/decisions/stats/overview");
};

export const deleteDecision = async (id: string) => {
    return api.delete(`/decisions/${id}`);
};
