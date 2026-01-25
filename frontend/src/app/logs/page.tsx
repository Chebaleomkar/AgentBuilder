'use client';

import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
    BarChart3, CheckCircle, XCircle, Clock,
    Bot, Workflow, Filter, RefreshCw
} from 'lucide-react';
import Link from 'next/link';
import Navbar from '@/components/layout/Navbar';
import { executionApi, Execution } from '@/lib/api';
import { clsx } from 'clsx';
import { format } from 'date-fns';

const statusConfig = {
    pending: { color: 'badge-warning', icon: Clock },
    running: { color: 'badge-info', icon: RefreshCw },
    completed: { color: 'badge-success', icon: CheckCircle },
    failed: { color: 'badge-error', icon: XCircle },
    cancelled: { color: 'text-gray-500', icon: XCircle },
};

export default function LogsPage() {
    const { data, isLoading, refetch } = useQuery({
        queryKey: ['executions'],
        queryFn: () => executionApi.list(),
        refetchInterval: 5000, // Auto-refresh every 5 seconds
    });

    return (
        <div className="min-h-screen pt-16">
            <Navbar />

            <div className="container mx-auto px-6 py-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold mb-2">Execution Logs</h1>
                        <p className="text-gray-400">Monitor agent and workflow executions</p>
                    </div>
                    <button
                        onClick={() => refetch()}
                        className="btn-secondary inline-flex items-center gap-2"
                    >
                        <RefreshCw className="w-4 h-4" />
                        Refresh
                    </button>
                </div>

                {/* Stats Cards */}
                <div className="grid md:grid-cols-4 gap-4 mb-8">
                    <div className="card">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-primary-500/10 flex items-center justify-center">
                                <BarChart3 className="w-5 h-5 text-primary-400" />
                            </div>
                            <div>
                                <div className="text-2xl font-bold">{data?.total || 0}</div>
                                <div className="text-sm text-gray-400">Total Executions</div>
                            </div>
                        </div>
                    </div>
                    <div className="card">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                                <CheckCircle className="w-5 h-5 text-emerald-400" />
                            </div>
                            <div>
                                <div className="text-2xl font-bold">
                                    {data?.executions?.filter((e: Execution) => e.status === 'completed').length || 0}
                                </div>
                                <div className="text-sm text-gray-400">Completed</div>
                            </div>
                        </div>
                    </div>
                    <div className="card">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center">
                                <XCircle className="w-5 h-5 text-red-400" />
                            </div>
                            <div>
                                <div className="text-2xl font-bold">
                                    {data?.executions?.filter((e: Execution) => e.status === 'failed').length || 0}
                                </div>
                                <div className="text-sm text-gray-400">Failed</div>
                            </div>
                        </div>
                    </div>
                    <div className="card">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                                <Clock className="w-5 h-5 text-amber-400" />
                            </div>
                            <div>
                                <div className="text-2xl font-bold">
                                    {data?.executions?.filter((e: Execution) => e.status === 'running').length || 0}
                                </div>
                                <div className="text-sm text-gray-400">Running</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Executions Table */}
                <div className="card overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-white/5">
                                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Status</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Type</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Input</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Duration</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Tokens</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Cost</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Time</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-400"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {isLoading ? (
                                    <tr>
                                        <td colSpan={8} className="py-8 text-center text-gray-500">
                                            Loading...
                                        </td>
                                    </tr>
                                ) : data?.executions?.length === 0 ? (
                                    <tr>
                                        <td colSpan={8} className="py-8 text-center text-gray-500">
                                            No executions yet
                                        </td>
                                    </tr>
                                ) : (
                                    data?.executions?.map((exec: Execution, index: number) => {
                                        const StatusIcon = statusConfig[exec.status]?.icon || Clock;
                                        return (
                                            <motion.tr
                                                key={exec.id}
                                                initial={{ opacity: 0 }}
                                                animate={{ opacity: 1 }}
                                                transition={{ delay: index * 0.02 }}
                                                className="border-b border-white/5 hover:bg-white/5"
                                            >
                                                <td className="py-3 px-4">
                                                    <span className={clsx(statusConfig[exec.status]?.color)}>
                                                        <StatusIcon className="w-3 h-3 inline mr-1" />
                                                        {exec.status}
                                                    </span>
                                                </td>
                                                <td className="py-3 px-4">
                                                    <div className="flex items-center gap-2">
                                                        {exec.agent_id ? (
                                                            <>
                                                                <Bot className="w-4 h-4 text-primary-400" />
                                                                <span className="text-sm">Agent</span>
                                                            </>
                                                        ) : (
                                                            <>
                                                                <Workflow className="w-4 h-4 text-accent-400" />
                                                                <span className="text-sm">Workflow</span>
                                                            </>
                                                        )}
                                                    </div>
                                                </td>
                                                <td className="py-3 px-4">
                                                    <div className="text-sm text-gray-400 max-w-xs truncate">
                                                        {JSON.stringify(exec.input_data).slice(0, 50)}...
                                                    </div>
                                                </td>
                                                <td className="py-3 px-4 text-sm">
                                                    {exec.duration_ms ? `${exec.duration_ms}ms` : '-'}
                                                </td>
                                                <td className="py-3 px-4 text-sm">
                                                    {exec.token_usage?.total_tokens || 0}
                                                </td>
                                                <td className="py-3 px-4 text-sm">
                                                    ${exec.cost_estimate?.toFixed(4) || '0.00'}
                                                </td>
                                                <td className="py-3 px-4 text-sm text-gray-400">
                                                    {format(new Date(exec.created_at), 'MMM d, HH:mm')}
                                                </td>
                                                <td className="py-3 px-4">
                                                    <Link
                                                        href={`/logs/${exec.id}`}
                                                        className="text-primary-400 hover:text-primary-300 text-sm"
                                                    >
                                                        Details
                                                    </Link>
                                                </td>
                                            </motion.tr>
                                        );
                                    })
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}
