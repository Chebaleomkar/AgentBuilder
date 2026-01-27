'use client';

import { useState, useEffect, Suspense } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useSearchParams, useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Play, Bot, Workflow, Loader2, Send,
    CheckCircle, XCircle, Clock, Zap,
    ChevronDown, ChevronRight, ArrowLeft,
    ExternalLink, Settings, Info
} from 'lucide-react';
import toast from 'react-hot-toast';
import Navbar from '@/components/layout/Navbar';
import OutputViewer from '@/components/OutputViewer';
import { agentApi, workflowApi, demoApi, Execution, ExecutionStep } from '@/lib/api';
import { clsx } from 'clsx';

type ExecutionMode = 'agent' | 'workflow' | 'demo';

const demoAgents = [
    { id: 'research', name: '🥇 Research Agent', description: 'Web search + structured reports' },
    { id: 'automation', name: '🥈 Automation Agent', description: 'Data analysis + operations' },
    { id: 'multi-agent', name: '🥉 Multi-Agent', description: 'Planner → Executor → Critic' },
];

function PlaygroundSkeleton() {
    return (
        <div className="min-h-screen pt-16 flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
        </div>
    );
}

function PlaygroundContent() {
    const searchParams = useSearchParams();
    const router = useRouter();

    // Initial state from URL
    const urlAgentId = searchParams.get('agent');
    const urlMode = searchParams.get('mode') as ExecutionMode;
    const urlId = searchParams.get('id');

    const [mode, setMode] = useState<ExecutionMode>(urlAgentId ? 'agent' : (urlMode || 'demo'));
    const [selectedId, setSelectedId] = useState<string>(urlAgentId || urlId || 'research');
    const [inputText, setInputText] = useState('');
    const [result, setResult] = useState<Execution | null>(null);
    const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());

    // Sync state if URL params change
    useEffect(() => {
        const agentId = searchParams.get('agent');
        const m = searchParams.get('mode') as ExecutionMode;
        const id = searchParams.get('id');

        if (agentId) {
            setMode('agent');
            setSelectedId(agentId);
        } else if (m) {
            setMode(m);
            if (id) setSelectedId(id);
        }
    }, [searchParams]);

    const isSingleAgentMode = !!urlAgentId;

    const { data: agentsData } = useQuery({
        queryKey: ['agents'],
        queryFn: () => agentApi.list(),
    });

    const { data: workflowsData } = useQuery({
        queryKey: ['workflows'],
        queryFn: () => workflowApi.list(),
    });

    const { data: currentAgent } = useQuery({
        queryKey: ['agent', selectedId],
        queryFn: () => agentApi.get(selectedId),
        enabled: mode === 'agent' && !!selectedId,
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

    const selectedTitle = isSingleAgentMode
        ? (currentAgent?.name || 'Agent Execution')
        : mode === 'demo'
            ? demoAgents.find(d => d.id === selectedId)?.name || 'Demo Execution'
            : mode === 'agent'
                ? agentsData?.agents?.find((a: any) => a.id === selectedId)?.name || 'Agent Execution'
                : workflowsData?.workflows?.find((w: any) => w.id === selectedId)?.name || 'Workflow Execution';

    return (
        <div className="min-h-screen pt-16">
            <Navbar />

            <div className="container mx-auto px-6 py-8">
                <div className="mb-8 flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold mb-2">
                            {isSingleAgentMode ? 'Agent Execution' : 'Execution Playground'}
                        </h1>
                        <p className="text-gray-400">
                            {isSingleAgentMode
                                ? `Running focused execution for ${currentAgent?.name || 'selected agent'}`
                                : 'Run agents and workflows, observe execution in real-time'}
                        </p>
                    </div>
                    {isSingleAgentMode && (
                        <button
                            onClick={() => router.push('/playground')}
                            className="btn-secondary flex items-center gap-2"
                        >
                            <ArrowLeft className="w-4 h-4" />
                            Back to All Agents
                        </button>
                    )}
                </div>

                <div className="grid lg:grid-cols-2 gap-8">
                    {/* Input Panel */}
                    <div className="space-y-6">
                        {!isSingleAgentMode ? (
                            <>
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
                            </>
                        ) : (
                            /* Focused Agent Info Card */
                            <div className="card border-primary-500/20 bg-primary-500/5">
                                <div className="flex items-center gap-4 mb-6">
                                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
                                        <Bot className="w-6 h-6 text-white" />
                                    </div>
                                    <div>
                                        <h2 className="text-xl font-bold">{currentAgent?.name || 'Loading Agent...'}</h2>
                                        <p className="text-sm text-gray-400">{currentAgent?.role}</p>
                                    </div>
                                </div>

                                {currentAgent?.goal && (
                                    <div className="mb-4">
                                        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Goal</h3>
                                        <p className="text-sm text-gray-300">{currentAgent.goal}</p>
                                    </div>
                                )}

                                {currentAgent?.tools && currentAgent.tools.length > 0 && (
                                    <div className="mb-6">
                                        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Capabilities</h3>
                                        <div className="flex flex-wrap gap-2">
                                            {currentAgent.tools.map((tool: string) => (
                                                <span key={tool} className="px-2 py-1 bg-dark-200 rounded text-xs text-primary-400 border border-primary-500/20">
                                                    {tool}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                <div className="flex gap-2">
                                    <button
                                        onClick={() => router.push(`/agents/${selectedId}`)}
                                        className="btn-ghost flex-1 text-xs py-2"
                                    >
                                        <Settings className="w-3.5 h-3.5 mr-2" />
                                        Configure
                                    </button>
                                    <button
                                        onClick={() => router.push('/playground')}
                                        className="btn-ghost flex-1 text-xs py-2"
                                    >
                                        <ExternalLink className="w-3.5 h-3.5 mr-2" />
                                        Full Playground
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Input */}
                        <div className="card">
                            <h2 className="text-lg font-semibold mb-4 flex items-center justify-between">
                                <span>Input</span>
                                {isSingleAgentMode && (
                                    <span className="text-xs px-2 py-1 bg-emerald-500/10 text-emerald-400 rounded-lg">
                                        Target: {currentAgent?.name}
                                    </span>
                                )}
                            </h2>
                            <textarea
                                value={inputText}
                                onChange={(e) => setInputText(e.target.value)}
                                placeholder={
                                    mode === 'demo' && selectedId === 'research'
                                        ? 'Enter a research topic... e.g., "AI browser automation competitors"'
                                        : `Send a prompt or task to ${isSingleAgentMode ? currentAgent?.name : 'the agent'}...`
                                }
                                className="textarea h-32 mb-4"
                            />
                            <button
                                onClick={handleExecute}
                                disabled={executeMutation.isPending}
                                className="btn-primary w-full flex items-center justify-center gap-2 py-3"
                            >
                                {executeMutation.isPending ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        Executing...
                                    </>
                                ) : (
                                    <>
                                        <Play className="w-5 h-5" />
                                        Run {isSingleAgentMode ? 'Agent' : 'Execution'}
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
                                    <h2 className="text-lg font-semibold">Results for {selectedTitle}</h2>
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

                                {/* Output - Using new OutputViewer */}
                                {result.output_data && (
                                    <OutputViewer data={result.output_data} />
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
                                <h3 className="text-xl font-semibold mb-2">
                                    {isSingleAgentMode ? `Ready to Run ${currentAgent?.name}` : 'Ready to Execute'}
                                </h3>
                                <p className="text-gray-400">
                                    {isSingleAgentMode
                                        ? 'Enter your prompt and click Execute to start'
                                        : 'Select an agent or workflow and enter your input'}
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function PlaygroundPage() {
    return (
        <Suspense fallback={<PlaygroundSkeleton />}>
            <PlaygroundContent />
        </Suspense>
    );
}

