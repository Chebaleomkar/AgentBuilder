'use client';

import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
    Bot, ArrowLeft, Play, Settings, Trash2,
    Clock, Zap, Activity, CheckCircle, XCircle,
    Edit, MoreVertical, Send
} from 'lucide-react';
import toast from 'react-hot-toast';
import Navbar from '@/components/layout/Navbar';
import { agentApi, Agent } from '@/lib/api';
import { clsx } from 'clsx';
import { useState } from 'react';

export default function AgentDetailPage() {
    const params = useParams();
    const router = useRouter();
    const queryClient = useQueryClient();
    const agentId = params.id as string;

    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [inputText, setInputText] = useState('');
    const [executionResult, setExecutionResult] = useState<any>(null);

    const { data: agent, isLoading, error } = useQuery({
        queryKey: ['agent', agentId],
        queryFn: () => agentApi.get(agentId),
        enabled: !!agentId,
    });

    const executeMutation = useMutation({
        mutationFn: (input: string) => agentApi.execute(agentId, { query: input }),
        onSuccess: (data) => {
            setExecutionResult(data);
            toast.success('Execution completed!');
        },
        onError: (err: any) => {
            toast.error(err.response?.data?.detail || 'Execution failed');
        },
    });

    const deleteMutation = useMutation({
        mutationFn: () => agentApi.delete(agentId),
        onSuccess: () => {
            toast.success('Agent deleted successfully');
            queryClient.invalidateQueries({ queryKey: ['agents'] });
            router.push('/agents');
        },
        onError: () => {
            toast.error('Failed to delete agent');
        },
    });

    const handleRunAgent = () => {
        if (!inputText.trim()) {
            toast.error('Please enter a prompt');
            return;
        }
        executeMutation.mutate(inputText);
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

    if (error || !agent) {
        return (
            <div className="min-h-screen pt-16">
                <Navbar />
                <div className="container mx-auto px-6 py-8">
                    <div className="card text-center py-16">
                        <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
                        <h2 className="text-xl font-semibold mb-2">Agent Not Found</h2>
                        <p className="text-gray-400 mb-6">The agent you're looking for doesn't exist or was deleted.</p>
                        <button onClick={() => router.push('/agents')} className="btn-primary">
                            Back to Agents
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    const statusColors = {
        active: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/30',
        inactive: 'text-gray-400 bg-gray-400/10 border-gray-400/30',
        running: 'text-primary-400 bg-primary-400/10 border-primary-400/30',
        error: 'text-red-400 bg-red-400/10 border-red-400/30',
    };

    return (
        <div className="min-h-screen pt-16">
            <Navbar />

            <div className="container mx-auto px-6 py-8 max-w-5xl">
                {/* Header */}
                <div className="flex items-start justify-between mb-8">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => router.back()}
                            className="p-2 rounded-lg hover:bg-white/5 transition-colors"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                        <div>
                            <div className="flex items-center gap-3 mb-1">
                                <Bot className="w-8 h-8 text-primary-400" />
                                <h1 className="text-3xl font-bold">{agent.name}</h1>
                                <span className={clsx(
                                    'px-2.5 py-1 rounded-full text-xs font-medium border',
                                    statusColors[agent.status] || statusColors.inactive
                                )}>
                                    {agent.status}
                                </span>
                            </div>
                            <p className="text-gray-400">{agent.role}</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => {
                                const el = document.getElementById('run-agent-section');
                                el?.scrollIntoView({ behavior: 'smooth' });
                            }}
                            className="btn-primary flex items-center gap-2"
                        >
                            <Play className="w-4 h-4" />
                            Run Agent
                        </button>
                        <button
                            onClick={() => setShowDeleteConfirm(true)}
                            className="p-2 rounded-lg text-red-400 hover:bg-red-400/10 transition-colors"
                        >
                            <Trash2 className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* Main Content */}
                <div className="grid lg:grid-cols-3 gap-6">
                    {/* Left Column - Details & Execution */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Run Agent Section (NEW) */}
                        <motion.div
                            id="run-agent-section"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="card border-primary-500/20 bg-primary-500/5 shadow-lg shadow-primary-500/5"
                        >
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <Zap className="w-5 h-5 text-primary-400" />
                                Quick Execution
                            </h2>
                            <div className="space-y-4">
                                <textarea
                                    value={inputText}
                                    onChange={(e) => setInputText(e.target.value)}
                                    placeholder={`Send a prompt to ${agent.name}...`}
                                    className="textarea h-24 bg-dark-300 ring-1 ring-white/5 focus:ring-primary-500/50"
                                />
                                <div className="flex justify-end">
                                    <button
                                        onClick={handleRunAgent}
                                        disabled={executeMutation.isPending}
                                        className="btn-primary flex items-center gap-2"
                                    >
                                        {executeMutation.isPending ? (
                                            <>
                                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                                Running...
                                            </>
                                        ) : (
                                            <>
                                                <Send className="w-4 h-4" />
                                                Execute
                                            </>
                                        )}
                                    </button>
                                </div>
                            </div>

                            {/* Execution Results Snippet */}
                            {executionResult && (
                                <div className="mt-6 border-t border-white/10 pt-6">
                                    <div className="flex items-center justify-between mb-4">
                                        <h3 className="text-sm font-medium text-gray-400">Response</h3>
                                        <button
                                            onClick={() => router.push(`/playground?mode=agent&id=${agentId}`)}
                                            className="text-xs text-primary-400 hover:underline flex items-center gap-1"
                                        >
                                            View in Playground
                                            <ArrowLeft className="w-3 h-3 rotate-180" />
                                        </button>
                                    </div>
                                    <div className="bg-dark-300 rounded-lg p-4 font-sans text-sm text-gray-300 prose prose-invert max-w-none">
                                        {executionResult.output_data?.result?.response || executionResult.output_data?.result || 'Execution completed with no direct output.'}
                                    </div>
                                </div>
                            )}
                        </motion.div>
                        {/* Goal & Instructions */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="card"
                        >
                            <h2 className="text-lg font-semibold mb-4">Goal</h2>
                            <p className="text-gray-300 mb-6">
                                {agent.goal || 'No goal specified'}
                            </p>

                            <h2 className="text-lg font-semibold mb-4">Instructions</h2>
                            <div className="bg-dark-300/50 rounded-lg p-4">
                                <pre className="text-sm text-gray-300 whitespace-pre-wrap font-sans">
                                    {agent.instructions || 'No instructions specified'}
                                </pre>
                            </div>
                        </motion.div>

                        {/* Tools */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="card"
                        >
                            <h2 className="text-lg font-semibold mb-4">Tools</h2>
                            {agent.tools && agent.tools.length > 0 ? (
                                <div className="flex flex-wrap gap-2">
                                    {agent.tools.map((tool) => (
                                        <span
                                            key={tool}
                                            className="px-3 py-1.5 bg-primary-500/10 text-primary-400 rounded-lg text-sm font-medium"
                                        >
                                            {tool}
                                        </span>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-gray-500">No tools configured</p>
                            )}
                        </motion.div>
                    </div>

                    {/* Right Column - Config */}
                    <div className="space-y-6">
                        {/* Model Info */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.15 }}
                            className="card"
                        >
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <Zap className="w-5 h-5 text-accent-400" />
                                Model Config
                            </h2>
                            <div className="space-y-4">
                                <div>
                                    <div className="text-xs text-gray-500 mb-1">Model</div>
                                    <div className="font-medium">{agent.model}</div>
                                </div>
                                <div>
                                    <div className="text-xs text-gray-500 mb-1">Temperature</div>
                                    <div className="flex items-center gap-2">
                                        <div className="flex-1 h-2 bg-dark-300 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full"
                                                style={{ width: `${(agent.temperature / 2) * 100}%` }}
                                            />
                                        </div>
                                        <span className="text-sm font-medium">{agent.temperature}</span>
                                    </div>
                                </div>
                                <div>
                                    <div className="text-xs text-gray-500 mb-1">Memory</div>
                                    <div className="font-medium capitalize">{agent.memory_type}</div>
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
                                    <span>{new Date(agent.created_at).toLocaleDateString()}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-500">Updated</span>
                                    <span>{new Date(agent.updated_at).toLocaleDateString()}</span>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                </div>

                {/* Delete Confirmation Modal */}
                {showDeleteConfirm && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            className="card max-w-md w-full mx-4"
                        >
                            <h3 className="text-xl font-semibold mb-2">Delete Agent</h3>
                            <p className="text-gray-400 mb-6">
                                Are you sure you want to delete "{agent.name}"? This action cannot be undone.
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
                                    {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </div>
        </div>
    );
}
