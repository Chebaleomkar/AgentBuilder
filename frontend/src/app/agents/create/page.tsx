'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Bot, ArrowLeft, Save, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';
import Navbar from '@/components/layout/Navbar';
import { agentApi, toolApi, AgentCreate } from '@/lib/api';

const models = [
    // OpenAI Models
    { id: 'gpt-4', name: 'GPT-4', description: 'Most capable, best for complex tasks', provider: 'OpenAI' },
    { id: 'gpt-4-turbo', name: 'GPT-4 Turbo', description: 'Faster, great balance of speed & quality', provider: 'OpenAI' },
    { id: 'gpt-4o', name: 'GPT-4o', description: 'Latest GPT-4 optimized model', provider: 'OpenAI' },
    { id: 'gpt-4o-mini', name: 'GPT-4o Mini', description: 'Smaller, faster, cost-effective', provider: 'OpenAI' },
    { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', description: 'Fast and cost-effective', provider: 'OpenAI' },
    // Google Gemini Models
    { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro', description: 'Most capable Gemini model', provider: 'Google' },
    { id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash', description: 'Fast and efficient', provider: 'Google' },
    { id: 'gemini-2.0-flash-exp', name: 'Gemini 2.0 Flash', description: 'Latest experimental model', provider: 'Google' },
    { id: 'gemini-pro', name: 'Gemini Pro', description: 'Balanced performance', provider: 'Google' },
];

const memoryTypes = [
    { id: 'session', name: 'Session', description: 'Memory cleared after each run' },
    { id: 'persistent', name: 'Persistent', description: 'Memory persists across runs' },
    { id: 'knowledge', name: 'Knowledge Base', description: 'Vector-store backed memory' },
];

export default function CreateAgentPage() {
    const router = useRouter();

    const [formData, setFormData] = useState<AgentCreate>({
        name: '',
        role: '',
        goal: '',
        instructions: '',
        model: 'gpt-4',
        temperature: 0.7,
        tools: [],
        memory_type: 'session',
    });

    const { data: toolsData } = useQuery({
        queryKey: ['tools'],
        queryFn: () => toolApi.list(),
    });

    const createMutation = useMutation({
        mutationFn: agentApi.create,
        onSuccess: (data) => {
            toast.success('Agent created successfully!');
            router.push(`/agents/${data.id}`);
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Failed to create agent');
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.name || !formData.role) {
            toast.error('Name and role are required');
            return;
        }
        createMutation.mutate(formData);
    };

    const toggleTool = (toolName: string) => {
        setFormData((prev) => ({
            ...prev,
            tools: prev.tools?.includes(toolName)
                ? prev.tools.filter((t) => t !== toolName)
                : [...(prev.tools || []), toolName],
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
                        <h1 className="text-3xl font-bold mb-1">Create Agent</h1>
                        <p className="text-gray-400">Define your AI agent's role, capabilities, and behavior</p>
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
                                <Bot className="w-5 h-5 text-primary-400" />
                                Basic Information
                            </h2>

                            <div className="grid md:grid-cols-2 gap-6">
                                <div>
                                    <label className="block text-sm font-medium mb-2">Agent Name *</label>
                                    <input
                                        type="text"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        placeholder="e.g., Research Assistant"
                                        className="input"
                                        required
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium mb-2">Role *</label>
                                    <input
                                        type="text"
                                        value={formData.role}
                                        onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                                        placeholder="e.g., Research Specialist"
                                        className="input"
                                        required
                                    />
                                </div>
                            </div>

                            <div className="mt-6">
                                <label className="block text-sm font-medium mb-2">Goal</label>
                                <input
                                    type="text"
                                    value={formData.goal}
                                    onChange={(e) => setFormData({ ...formData, goal: e.target.value })}
                                    placeholder="What should this agent accomplish?"
                                    className="input"
                                />
                            </div>

                            <div className="mt-6">
                                <label className="block text-sm font-medium mb-2">Instructions / Behavior</label>
                                <textarea
                                    value={formData.instructions}
                                    onChange={(e) => setFormData({ ...formData, instructions: e.target.value })}
                                    placeholder="Detailed instructions for how the agent should behave..."
                                    className="textarea h-32"
                                />
                            </div>
                        </motion.div>

                        {/* Model Settings */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="card"
                        >
                            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                                <Sparkles className="w-5 h-5 text-accent-400" />
                                Model Settings
                            </h2>

                            <div className="grid md:grid-cols-3 gap-4 mb-6">
                                {models.map((model) => (
                                    <button
                                        key={model.id}
                                        type="button"
                                        onClick={() => setFormData({ ...formData, model: model.id })}
                                        className={`p-4 rounded-lg border text-left transition-all ${formData.model === model.id
                                            ? 'border-primary-500 bg-primary-500/10'
                                            : 'border-white/10 hover:border-white/20'
                                            }`}
                                    >
                                        <div className="font-medium mb-1">{model.name}</div>
                                        <div className="text-xs text-gray-400">{model.description}</div>
                                    </button>
                                ))}
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-2">
                                    Temperature: {formData.temperature}
                                </label>
                                <input
                                    type="range"
                                    min="0"
                                    max="2"
                                    step="0.1"
                                    value={formData.temperature}
                                    onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                                    className="w-full accent-primary-500"
                                />
                                <div className="flex justify-between text-xs text-gray-500 mt-1">
                                    <span>Precise (0)</span>
                                    <span>Balanced (1)</span>
                                    <span>Creative (2)</span>
                                </div>
                            </div>
                        </motion.div>

                        {/* Tools */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="card"
                        >
                            <h2 className="text-xl font-semibold mb-6">Tools</h2>
                            <p className="text-gray-400 text-sm mb-4">
                                Select the tools this agent can use during execution
                            </p>

                            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
                                {toolsData?.tools?.map((tool: any) => (
                                    <button
                                        key={tool.name}
                                        type="button"
                                        onClick={() => toggleTool(tool.name)}
                                        className={`p-3 rounded-lg border text-left transition-all ${formData.tools?.includes(tool.name)
                                            ? 'border-primary-500 bg-primary-500/10'
                                            : 'border-white/10 hover:border-white/20'
                                            }`}
                                    >
                                        <div className="font-medium text-sm mb-1">{tool.name}</div>
                                        <div className="text-xs text-gray-400 line-clamp-2">{tool.description}</div>
                                    </button>
                                )) || (
                                        <p className="text-gray-500 col-span-full">Loading tools...</p>
                                    )}
                            </div>
                        </motion.div>

                        {/* Memory */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.3 }}
                            className="card"
                        >
                            <h2 className="text-xl font-semibold mb-6">Memory</h2>

                            <div className="grid md:grid-cols-3 gap-4">
                                {memoryTypes.map((mem) => (
                                    <button
                                        key={mem.id}
                                        type="button"
                                        onClick={() => setFormData({ ...formData, memory_type: mem.id as any })}
                                        className={`p-4 rounded-lg border text-left transition-all ${formData.memory_type === mem.id
                                            ? 'border-primary-500 bg-primary-500/10'
                                            : 'border-white/10 hover:border-white/20'
                                            }`}
                                    >
                                        <div className="font-medium mb-1">{mem.name}</div>
                                        <div className="text-xs text-gray-400">{mem.description}</div>
                                    </button>
                                ))}
                            </div>
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
                                        Create Agent
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
