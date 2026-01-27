'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Plus, Workflow, MoreVertical, Play, Edit, Users } from 'lucide-react';
import Navbar from '@/components/layout/Navbar';
import { workflowApi, Workflow as WorkflowType } from '@/lib/api';
import { clsx } from 'clsx';
import { WorkflowCardSkeleton } from '@/components/ui/Skeleton';

const statusColors = {
    draft: 'badge-warning',
    active: 'badge-success',
    paused: 'badge-info',
    archived: 'text-gray-500',
};

const strategyLabels = {
    sequential: 'Sequential',
    supervisor: 'Supervisor',
    peer: 'Peer',
    conditional: 'Conditional',
};

export default function WorkflowsPage() {
    const { data, isLoading, error } = useQuery({
        queryKey: ['workflows'],
        queryFn: () => workflowApi.list(),
    });

    return (
        <div className="min-h-screen pt-16">
            <Navbar />

            <div className="container mx-auto px-6 py-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold mb-2">Workflows</h1>
                        <p className="text-gray-400">Create multi-agent orchestration workflows</p>
                    </div>
                    <Link href="/workflows/create" className="btn-primary inline-flex items-center gap-2">
                        <Plus className="w-5 h-5" />
                        Create Workflow
                    </Link>
                </div>

                {/* Loading State */}
                {isLoading && (
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[1, 2, 3, 4, 5, 6].map((i) => (
                            <WorkflowCardSkeleton key={i} />
                        ))}
                    </div>
                )}

                {/* Empty State */}
                {data?.workflows?.length === 0 && (
                    <div className="card text-center py-16">
                        <Workflow className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                        <h3 className="text-xl font-semibold mb-2">No workflows yet</h3>
                        <p className="text-gray-400 mb-6">Create your first multi-agent workflow</p>
                        <Link href="/workflows/create" className="btn-primary inline-flex items-center gap-2">
                            <Plus className="w-5 h-5" />
                            Create Workflow
                        </Link>
                    </div>
                )}

                {/* Workflows Grid */}
                {data?.workflows && data.workflows.length > 0 && (
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {data.workflows.map((workflow: WorkflowType, index: number) => (
                            <motion.div
                                key={workflow.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.05 }}
                            >
                                <div className="card-hover group">
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-500 to-primary-500 flex items-center justify-center">
                                                <Workflow className="w-5 h-5 text-white" />
                                            </div>
                                            <div>
                                                <h3 className="font-semibold group-hover:text-primary-400 transition-colors">
                                                    {workflow.name}
                                                </h3>
                                                <p className="text-sm text-gray-500">
                                                    {strategyLabels[workflow.coordination_strategy]}
                                                </p>
                                            </div>
                                        </div>
                                        <span className={clsx(statusColors[workflow.status])}>
                                            {workflow.status}
                                        </span>
                                    </div>

                                    {workflow.description && (
                                        <p className="text-sm text-gray-400 mb-4 line-clamp-2">
                                            {workflow.description}
                                        </p>
                                    )}

                                    <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
                                        <Users className="w-4 h-4" />
                                        <span>{workflow.agents.length} agent{workflow.agents.length !== 1 ? 's' : ''}</span>
                                    </div>

                                    <div className="flex items-center gap-2 pt-4 border-t border-white/5">
                                        <Link
                                            href={`/playground?workflow=${workflow.id}`}
                                            className="btn-ghost flex-1 flex items-center justify-center gap-2 text-sm"
                                        >
                                            <Play className="w-4 h-4" />
                                            Run
                                        </Link>
                                        <Link
                                            href={`/workflows/${workflow.id}`}
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
