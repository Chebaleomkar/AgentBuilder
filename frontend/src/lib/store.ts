import { create } from 'zustand';
import { Agent, Workflow, Execution, Tool } from './api';

interface AppStore {
    // Agents
    agents: Agent[];
    selectedAgent: Agent | null;
    setAgents: (agents: Agent[]) => void;
    setSelectedAgent: (agent: Agent | null) => void;

    // Workflows
    workflows: Workflow[];
    selectedWorkflow: Workflow | null;
    setWorkflows: (workflows: Workflow[]) => void;
    setSelectedWorkflow: (workflow: Workflow | null) => void;

    // Tools
    tools: Tool[];
    setTools: (tools: Tool[]) => void;

    // Executions
    executions: Execution[];
    currentExecution: Execution | null;
    setExecutions: (executions: Execution[]) => void;
    setCurrentExecution: (execution: Execution | null) => void;

    // UI State
    sidebarOpen: boolean;
    toggleSidebar: () => void;
}

export const useAppStore = create<AppStore>((set) => ({
    // Agents
    agents: [],
    selectedAgent: null,
    setAgents: (agents) => set({ agents }),
    setSelectedAgent: (agent) => set({ selectedAgent: agent }),

    // Workflows
    workflows: [],
    selectedWorkflow: null,
    setWorkflows: (workflows) => set({ workflows }),
    setSelectedWorkflow: (workflow) => set({ selectedWorkflow: workflow }),

    // Tools
    tools: [],
    setTools: (tools) => set({ tools }),

    // Executions
    executions: [],
    currentExecution: null,
    setExecutions: (executions) => set({ executions }),
    setCurrentExecution: (execution) => set({ currentExecution: execution }),

    // UI State
    sidebarOpen: true,
    toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}));
