'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Play, Bot, Workflow, Loader2, Send,
    CheckCircle, XCircle, Clock, Zap,
    ChevronDown, ChevronRight
} from 'lucide-react';
import toast from 'react-hot-toast';
import Navbar from '@/components/layout/Navbar';
import { agentApi, workflowApi, demoApi, Execution, ExecutionStep } from '@/lib/api';
import { clsx } from 'clsx';

type ExecutionMode = 'agent' | 'workflow' | 'demo';

const demoAgents = [
    { id: 'research', name: '🥇 Research Agent', description: 'Web search + structured reports' },
    { id: 'automation', name: '🥈 Automation Agent', description: 'Data analysis + operations' },
    { id: 'multi-agent', name: '🥉 Multi-Agent', description: 'Planner → Executor → Critic' },
];

export default function PlaygroundPage() {
    const [mode, setMode] = useState<ExecutionMode>('demo');
    const [selectedId, setSelectedId] = useState<string>('research');
    const [inputText, setInputText] = useState('');
    const [result, setResult] = useState<Execution | null>(null);
    const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());

    const { data: agentsData } = useQuery({
        queryKey: ['agents'],
        queryFn: () => agentApi.list(),
    });

    const { data: workflowsData } = useQuery({
        queryKey: ['workflows'],
        queryFn: () => workflowApi.list(),
    });

    const executeMutation = useMutation({
        mutationFn: async () => {
            if (mode === 'demo') {
                if (selectedId === 'research') {
                    return demoApi.runResearch(inputText);
                } else if (selectedId === 'automation') {
                    return demoApi.runAutomation([{ data: inputText }], 'analyze');
                } else {
                    return demoApi.runMultiAgent(inputText);
                }
            } else if (mode === 'agent') {
                return agentApi.execute(selectedId, { query: inputText });
            } else {
                return workflowApi.execute(selectedId, { task: inputText });
            }
        },
        onSuccess: (data) => {
            setResult(data);
            toast.success('Execution completed!');
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Execution failed');
        },
    });

    const handleExecute = () => {
        if (!inputText.trim()) {
            toast.error('Please enter some input');
            return;
        }
        executeMutation.mutate();
    };

    const toggleStep = (stepId: string) => {
        const newExpanded = new Set(expandedSteps);
        if (newExpanded.has(stepId)) {
            newExpanded.delete(stepId);
        } else {
            newExpanded.add(stepId);
        }
        setExpandedSteps(newExpanded);
    };

    const stepStatusIcon = (status: string) => {
        switch (status) {
            case 'completed':
                return <CheckCircle className="w-4 h-4 text-emerald-400" />;
            case 'failed':
                return <XCircle className="w-4 h-4 text-red-400" />;
            case 'running':
                return <Loader2 className="w-4 h-4 text-primary-400 animate-spin" />;
            default:
                return <Clock className="w-4 h-4 text-gray-400" />;
        }
    };

    return (
        <div className="min-h-screen pt-16">
            <Navbar />

            <div className="container mx-auto px-6 py-8">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold mb-2">Execution Playground</h1>
                    <p className="text-gray-400">Run agents and workflows, observe execution in real-time</p>
                </div>

                <div className="grid lg:grid-cols-2 gap-8">
                    {/* Input Panel */}
                    <div className="space-y-6">
                        {/* Mode Selector */}
                        <div className="card">
                            <h2 className="text-lg font-semibold mb-4">Select Mode</h2>
                            <div className="flex gap-2">
                                {(['demo', 'agent', 'workflow'] as ExecutionMode[]).map((m) => (
                                    <button
                                        key={m}
                                        onClick={() => setMode(m)}
                                        className={clsx(
                                            'px-4 py-2 rounded-lg capitalize transition-all',
                                            mode === m
                                                ? 'bg-primary-500 text-white'
                                                : 'bg-dark-100 text-gray-400 hover:text-white'
                                        )}
                                    >
                                        {m}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Selection */}
                        <div className="card">
                            <h2 className="text-lg font-semibold mb-4">
                                {mode === 'demo' ? 'Demo Agents' : mode === 'agent' ? 'Select Agent' : 'Select Workflow'}
                            </h2>

                            {mode === 'demo' && (
                                <div className="space-y-2">
                                    {demoAgents.map((demo) => (
                                        <button
                                            key={demo.id}
                                            onClick={() => setSelectedId(demo.id)}
                                            className={clsx(
                                                'w-full p-4 rounded-lg border text-left transition-all',
                                                selectedId === demo.id
                                                    ? 'border-primary-500 bg-primary-500/10'
                                                    : 'border-white/10 hover:border-white/20'
                                            )}
                                        >
                                            <div className="font-medium">{demo.name}</div>
                                            <div className="text-sm text-gray-400">{demo.description}</div>
                                        </button>
                                    ))}
                                </div>
                            )}

                            {mode === 'agent' && (
                                <div className="space-y-2">
                                    {agentsData?.agents?.map((agent: any) => (
                                        <button
                                            key={agent.id}
                                            onClick={() => setSelectedId(agent.id)}
                                            className={clsx(
                                                'w-full p-4 rounded-lg border text-left transition-all',
                                                selectedId === agent.id
                                                    ? 'border-primary-500 bg-primary-500/10'
                                                    : 'border-white/10 hover:border-white/20'
                                            )}
                                        >
                                            <div className="flex items-center gap-2">
                                                <Bot className="w-4 h-4 text-primary-400" />
                                                <span className="font-medium">{agent.name}</span>
                                            </div>
                                            <div className="text-sm text-gray-400">{agent.role}</div>
                                        </button>
                                    )) || <p className="text-gray-500">No agents found</p>}
                                </div>
                            )}

                            {mode === 'workflow' && (
                                <div className="space-y-2">
                                    {workflowsData?.workflows?.map((wf: any) => (
                                        <button
                                            key={wf.id}
                                            onClick={() => setSelectedId(wf.id)}
                                            className={clsx(
                                                'w-full p-4 rounded-lg border text-left transition-all',
                                                selectedId === wf.id
                                                    ? 'border-primary-500 bg-primary-500/10'
                                                    : 'border-white/10 hover:border-white/20'
                                            )}
                                        >
                                            <div className="flex items-center gap-2">
                                                <Workflow className="w-4 h-4 text-accent-400" />
                                                <span className="font-medium">{wf.name}</span>
                                            </div>
                                            <div className="text-sm text-gray-400">{wf.description}</div>
                                        </button>
                                    )) || <p className="text-gray-500">No workflows found</p>}
                                </div>
                            )}
                        </div>

                        {/* Input */}
                        <div className="card">
                            <h2 className="text-lg font-semibold mb-4">Input</h2>
                            <textarea
                                value={inputText}
                                onChange={(e) => setInputText(e.target.value)}
                                placeholder={
                                    mode === 'demo' && selectedId === 'research'
                                        ? 'Enter a research topic... e.g., "AI browser automation competitors"'
                                        : 'Enter your prompt or task...'
                                }
                                className="textarea h-32 mb-4"
                            />
                            <button
                                onClick={handleExecute}
                                disabled={executeMutation.isPending}
                                className="btn-primary w-full flex items-center justify-center gap-2"
                            >
                                {executeMutation.isPending ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        Executing...
                                    </>
                                ) : (
                                    <>
                                        <Play className="w-5 h-5" />
                                        Execute
                                    </>
                                )}
                            </button>
                        </div>
                    </div>

                    {/* Results Panel */}
                    <div className="space-y-6">
                        {/* Status */}
                        {result && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="card"
                            >
                                <div className="flex items-center justify-between mb-4">
                                    <h2 className="text-lg font-semibold">Execution Result</h2>
                                    <span className={clsx(
                                        result.status === 'completed' && 'badge-success',
                                        result.status === 'failed' && 'badge-error',
                                        result.status === 'running' && 'badge-info',
                                    )}>
                                        {result.status}
                                    </span>
                                </div>

                                {/* Metrics */}
                                <div className="grid grid-cols-3 gap-4 mb-6">
                                    <div className="bg-dark-200 rounded-lg p-3">
                                        <div className="text-xs text-gray-500 mb-1">Duration</div>
                                        <div className="font-medium">{result.duration_ms || 0}ms</div>
                                    </div>
                                    <div className="bg-dark-200 rounded-lg p-3">
                                        <div className="text-xs text-gray-500 mb-1">Tokens</div>
                                        <div className="font-medium">{result.token_usage?.total_tokens || 0}</div>
                                    </div>
                                    <div className="bg-dark-200 rounded-lg p-3">
                                        <div className="text-xs text-gray-500 mb-1">Cost</div>
                                        <div className="font-medium">${result.cost_estimate?.toFixed(4) || '0.00'}</div>
                                    </div>
                                </div>

                                {/* Output */}
                                {result.output_data && (
                                    <div className="mb-6">
                                        <h3 className="text-sm font-medium mb-2 text-gray-400">Output</h3>
                                        <pre className="bg-dark-300 rounded-lg p-4 overflow-auto max-h-64 text-sm">
                                            {JSON.stringify(result.output_data, null, 2)}
                                        </pre>
                                    </div>
                                )}

                                {/* Error */}
                                {result.error_message && (
                                    <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                                        <div className="text-red-400 text-sm">{result.error_message}</div>
                                    </div>
                                )}
                            </motion.div>
                        )}

                        {/* Execution Steps */}
                        {result?.steps && result.steps.length > 0 && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.1 }}
                                className="card"
                            >
                                <h2 className="text-lg font-semibold mb-4">Execution Steps</h2>
                                <div className="space-y-2">
                                    {result.steps.map((step: ExecutionStep) => (
                                        <div key={step.id} className="border border-white/5 rounded-lg overflow-hidden">
                                            <button
                                                onClick={() => toggleStep(step.id)}
                                                className="w-full flex items-center gap-3 p-3 hover:bg-white/5 transition-colors"
                                            >
                                                {expandedSteps.has(step.id) ? (
                                                    <ChevronDown className="w-4 h-4" />
                                                ) : (
                                                    <ChevronRight className="w-4 h-4" />
                                                )}
                                                {stepStatusIcon(step.status)}
                                                <span className="flex-1 text-left font-medium text-sm">{step.step_name}</span>
                                                {step.duration_ms && (
                                                    <span className="text-xs text-gray-500">{step.duration_ms}ms</span>
                                                )}
                                            </button>

                                            <AnimatePresence>
                                                {expandedSteps.has(step.id) && (
                                                    <motion.div
                                                        initial={{ height: 0, opacity: 0 }}
                                                        animate={{ height: 'auto', opacity: 1 }}
                                                        exit={{ height: 0, opacity: 0 }}
                                                        className="border-t border-white/5"
                                                    >
                                                        <div className="p-3 space-y-3">
                                                            {step.input_data && Object.keys(step.input_data).length > 0 && (
                                                                <div>
                                                                    <div className="text-xs text-gray-500 mb-1">Input</div>
                                                                    <pre className="text-xs bg-dark-300 p-2 rounded overflow-auto max-h-24">
                                                                        {JSON.stringify(step.input_data, null, 2)}
                                                                    </pre>
                                                                </div>
                                                            )}
                                                            {step.output_data && (
                                                                <div>
                                                                    <div className="text-xs text-gray-500 mb-1">Output</div>
                                                                    <pre className="text-xs bg-dark-300 p-2 rounded overflow-auto max-h-24">
                                                                        {JSON.stringify(step.output_data, null, 2)}
                                                                    </pre>
                                                                </div>
                                                            )}
                                                            {step.tool_calls && step.tool_calls.length > 0 && (
                                                                <div>
                                                                    <div className="text-xs text-gray-500 mb-1">Tool Calls</div>
                                                                    {step.tool_calls.map((tc: any, i: number) => (
                                                                        <div key={i} className="flex items-center gap-2 text-xs">
                                                                            <Zap className="w-3 h-3 text-amber-400" />
                                                                            <span>{tc.tool_name}</span>
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            )}
                                                        </div>
                                                    </motion.div>
                                                )}
                                            </AnimatePresence>
                                        </div>
                                    ))}
                                </div>
                            </motion.div>
                        )}

                        {/* Empty State */}
                        {!result && !executeMutation.isPending && (
                            <div className="card text-center py-16">
                                <Play className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                                <h3 className="text-xl font-semibold mb-2">Ready to Execute</h3>
                                <p className="text-gray-400">Select an agent or workflow and enter your input</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
