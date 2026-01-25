import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
    baseURL: `${API_BASE_URL}/api/v1`,
    headers: {
        'Content-Type': 'application/json',
    },
});

// ========== Agent API ==========

export interface Agent {
    id: string;
    name: string;
    role: string;
    goal?: string;
    instructions?: string;
    model: string;
    temperature: number;
    tools: string[];
    memory_type: 'session' | 'persistent' | 'knowledge';
    status: 'active' | 'inactive' | 'running' | 'error';
    created_at: string;
    updated_at: string;
}

export interface AgentCreate {
    name: string;
    role: string;
    goal?: string;
    instructions?: string;
    model?: string;
    temperature?: number;
    tools?: string[];
    memory_type?: 'session' | 'persistent' | 'knowledge';
}

export const agentApi = {
    list: async (page = 1, perPage = 20) => {
        const { data } = await api.get('/agents', { params: { page, per_page: perPage } });
        return data;
    },

    get: async (id: string) => {
        const { data } = await api.get(`/agents/${id}`);
        return data as Agent;
    },

    create: async (agent: AgentCreate) => {
        const { data } = await api.post('/agents', agent);
        return data as Agent;
    },

    update: async (id: string, updates: Partial<AgentCreate>) => {
        const { data } = await api.put(`/agents/${id}`, updates);
        return data as Agent;
    },

    delete: async (id: string) => {
        await api.delete(`/agents/${id}`);
    },

    execute: async (id: string, input: Record<string, any>) => {
        const { data } = await api.post(`/agents/${id}/execute`, { input });
        return data;
    },
};

// ========== Workflow API ==========

export interface WorkflowStep {
    id: string;
    name: string;
    type: 'agent' | 'condition' | 'parallel' | 'loop' | 'handoff';
    agent_id?: string;
    condition?: string;
    config: Record<string, any>;
    next_steps: string[];
}

export interface Workflow {
    id: string;
    name: string;
    description?: string;
    coordination_strategy: 'sequential' | 'supervisor' | 'peer' | 'conditional';
    execution_mode: 'on_demand' | 'scheduled' | 'webhook';
    steps: WorkflowStep[];
    agents: string[];
    status: 'draft' | 'active' | 'paused' | 'archived';
    created_at: string;
    updated_at: string;
}

export interface WorkflowCreate {
    name: string;
    description?: string;
    coordination_strategy?: string;
    execution_mode?: string;
    steps?: WorkflowStep[];
    agents?: string[];
}

export const workflowApi = {
    list: async (page = 1, perPage = 20) => {
        const { data } = await api.get('/workflows', { params: { page, per_page: perPage } });
        return data;
    },

    get: async (id: string) => {
        const { data } = await api.get(`/workflows/${id}`);
        return data as Workflow;
    },

    create: async (workflow: WorkflowCreate) => {
        const { data } = await api.post('/workflows', workflow);
        return data as Workflow;
    },

    update: async (id: string, updates: Partial<WorkflowCreate>) => {
        const { data } = await api.put(`/workflows/${id}`, updates);
        return data as Workflow;
    },

    delete: async (id: string) => {
        await api.delete(`/workflows/${id}`);
    },

    execute: async (id: string, input: Record<string, any>) => {
        const { data } = await api.post(`/workflows/${id}/execute`, { input });
        return data;
    },
};

// ========== Tool API ==========

export interface Tool {
    id: string;
    name: string;
    description: string;
    category: 'web' | 'rag' | 'file' | 'api' | 'data' | 'custom';
    input_schema: Record<string, any>;
    output_schema?: Record<string, any>;
    is_builtin: boolean;
    status: 'active' | 'disabled' | 'deprecated';
}

export const toolApi = {
    list: async () => {
        const { data } = await api.get('/tools');
        return data;
    },

    getBuiltin: async () => {
        const { data } = await api.get('/tools/builtin');
        return data;
    },
};

// ========== Execution API ==========

export interface ExecutionStep {
    id: string;
    step_name: string;
    step_type: string;
    agent_id?: string;
    tool_name?: string;
    input_data: Record<string, any>;
    output_data?: Record<string, any>;
    status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
    error_message?: string;
    started_at?: string;
    completed_at?: string;
    duration_ms?: number;
    tool_calls: any[];
}

export interface ExecutionLog {
    id: string;
    level: 'debug' | 'info' | 'warning' | 'error';
    message: string;
    metadata: Record<string, any>;
    source?: string;
    timestamp: string;
}

export interface Execution {
    id: string;
    agent_id?: string;
    workflow_id?: string;
    status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
    input_data: Record<string, any>;
    output_data?: Record<string, any>;
    error_message?: string;
    started_at?: string;
    completed_at?: string;
    duration_ms?: number;
    token_usage: {
        input_tokens: number;
        output_tokens: number;
        total_tokens: number;
    };
    cost_estimate?: number;
    created_at: string;
    steps?: ExecutionStep[];
    logs?: ExecutionLog[];
}

export const executionApi = {
    list: async (params?: { agent_id?: string; workflow_id?: string; status?: string; page?: number }) => {
        const { data } = await api.get('/executions', { params });
        return data;
    },

    get: async (id: string) => {
        const { data } = await api.get(`/executions/${id}`);
        return data as Execution;
    },

    cancel: async (id: string) => {
        await api.post(`/executions/${id}/cancel`);
    },
};

// ========== Demo API ==========

export const demoApi = {
    list: async () => {
        const { data } = await api.get('/demo');
        return data;
    },

    runResearch: async (topic: string, maxSources = 5) => {
        const { data } = await api.post('/demo/research', { topic, max_sources: maxSources });
        return data;
    },

    runAutomation: async (taskData: any[], task = 'analyze') => {
        const { data } = await api.post('/demo/automation', { data: taskData, task });
        return data;
    },

    runMultiAgent: async (task: string, context?: Record<string, any>) => {
        const { data } = await api.post('/demo/multi-agent', { task, context });
        return data;
    },
};
