'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Workflow, ArrowLeft, Save, Plus, X, Users } from 'lucide-react';
import toast from 'react-hot-toast';
import Navbar from '@/components/layout/Navbar';
import { workflowApi, agentApi, WorkflowCreate } from '@/lib/api';
import { clsx } from 'clsx';

const coordinationStrategies = [
    { id: 'sequential', name: 'Sequential', description: 'Agents run one after another' },
    { id: 'supervisor', name: 'Supervisor', description: 'One agent coordinates others' },
    { id: 'peer', name: 'Peer', description: 'Agents work in parallel' },
    { id: 'conditional', name: 'Conditional', description: 'Branch based on conditions' },
];

export default function CreateWorkflowPage() {
    const router = useRouter();

    const [formData, setFormData] = useState<WorkflowCreate>({
        name: '',
        description: '',
        coordination_strategy: 'sequential',
        agents: [],
    });

    const { data: agentsData } = useQuery({
        queryKey: ['agents'],
        queryFn: () => agentApi.list(),
    });

    const createMutation = useMutation({
        mutationFn: workflowApi.create,
        onSuccess: (data) => {
            toast.success('Workflow created successfully!');
            router.push(`/workflows/${data.id}`);
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Failed to create workflow');
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.name) {
            toast.error('Workflow name is required');
            return;
        }
        if (!formData.agents || formData.agents.length < 2) {
            toast.error('Select at least 2 agents for the workflow');
            return;
        }
        createMutation.mutate(formData);
    };

    const toggleAgent = (agentId: string) => {
        setFormData((prev) => ({
            ...prev,
            agents: prev.agents?.includes(agentId)
                ? prev.agents.filter((id) => id !== agentId)
                : [...(prev.agents || []), agentId],
        }));
    };

    return (
        <div className="min-h-screen pt-16">
            <Navbar />

            <div className="container mx-auto px-6 py-8 max-w-4xl">
                {/* Header */}
                <div className="flex items-center gap-4 mb-8">
                    <button
                        onClick={() => router.back()}
                        className="p-2 rounded-lg hover:bg-white/5 transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <h1 className="text-3xl font-bold mb-1">Create Workflow</h1>
                        <p className="text-gray-400">Design a multi-agent workflow</p>
                    </div>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="space-y-8">
                        {/* Basic Info */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="card"
                        >
                            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                                <Workflow className="w-5 h-5 text-accent-400" />
                                Workflow Details
                            </h2>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium mb-2">Workflow Name *</label>
                                    <input
                                        type="text"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        placeholder="e.g., Research & Report Pipeline"
                                        className="input"
                                        required
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium mb-2">Description</label>
                                    <textarea
                                        value={formData.description}
                                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                        placeholder="Describe what this workflow does..."
                                        className="textarea h-24"
                                    />
                                </div>
                            </div>
                        </motion.div>

                        {/* Coordination Strategy */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="card"
                        >
                            <h2 className="text-xl font-semibold mb-6">Coordination Strategy</h2>

                            <div className="grid md:grid-cols-2 gap-4">
                                {coordinationStrategies.map((strategy) => (
                                    <button
                                        key={strategy.id}
                                        type="button"
                                        onClick={() => setFormData({ ...formData, coordination_strategy: strategy.id })}
                                        className={clsx(
                                            'p-4 rounded-lg border text-left transition-all',
                                            formData.coordination_strategy === strategy.id
                                                ? 'border-accent-500 bg-accent-500/10'
                                                : 'border-white/10 hover:border-white/20'
                                        )}
                                    >
                                        <div className="font-medium mb-1">{strategy.name}</div>
                                        <div className="text-sm text-gray-400">{strategy.description}</div>
                                    </button>
                                ))}
                            </div>
                        </motion.div>

                        {/* Agent Selection */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="card"
                        >
                            <h2 className="text-xl font-semibold mb-2 flex items-center gap-2">
                                <Users className="w-5 h-5" />
                                Select Agents
                            </h2>
                            <p className="text-gray-400 text-sm mb-6">
                                Choose agents to include in this workflow (select at least 2)
                            </p>

                            {agentsData?.agents?.length === 0 ? (
                                <div className="text-center py-8">
                                    <p className="text-gray-400 mb-4">No agents found. Create some agents first.</p>
                                    <button
                                        type="button"
                                        onClick={() => router.push('/agents/create')}
                                        className="btn-primary inline-flex items-center gap-2"
                                    >
                                        <Plus className="w-4 h-4" />
                                        Create Agent
                                    </button>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    {agentsData?.agents?.map((agent: any, index: number) => {
                                        const isSelected = formData.agents?.includes(agent.id);
                                        const orderIndex = formData.agents?.indexOf(agent.id);

                                        return (
                                            <button
                                                key={agent.id}
                                                type="button"
                                                onClick={() => toggleAgent(agent.id)}
                                                className={clsx(
                                                    'w-full p-4 rounded-lg border text-left transition-all flex items-center gap-4',
                                                    isSelected
                                                        ? 'border-primary-500 bg-primary-500/10'
                                                        : 'border-white/10 hover:border-white/20'
                                                )}
                                            >
                                                {isSelected && (
                                                    <div className="w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center text-white font-bold">
                                                        {(orderIndex ?? 0) + 1}
                                                    </div>
                                                )}
                                                <div className="flex-1">
                                                    <div className="font-medium">{agent.name}</div>
                                                    <div className="text-sm text-gray-400">{agent.role}</div>
                                                </div>
                                                {isSelected && (
                                                    <X className="w-5 h-5 text-gray-400" />
                                                )}
                                            </button>
                                        );
                                    })}
                                </div>
                            )}

                            {formData.agents && formData.agents.length > 0 && (
                                <div className="mt-4 p-3 bg-dark-200 rounded-lg">
                                    <div className="text-sm text-gray-400 mb-2">Execution Order:</div>
                                    <div className="flex flex-wrap gap-2">
                                        {formData.agents.map((agentId, index) => {
                                            const agent = agentsData?.agents?.find((a: any) => a.id === agentId);
                                            return (
                                                <span key={agentId} className="badge-info flex items-center gap-1">
                                                    <span>{index + 1}.</span>
                                                    <span>{agent?.name || 'Unknown'}</span>
                                                </span>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                        </motion.div>

                        {/* Submit */}
                        <div className="flex justify-end gap-4">
                            <button
                                type="button"
                                onClick={() => router.back()}
                                className="btn-secondary"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={createMutation.isPending}
                                className="btn-primary inline-flex items-center gap-2"
                            >
                                {createMutation.isPending ? (
                                    <>
                                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                        Creating...
                                    </>
                                ) : (
                                    <>
                                        <Save className="w-4 h-4" />
                                        Create Workflow
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    );
}
