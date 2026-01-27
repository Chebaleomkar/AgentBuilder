'use client';

import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, Reorder, AnimatePresence } from 'framer-motion';
import {
    Workflow as WorkflowIcon, ArrowLeft, Play, Settings, Trash2,
    Clock, Zap, Activity, CheckCircle, XCircle,
    Edit, Users, ChevronRight, Save, X, GripVertical, Plus
} from 'lucide-react';
import toast from 'react-hot-toast';
import Navbar from '@/components/layout/Navbar';
import { workflowApi, agentApi, Workflow as WorkflowType } from '@/lib/api';
import { clsx } from 'clsx';
import { useState, useEffect } from 'react';

const coordinationStrategies = [
    { id: 'sequential', name: 'Sequential', description: 'Agents run one after another' },
    { id: 'supervisor', name: 'Supervisor', description: 'One agent coordinates others' },
    { id: 'peer', name: 'Peer', description: 'Agents work in parallel' },
    { id: 'conditional', name: 'Conditional', description: 'Branch based on conditions' },
];

export default function WorkflowDetailPage() {
    const params = useParams();
    const router = useRouter();
    const queryClient = useQueryClient();
    const workflowId = params.id as string;

    const [isEditing, setIsEditing] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [showAddAgent, setShowAddAgent] = useState(false);

    // Form state
    const [editData, setEditData] = useState({
        name: '',
        description: '',
        coordination_strategy: '',
        agents: [] as string[]
    });

    const { data: workflow, isLoading, error } = useQuery({
        queryKey: ['workflow', workflowId],
        queryFn: () => workflowApi.get(workflowId),
        enabled: !!workflowId,
    });

    const { data: agentsData } = useQuery({
        queryKey: ['agents'],
        queryFn: () => agentApi.list(),
    });

    // Sync form state when workflow data loads
    useEffect(() => {
        if (workflow) {
            setEditData({
                name: workflow.name,
                description: workflow.description || '',
                coordination_strategy: workflow.coordination_strategy,
                agents: workflow.agents || [],
            });
        }
    }, [workflow]);

    const updateMutation = useMutation({
        mutationFn: (updates: any) => workflowApi.update(workflowId, updates),
        onSuccess: () => {
            toast.success('Workflow updated successfully');
            queryClient.invalidateQueries({ queryKey: ['workflow', workflowId] });
            setIsEditing(false);
        },
        onError: () => {
            toast.error('Failed to update workflow');
        },
    });

    const deleteMutation = useMutation({
        mutationFn: () => workflowApi.delete(workflowId),
        onSuccess: () => {
            toast.success('Workflow deleted successfully');
            queryClient.invalidateQueries({ queryKey: ['workflows'] });
            router.push('/workflows');
        },
        onError: () => {
            toast.error('Failed to delete workflow');
        },
    });

    const handleSave = () => {
        if (!editData.name) {
            toast.error('Workflow name is required');
            return;
        }
        if (editData.agents.length < 2) {
            toast.error('Workflow must have at least 2 agents');
            return;
        }
        updateMutation.mutate(editData);
    };

    const handleReorder = (newOrder: string[]) => {
        setEditData(prev => ({ ...prev, agents: newOrder }));
    };

    const removeAgent = (agentId: string) => {
        setEditData(prev => ({
            ...prev,
            agents: prev.agents.filter(id => id !== agentId)
        }));
    };

    const addAgent = (agentId: string) => {
        if (!editData.agents.includes(agentId)) {
            setEditData(prev => ({
                ...prev,
                agents: [...prev.agents, agentId]
            }));
        }
        setShowAddAgent(false);
    };

    if (isLoading) {
        return (
            <div className="min-h-screen pt-16">
                <Navbar />
                <div className="container mx-auto px-6 py-8">
                    <div className="animate-pulse space-y-6">
                        <div className="h-8 bg-dark-200 rounded w-1/3"></div>
                        <div className="h-64 bg-dark-200 rounded-xl"></div>
                    </div>
                </div>
            </div>
        );
    }

    if (error || !workflow) {
        return (
            <div className="min-h-screen pt-16">
                <Navbar />
                <div className="container mx-auto px-6 py-8">
                    <div className="card text-center py-16">
                        <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
                        <h2 className="text-xl font-semibold mb-2">Workflow Not Found</h2>
                        <p className="text-gray-400 mb-6">The workflow you're looking for doesn't exist or was deleted.</p>
                        <button onClick={() => router.push('/workflows')} className="btn-primary">
                            Back to Workflows
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    const statusColors = {
        active: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/30',
        draft: 'text-gray-400 bg-gray-400/10 border-gray-400/30',
        paused: 'text-amber-400 bg-amber-400/10 border-amber-400/30',
        archived: 'text-red-400 bg-red-400/10 border-red-400/30',
    };

    return (
        <div className="min-h-screen pt-16">
            <Navbar />

            <div className="container mx-auto px-6 py-8 max-w-5xl">
                {/* Header */}
                <div className="flex items-start justify-between mb-8">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => isEditing ? setIsEditing(false) : router.back()}
                            className="p-2 rounded-lg hover:bg-white/5 transition-colors"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                        <div>
                            <div className="flex items-center gap-3 mb-1">
                                <WorkflowIcon className="w-8 h-8 text-accent-400" />
                                {isEditing ? (
                                    <input
                                        type="text"
                                        value={editData.name}
                                        onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                                        className="text-3xl font-bold bg-transparent border-b border-white/20 focus:border-primary-500 outline-none px-1"
                                    />
                                ) : (
                                    <h1 className="text-3xl font-bold">{workflow.name}</h1>
                                )}
                                <span className={clsx(
                                    'px-2.5 py-1 rounded-full text-xs font-medium border capitalize',
                                    statusColors[workflow.status as keyof typeof statusColors] || statusColors.draft
                                )}>
                                    {workflow.status}
                                </span>
                            </div>
                            {isEditing ? (
                                <input
                                    type="text"
                                    value={editData.description}
                                    onChange={(e) => setEditData({ ...editData, description: e.target.value })}
                                    placeholder="Add description..."
                                    className="text-gray-400 bg-transparent border-b border-white/10 focus:border-primary-500 outline-none px-1 w-full mt-2"
                                />
                            ) : (
                                <p className="text-gray-400">{workflow.description || 'No description provided'}</p>
                            )}
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        {isEditing ? (
                            <>
                                <button
                                    onClick={() => setIsEditing(false)}
                                    className="btn-secondary flex items-center gap-2"
                                >
                                    <X className="w-4 h-4" />
                                    Cancel
                                </button>
                                <button
                                    onClick={handleSave}
                                    disabled={updateMutation.isPending}
                                    className="btn-primary flex items-center gap-2"
                                >
                                    {updateMutation.isPending ? (
                                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                    ) : (
                                        <Save className="w-4 h-4" />
                                    )}
                                    Save Changes
                                </button>
                            </>
                        ) : (
                            <>
                                <button
                                    onClick={() => router.push(`/playground?workflow=${workflowId}`)}
                                    className="btn-primary flex items-center gap-2"
                                >
                                    <Play className="w-4 h-4" />
                                    Run
                                </button>
                                <button
                                    onClick={() => setIsEditing(true)}
                                    className="p-2 rounded-lg text-gray-400 hover:bg-white/5 transition-colors"
                                    title="Edit Workflow"
                                >
                                    <Edit className="w-5 h-5" />
                                </button>
                                <button
                                    onClick={() => setShowDeleteConfirm(true)}
                                    className="p-2 rounded-lg text-red-400 hover:bg-red-400/10 transition-colors"
                                    title="Delete Workflow"
                                >
                                    <Trash2 className="w-5 h-5" />
                                </button>
                            </>
                        )}
                    </div>
                </div>

                {/* Main Content */}
                <div className="grid lg:grid-cols-3 gap-6">
                    {/* Left Column - Pipeline */}
                    <div className="lg:col-span-2 space-y-6">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="card"
                        >
                            <div className="flex items-center justify-between mb-6">
                                <h2 className="text-lg font-semibold flex items-center gap-2">
                                    <Activity className="w-5 h-5 text-primary-400" />
                                    Execution Pipeline
                                </h2>
                                {isEditing && (
                                    <button
                                        onClick={() => setShowAddAgent(true)}
                                        className="text-xs text-primary-400 hover:underline flex items-center gap-1"
                                    >
                                        <Plus className="w-3 h-3" />
                                        Add Agent
                                    </button>
                                )}
                            </div>

                            <div className="space-y-4">
                                {isEditing ? (
                                    <Reorder.Group
                                        axis="y"
                                        values={editData.agents}
                                        onReorder={handleReorder}
                                        className="space-y-4"
                                    >
                                        {editData.agents.map((agentId, index) => {
                                            const agent = agentsData?.agents?.find((a: any) => a.id === agentId);
                                            return (
                                                <Reorder.Item
                                                    key={agentId}
                                                    value={agentId}
                                                    className="flex items-center gap-4 group"
                                                >
                                                    <div className="flex flex-col items-center">
                                                        <div className="w-10 h-10 rounded-full bg-dark-200 border border-white/10 flex items-center justify-center font-bold text-primary-400">
                                                            {index + 1}
                                                        </div>
                                                        {index < editData.agents.length - 1 && (
                                                            <div className="w-0.5 h-12 bg-gradient-to-b from-primary-500/50 to-transparent my-1" />
                                                        )}
                                                    </div>
                                                    <div className="flex-1 p-4 rounded-xl border border-white/10 bg-white/5 flex items-center gap-4">
                                                        <GripVertical className="w-5 h-5 text-gray-600 cursor-grab active:cursor-grabbing" />
                                                        <div className="flex-1">
                                                            <div className="font-medium text-white">{agent?.name || 'Unknown Agent'}</div>
                                                            <div className="text-sm text-gray-500">{agent?.role || 'Agent Role'}</div>
                                                        </div>
                                                        <button
                                                            onClick={() => removeAgent(agentId)}
                                                            className="p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-400/10 transition-colors opacity-0 group-hover:opacity-100"
                                                        >
                                                            <X className="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                </Reorder.Item>
                                            );
                                        })}
                                    </Reorder.Group>
                                ) : (
                                    workflow.agents && workflow.agents.length > 0 ? (
                                        workflow.agents.map((agentId, index) => {
                                            const agent = agentsData?.agents?.find((a: any) => a.id === agentId);
                                            return (
                                                <div key={agentId} className="flex items-center gap-4">
                                                    <div className="flex flex-col items-center">
                                                        <div className="w-10 h-10 rounded-full bg-dark-200 border border-white/10 flex items-center justify-center font-bold text-primary-400">
                                                            {index + 1}
                                                        </div>
                                                        {index < workflow.agents.length - 1 && (
                                                            <div className="w-0.5 h-12 bg-gradient-to-b from-primary-500/50 to-transparent my-1" />
                                                        )}
                                                    </div>
                                                    <div
                                                        className="flex-1 p-4 rounded-xl border border-white/5 bg-white/5 hover:bg-white/10 transition-colors cursor-pointer"
                                                        onClick={() => router.push(`/agents/${agentId}`)}
                                                    >
                                                        <div className="flex justify-between items-center">
                                                            <div>
                                                                <div className="font-medium text-white">{agent?.name || 'Unknown Agent'}</div>
                                                                <div className="text-sm text-gray-500">{agent?.role || 'Agent Role'}</div>
                                                            </div>
                                                            <ChevronRight className="w-4 h-4 text-gray-600" />
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })
                                    ) : (
                                        <div className="p-8 text-center bg-dark-200 rounded-xl border border-dashed border-white/10 text-gray-500">
                                            No agents assigned to this workflow.
                                        </div>
                                    )
                                )}
                            </div>
                        </motion.div>
                    </div>

                    {/* Right Column - Config */}
                    <div className="space-y-6">
                        {/* Strategy Info */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="card"
                        >
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <Zap className="w-5 h-5 text-accent-400" />
                                Strategy
                            </h2>
                            <div className="space-y-4">
                                <div>
                                    <div className="text-xs text-gray-500 mb-1">Coordination</div>
                                    {isEditing ? (
                                        <select
                                            value={editData.coordination_strategy}
                                            onChange={(e) => setEditData({ ...editData, coordination_strategy: e.target.value })}
                                            className="w-full bg-dark-200 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-primary-500"
                                        >
                                            {coordinationStrategies.map(s => (
                                                <option key={s.id} value={s.id}>{s.name}</option>
                                            ))}
                                        </select>
                                    ) : (
                                        <div className="font-medium capitalize">{workflow.coordination_strategy}</div>
                                    )}
                                </div>
                                <div>
                                    <div className="text-xs text-gray-500 mb-1">Execution Mode</div>
                                    <div className="font-medium capitalize">{workflow.execution_mode}</div>
                                </div>
                                <div>
                                    <div className="text-xs text-gray-500 mb-1">Total Agents</div>
                                    <div className="flex items-center gap-2 font-medium">
                                        <Users className="w-4 h-4 text-gray-400" />
                                        {isEditing ? editData.agents.length : workflow.agents?.length || 0} Agents
                                    </div>
                                </div>
                            </div>
                        </motion.div>

                        {/* Timestamps */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="card"
                        >
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <Clock className="w-5 h-5 text-gray-400" />
                                Timeline
                            </h2>
                            <div className="space-y-3 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-gray-500">Created</span>
                                    <span>{new Date(workflow.created_at).toLocaleDateString()}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-500">Updated</span>
                                    <span>{new Date(workflow.updated_at).toLocaleDateString()}</span>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                </div>

                {/* Modals */}
                <AnimatePresence>
                    {/* Delete Confirmation */}
                    {showDeleteConfirm && (
                        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                            <motion.div
                                initial={{ scale: 0.9, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                exit={{ scale: 0.9, opacity: 0 }}
                                className="card max-w-md w-full mx-4"
                            >
                                <h3 className="text-xl font-semibold mb-2 text-white">Delete Workflow</h3>
                                <p className="text-gray-400 mb-6">
                                    Are you sure you want to delete "{workflow.name}"? This will remove all orchestration logic for these agents.
                                </p>
                                <div className="flex gap-3 justify-end">
                                    <button
                                        onClick={() => setShowDeleteConfirm(false)}
                                        className="btn-secondary"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={() => deleteMutation.mutate()}
                                        disabled={deleteMutation.isPending}
                                        className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors"
                                    >
                                        {deleteMutation.isPending ? 'Deleting...' : 'Delete Workflow'}
                                    </button>
                                </div>
                            </motion.div>
                        </div>
                    )}

                    {/* Add Agent Modal */}
                    {showAddAgent && (
                        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                            <motion.div
                                initial={{ scale: 0.9, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                exit={{ scale: 0.9, opacity: 0 }}
                                className="card max-w-lg w-full mx-4 overflow-hidden flex flex-col max-h-[80vh]"
                            >
                                <div className="flex items-center justify-between mb-6">
                                    <h3 className="text-xl font-semibold text-white">Add Agent to Pipeline</h3>
                                    <button onClick={() => setShowAddAgent(false)}>
                                        <X className="w-5 h-5 text-gray-500" />
                                    </button>
                                </div>

                                <div className="flex-1 overflow-y-auto space-y-2 pr-2">
                                    {agentsData?.agents?.filter((a: any) => !editData.agents.includes(a.id)).map((agent: any) => (
                                        <button
                                            key={agent.id}
                                            onClick={() => addAgent(agent.id)}
                                            className="w-full p-4 rounded-lg border border-white/10 text-left hover:border-primary-500 hover:bg-primary-500/5 transition-all group"
                                        >
                                            <div className="font-medium group-hover:text-primary-400 transition-colors">{agent.name}</div>
                                            <div className="text-sm text-gray-500">{agent.role}</div>
                                        </button>
                                    ))}
                                    {agentsData?.agents?.filter((a: any) => !editData.agents.includes(a.id)).length === 0 && (
                                        <div className="text-center py-8 text-gray-500 italic">
                                            All available agents are already in the pipeline.
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        </div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
