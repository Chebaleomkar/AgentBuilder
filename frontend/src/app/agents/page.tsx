'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Plus, Bot, MoreVertical, Play, Edit, Trash2 } from 'lucide-react';
import Navbar from '@/components/layout/Navbar';
import { agentApi, Agent } from '@/lib/api';
import { clsx } from 'clsx';

const statusColors = {
    active: 'badge-success',
    inactive: 'badge-warning',
    running: 'badge-info',
    error: 'badge-error',
};

export default function AgentsPage() {
    const { data, isLoading, error } = useQuery({
        queryKey: ['agents'],
        queryFn: () => agentApi.list(),
    });

    return (
        <div className="min-h-screen pt-16">
            <Navbar />

            <div className="container mx-auto px-6 py-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold mb-2">Agents</h1>
                        <p className="text-gray-400">Create and manage your AI agents</p>
                    </div>
                    <Link href="/agents/create" className="btn-primary inline-flex items-center gap-2">
                        <Plus className="w-5 h-5" />
                        Create Agent
                    </Link>
                </div>

                {/* Loading State */}
                {isLoading && (
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="card animate-pulse">
                                <div className="h-6 bg-dark-100 rounded w-3/4 mb-4" />
                                <div className="h-4 bg-dark-100 rounded w-1/2 mb-2" />
                                <div className="h-4 bg-dark-100 rounded w-full" />
                            </div>
                        ))}
                    </div>
                )}

                {/* Error State */}
                {error && (
                    <div className="card border-red-500/30 bg-red-500/10">
                        <p className="text-red-400">Failed to load agents. Please try again.</p>
                    </div>
                )}

                {/* Empty State */}
                {data?.agents?.length === 0 && (
                    <div className="card text-center py-16">
                        <Bot className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                        <h3 className="text-xl font-semibold mb-2">No agents yet</h3>
                        <p className="text-gray-400 mb-6">Create your first AI agent to get started</p>
                        <Link href="/agents/create" className="btn-primary inline-flex items-center gap-2">
                            <Plus className="w-5 h-5" />
                            Create Agent
                        </Link>
                    </div>
                )}

                {/* Agents Grid */}
                {data?.agents && data.agents.length > 0 && (
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {data.agents.map((agent: Agent, index: number) => (
                            <motion.div
                                key={agent.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.05 }}
                            >
                                <div className="card-hover group">
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
                                                <Bot className="w-5 h-5 text-white" />
                                            </div>
                                            <div>
                                                <h3 className="font-semibold group-hover:text-primary-400 transition-colors">
                                                    {agent.name}
                                                </h3>
                                                <p className="text-sm text-gray-500">{agent.role}</p>
                                            </div>
                                        </div>
                                        <span className={clsx(statusColors[agent.status])}>
                                            {agent.status}
                                        </span>
                                    </div>

                                    {agent.goal && (
                                        <p className="text-sm text-gray-400 mb-4 line-clamp-2">
                                            {agent.goal}
                                        </p>
                                    )}

                                    <div className="flex flex-wrap gap-2 mb-4">
                                        {agent.tools.slice(0, 3).map((tool) => (
                                            <span key={tool} className="px-2 py-1 bg-dark-100 rounded text-xs text-gray-400">
                                                {tool}
                                            </span>
                                        ))}
                                        {agent.tools.length > 3 && (
                                            <span className="px-2 py-1 bg-dark-100 rounded text-xs text-gray-400">
                                                +{agent.tools.length - 3} more
                                            </span>
                                        )}
                                    </div>

                                    <div className="flex items-center gap-2 pt-4 border-t border-white/5">
                                        <Link
                                            href={`/playground?agent=${agent.id}`}
                                            className="btn-ghost flex-1 flex items-center justify-center gap-2 text-sm"
                                        >
                                            <Play className="w-4 h-4" />
                                            Run
                                        </Link>
                                        <Link
                                            href={`/agents/${agent.id}`}
                                            className="btn-ghost flex-1 flex items-center justify-center gap-2 text-sm"
                                        >
                                            <Edit className="w-4 h-4" />
                                            Edit
                                        </Link>
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
