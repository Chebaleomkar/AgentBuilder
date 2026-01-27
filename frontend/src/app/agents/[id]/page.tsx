'use client';

import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
    Bot, ArrowLeft, Play, Settings, Trash2,
    Clock, Zap, Activity, CheckCircle, XCircle,
    Edit, MoreVertical, Send, Database, FileText, Plus, X, Upload
} from 'lucide-react';
import toast from 'react-hot-toast';
import Navbar from '@/components/layout/Navbar';
import { agentApi, Agent, knowledgeApi, KnowledgeBase, KnowledgeSource } from '@/lib/api';
import { clsx } from 'clsx';
import { AgentDetailSkeleton, Skeleton } from '@/components/ui/Skeleton';
import { useState, useRef } from 'react';

export default function AgentDetailPage() {
    const params = useParams();
    const router = useRouter();
    const queryClient = useQueryClient();
    const agentId = params.id as string;
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [inputText, setInputText] = useState('');
    const [executionResult, setExecutionResult] = useState<any>(null);
    const [activeTab, setActiveTab] = useState<'overview' | 'knowledge'>('overview');
    const [showAddText, setShowAddText] = useState(false);
    const [newTextSource, setNewTextSource] = useState({ name: '', content: '' });
    const [previewSource, setPreviewSource] = useState<KnowledgeSource | null>(null);
    const [previewContent, setPreviewContent] = useState<string | null>(null);
    const [isPreviewLoading, setIsPreviewLoading] = useState(false);

    const { data: agent, isLoading, error } = useQuery({
        queryKey: ['agent', agentId],
        queryFn: () => agentApi.get(agentId),
        enabled: !!agentId,
    });

    const { data: knowledge, isLoading: isLoadingKnowledge } = useQuery({
        queryKey: ['knowledge', agentId],
        queryFn: () => knowledgeApi.get(agentId),
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

    const uploadMutation = useMutation({
        mutationFn: (file: File) => knowledgeApi.upload(agentId, file),
        onSuccess: () => {
            toast.success('File uploaded successfully');
            queryClient.invalidateQueries({ queryKey: ['knowledge', agentId] });
        },
        onError: () => toast.error('Failed to upload file'),
    });

    const addTextMutation = useMutation({
        mutationFn: () => knowledgeApi.addText(agentId, newTextSource.name, newTextSource.content),
        onSuccess: () => {
            toast.success('Knowledge source added');
            setShowAddText(false);
            setNewTextSource({ name: '', content: '' });
            queryClient.invalidateQueries({ queryKey: ['knowledge', agentId] });
        },
        onError: () => toast.error('Failed to add knowledge'),
    });

    const deleteSourceMutation = useMutation({
        mutationFn: (sourceId: string) => knowledgeApi.deleteSource(agentId, sourceId),
        onSuccess: () => {
            toast.success('Source removed');
            queryClient.invalidateQueries({ queryKey: ['knowledge', agentId] });
        },
        onError: () => toast.error('Failed to remove source'),
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

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            // Check file size (e.g., 10MB limit)
            if (file.size > 10 * 1024 * 1024) {
                toast.error('File size exceeds 10MB limit');
                return;
            }
            uploadMutation.mutate(file);
        }
    };

    const handlePreviewSource = async (source: KnowledgeSource) => {
        setPreviewSource(source);
        setIsPreviewLoading(true);
        setPreviewContent(null);
        try {
            const content = await knowledgeApi.getContent(agentId, source.id);
            setPreviewContent(content);
        } catch (err) {
            toast.error('Failed to load document content');
            setPreviewSource(null);
        } finally {
            setIsPreviewLoading(false);
        }
    };

    if (isLoading) {
        return (
            <div className="min-h-screen pt-16">
                <Navbar />
                <div className="container mx-auto px-6 py-8 max-w-5xl">
                    <AgentDetailSkeleton />
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

                    <div className="flex items-center gap-2 sm:gap-3 shrink-0">
                        <button
                            onClick={() => router.push(`/playground?agent=${agentId}`)}
                            className="btn-primary flex items-center gap-2"
                        >
                            <Play className="w-4 h-4" />
                            <span className="hidden sm:inline">Run Agent</span>
                        </button>
                        <button
                            onClick={() => setShowDeleteConfirm(true)}
                            className="p-2 rounded-lg text-red-400 hover:bg-red-400/10 border border-transparent hover:border-red-400/20 transition-colors"
                            title="Delete Agent"
                        >
                            <Trash2 className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex items-center gap-4 border-b border-white/5 mb-8">
                    <button
                        onClick={() => setActiveTab('overview')}
                        className={clsx(
                            'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                            activeTab === 'overview' ? 'border-primary-500 text-primary-400' : 'border-transparent text-gray-500 hover:text-white'
                        )}
                    >
                        Overview
                    </button>
                    <button
                        onClick={() => setActiveTab('knowledge')}
                        className={clsx(
                            'px-4 py-2 text-sm font-medium border-b-2 transition-colors flex items-center gap-2',
                            activeTab === 'knowledge' ? 'border-primary-500 text-primary-400' : 'border-transparent text-green-500 hover:text-green-400'
                        )}
                    >
                        <Database className="w-4 h-4" />
                        Knowledge Base
                    </button>
                </div>

                {activeTab === 'overview' ? (
                    <div className="grid lg:grid-cols-3 gap-6">
                        {/* Left Column - Details & Execution */}
                        <div className="lg:col-span-2 space-y-6">
                            {/* Run Agent Section */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="card border-primary-500/20 bg-primary-500/5"
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

                                {executionResult && (
                                    <div className="mt-6 border-t border-white/10 pt-6">
                                        <h3 className="text-sm font-medium text-gray-400 mb-4">Response</h3>
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
                                <p className="text-gray-300 mb-6">{agent.goal || 'No goal specified'}</p>

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
                ) : (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="space-y-6"
                    >
                        {/* Knowledge Overview */}
                        <div className="grid md:grid-cols-2 gap-6">
                            <div className="card bg-dark-200/50 border-white/5">
                                <h3 className="text-sm font-semibold text-gray-400 uppercase mb-4">Add Grounding Material</h3>
                                <div className="grid grid-cols-2 gap-4">
                                    <button
                                        onClick={() => fileInputRef.current?.click()}
                                        className="flex flex-col items-center justify-center gap-3 p-6 rounded-xl border border-dashed border-white/10 hover:border-primary-500/50 hover:bg-primary-500/5 transition-all group"
                                    >
                                        <div className="w-12 h-12 rounded-full bg-primary-500/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                                            <Upload className="w-6 h-6 text-primary-400" />
                                        </div>
                                        <span className="text-sm font-medium">Upload File</span>
                                        <input
                                            type="file"
                                            ref={fileInputRef}
                                            onChange={handleFileUpload}
                                            className="hidden"
                                            accept=".txt,.pdf,.doc,.docx"
                                        />
                                    </button>
                                    <button
                                        onClick={() => setShowAddText(true)}
                                        className="flex flex-col items-center justify-center gap-3 p-6 rounded-xl border border-dashed border-white/10 hover:border-accent-500/50 hover:bg-accent-500/5 transition-all group"
                                    >
                                        <div className="w-12 h-12 rounded-full bg-accent-500/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                                            <Plus className="w-6 h-6 text-accent-400" />
                                        </div>
                                        <span className="text-sm font-medium">Add Text Nugget</span>
                                    </button>
                                </div>
                                <p className="text-xs text-gray-500 mt-4 text-center">
                                    Upload SOPs, policy docs (TXT), or paste direct text to give your agent static knowledge.
                                </p>
                            </div>

                            <div className="card">
                                <h3 className="text-sm font-semibold text-gray-400 uppercase mb-4">Knowledge Sources</h3>
                                <div className="space-y-3">
                                    {isLoadingKnowledge ? (
                                        <div className="space-y-3">
                                            {[1, 2, 3].map(i => (
                                                <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-dark-300 border border-white/5">
                                                    <Skeleton className="w-8 h-8 rounded" />
                                                    <div className="flex-1 space-y-2">
                                                        <Skeleton className="w-32 h-4" />
                                                        <Skeleton className="w-16 h-2" />
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    ) : knowledge?.sources.length === 0 ? (
                                        <div className="flex flex-col items-center justify-center py-12 text-center border border-dashed border-white/5 rounded-xl bg-dark-400/20">
                                            <div className="w-12 h-12 rounded-full bg-dark-300 flex items-center justify-center mb-4">
                                                <Database className="w-6 h-6 text-gray-600" />
                                            </div>
                                            <p className="text-sm font-medium text-gray-300">Knowledge base is empty</p>
                                            <p className="text-xs text-gray-500 mt-1 max-w-[200px]">
                                                Upload files or add text nuggets to provide context for your agent.
                                            </p>
                                        </div>
                                    ) : (
                                        knowledge?.sources.map((source) => (
                                            <div
                                                key={source.id}
                                                onDoubleClick={() => handlePreviewSource(source)}
                                                className="flex items-center justify-between p-3 rounded-lg bg-dark-300 border border-white/5 hover:border-primary-500/30 transition-all cursor-pointer group"
                                                title="Double-click to preview"
                                            >
                                                <div className="flex items-center gap-3 overflow-hidden">
                                                    <div className={clsx(
                                                        "w-8 h-8 rounded flex items-center justify-center flex-shrink-0",
                                                        source.type === 'file' ? 'bg-blue-500/10' : 'bg-purple-500/10'
                                                    )}>
                                                        <FileText className={clsx("w-4 h-4", source.type === 'file' ? 'text-blue-400' : 'text-purple-400')} />
                                                    </div>
                                                    <div className="min-w-0">
                                                        <div className="text-sm font-medium truncate group-hover:text-primary-400 transition-colors">{source.name}</div>
                                                        <div className="text-[10px] text-gray-500 uppercase">{source.type} {source.size_bytes ? `• ${(source.size_bytes / 1024).toFixed(1)}KB` : ''}</div>
                                                    </div>
                                                </div>
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        deleteSourceMutation.mutate(source.id);
                                                    }}
                                                    className="p-1.5 rounded-md hover:bg-red-500/10 text-gray-500 hover:text-red-400 transition-colors"
                                                >
                                                    <X className="w-4 h-4" />
                                                </button>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Add Text Modal */}
                        {showAddText && (
                            <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="card max-w-lg w-full"
                                >
                                    <div className="flex items-center justify-between mb-6">
                                        <h3 className="text-xl font-bold">Add Text Source</h3>
                                        <button onClick={() => setShowAddText(false)} className="text-gray-500 hover:text-white">
                                            <X className="w-6 h-6" />
                                        </button>
                                    </div>
                                    <div className="space-y-4">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-400 mb-1">Source Name</label>
                                            <input
                                                type="text"
                                                value={newTextSource.name}
                                                onChange={(e) => setNewTextSource({ ...newTextSource, name: e.target.value })}
                                                placeholder="e.g. Employee Support Policy"
                                                className="input bg-dark-300"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-400 mb-1">Content</label>
                                            <textarea
                                                value={newTextSource.content}
                                                onChange={(e) => setNewTextSource({ ...newTextSource, content: e.target.value })}
                                                placeholder="Paste the relevant SOP text here..."
                                                className="textarea bg-dark-300 h-48"
                                            />
                                        </div>
                                        <div className="flex justify-end gap-3 mt-4">
                                            <button onClick={() => setShowAddText(false)} className="btn-secondary">Cancel</button>
                                            <button
                                                onClick={() => addTextMutation.mutate()}
                                                disabled={!newTextSource.name || !newTextSource.content || addTextMutation.isPending}
                                                className="btn-primary"
                                            >
                                                {addTextMutation.isPending ? 'Saving...' : 'Add Knowledge'}
                                            </button>
                                        </div>
                                    </div>
                                </motion.div>
                            </div>
                        )}
                        {/* Document Preview Modal */}
                        {previewSource && (
                            <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center z-50 p-4 lg:p-12">
                                <motion.div
                                    initial={{ opacity: 0, y: 50 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="bg-dark-200 rounded-2xl w-full max-w-5xl h-[85vh] border border-white/10 flex flex-col shadow-2xl overflow-hidden"
                                >
                                    <div className="p-6 border-b border-white/10 flex items-center justify-between bg-dark-100/50">
                                        <div className="flex items-center gap-4">
                                            <div className="w-10 h-10 rounded-xl bg-primary-500/10 flex items-center justify-center">
                                                <FileText className="w-5 h-5 text-primary-400" />
                                            </div>
                                            <div>
                                                <h3 className="text-xl font-bold">{previewSource.name}</h3>
                                                <p className="text-xs text-gray-500 uppercase">
                                                    {previewSource.type} • {previewSource.file_type || 'Text Nugget'}
                                                </p>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => setPreviewSource(null)}
                                            className="p-2 rounded-xl bg-white/5 hover:bg-white/10 transition-colors group"
                                        >
                                            <X className="w-6 h-6 text-gray-400 group-hover:text-white" />
                                        </button>
                                    </div>
                                    <div className="flex-1 overflow-y-auto p-8 font-sans leading-relaxed text-gray-300">
                                        {isPreviewLoading ? (
                                            <div className="h-full flex flex-col items-center justify-center gap-4">
                                                <div className="w-10 h-10 border-4 border-primary-500/20 border-t-primary-500 rounded-full animate-spin" />
                                                <span className="text-sm text-gray-500 font-medium">Extracting content...</span>
                                            </div>
                                        ) : previewContent ? (
                                            <div className="prose prose-invert max-w-none whitespace-pre-wrap">
                                                {previewContent}
                                            </div>
                                        ) : (
                                            <div className="h-full flex flex-col items-center justify-center gap-4 text-gray-500">
                                                <XCircle className="w-12 h-12 opacity-20" />
                                                <span>No content available for this source.</span>
                                            </div>
                                        )}
                                    </div>
                                    <div className="p-4 border-t border-white/10 bg-dark-100/30 flex justify-end">
                                        <button onClick={() => setPreviewSource(null)} className="btn-secondary px-6">Close</button>
                                    </div>
                                </motion.div>
                            </div>
                        )}
                    </motion.div>
                )}

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
