'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import {
    Bot,
    Workflow,
    Play,
    BarChart3,
    Sparkles,
    ArrowRight,
    Zap,
    Shield,
    Eye
} from 'lucide-react';
import Navbar from '@/components/layout/Navbar';

const features = [
    {
        icon: Bot,
        title: 'Agent Builder',
        description: 'Create AI agents with simple forms. Define role, goal, instructions, and select tools.',
        href: '/agents/create',
        color: 'from-primary-500 to-primary-600',
    },
    {
        icon: Workflow,
        title: 'Workflow Designer',
        description: 'Build multi-agent workflows with sequential, parallel, or conditional execution.',
        href: '/workflows/create',
        color: 'from-accent-500 to-accent-600',
    },
    {
        icon: Play,
        title: 'Execution Playground',
        description: 'Run agents and workflows, see real-time execution with tool calls and responses.',
        href: '/playground',
        color: 'from-emerald-500 to-emerald-600',
    },
    {
        icon: BarChart3,
        title: 'Logs & Monitoring',
        description: 'Deep observability into execution steps, tool calls, errors, and token usage.',
        href: '/logs',
        color: 'from-orange-500 to-orange-600',
    },
];

const demoAgents = [
    {
        title: '🥇 Research Agent',
        description: 'Searches web + documents, produces structured reports',
        capabilities: ['Web Search', 'RAG', 'Summarization'],
    },
    {
        title: '🥈 Automation Agent',
        description: 'Executes operational tasks with deterministic outputs',
        capabilities: ['Data Analysis', 'File Processing', 'API Calls'],
    },
    {
        title: '🥉 Multi-Agent Orchestrator',
        description: 'Planner → Executor → Critic workflow',
        capabilities: ['Agent Coordination', 'Sequential Execution', 'Quality Review'],
    },
];

export default function HomePage() {
    return (
        <div className="min-h-screen">
            <Navbar />

            {/* Hero Section */}
            <section className="relative overflow-hidden pt-20 pb-32">
                {/* Background decorations */}
                <div className="absolute inset-0 overflow-hidden">
                    <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary-500/20 rounded-full blur-3xl" />
                    <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-accent-500/20 rounded-full blur-3xl" />
                </div>

                <div className="container mx-auto px-6 relative z-10">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6 }}
                        className="text-center max-w-4xl mx-auto"
                    >
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-500/10 border border-primary-500/20 mb-6">
                            <Sparkles className="w-4 h-4 text-primary-400" />
                            <span className="text-sm text-primary-300">UI-first AI Agent Platform</span>
                        </div>

                        <h1 className="text-5xl md:text-7xl font-bold mb-6">
                            <span className="gradient-text">AgentBuilder</span>
                        </h1>

                        <p className="text-xl md:text-2xl text-gray-400 mb-8 max-w-2xl mx-auto">
                            Build, run, and observe AI agents with ease. Create powerful automations without writing code.
                        </p>

                        <div className="flex flex-col sm:flex-row gap-4 justify-center">
                            <Link href="/agents/create" className="btn-primary inline-flex items-center gap-2 text-lg px-8 py-4">
                                Create Agent
                                <ArrowRight className="w-5 h-5" />
                            </Link>
                            <Link href="/playground" className="btn-secondary inline-flex items-center gap-2 text-lg px-8 py-4">
                                <Play className="w-5 h-5" />
                                Try Playground
                            </Link>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Features Grid */}
            <section className="py-20 relative">
                <div className="container mx-auto px-6">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="text-center mb-16"
                    >
                        <h2 className="text-3xl md:text-4xl font-bold mb-4">
                            Everything You Need
                        </h2>
                        <p className="text-gray-400 text-lg max-w-2xl mx-auto">
                            From agent creation to execution monitoring, all in one platform.
                        </p>
                    </motion.div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {features.map((feature, index) => (
                            <motion.div
                                key={feature.title}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: index * 0.1 }}
                            >
                                <Link href={feature.href} className="block card-hover group h-full">
                                    <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                                        <feature.icon className="w-6 h-6 text-white" />
                                    </div>
                                    <h3 className="text-xl font-semibold mb-2 group-hover:text-primary-400 transition-colors">
                                        {feature.title}
                                    </h3>
                                    <p className="text-gray-400 text-sm">
                                        {feature.description}
                                    </p>
                                </Link>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Demo Agents Section */}
            <section className="py-20 relative">
                <div className="container mx-auto px-6">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="text-center mb-16"
                    >
                        <h2 className="text-3xl md:text-4xl font-bold mb-4">
                            Pre-built Demo Agents
                        </h2>
                        <p className="text-gray-400 text-lg max-w-2xl mx-auto">
                            Get started instantly with our showcase agents that demonstrate platform capabilities.
                        </p>
                    </motion.div>

                    <div className="grid md:grid-cols-3 gap-6">
                        {demoAgents.map((agent, index) => (
                            <motion.div
                                key={agent.title}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: index * 0.1 }}
                                className="card-hover"
                            >
                                <h3 className="text-xl font-semibold mb-2">{agent.title}</h3>
                                <p className="text-gray-400 text-sm mb-4">{agent.description}</p>
                                <div className="flex flex-wrap gap-2">
                                    {agent.capabilities.map((cap) => (
                                        <span key={cap} className="badge-info">{cap}</span>
                                    ))}
                                </div>
                            </motion.div>
                        ))}
                    </div>

                    <div className="text-center mt-10">
                        <Link href="/playground" className="btn-primary inline-flex items-center gap-2">
                            Try Demo Agents
                            <ArrowRight className="w-4 h-4" />
                        </Link>
                    </div>
                </div>
            </section>

            {/* Key Benefits */}
            <section className="py-20 relative">
                <div className="container mx-auto px-6">
                    <div className="grid md:grid-cols-3 gap-8">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            className="text-center"
                        >
                            <div className="w-16 h-16 rounded-2xl bg-primary-500/10 border border-primary-500/20 flex items-center justify-center mx-auto mb-4">
                                <Zap className="w-8 h-8 text-primary-400" />
                            </div>
                            <h3 className="text-xl font-semibold mb-2">Lightning Fast</h3>
                            <p className="text-gray-400">Create and deploy agents in minutes, not hours.</p>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: 0.1 }}
                            className="text-center"
                        >
                            <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-4">
                                <Eye className="w-8 h-8 text-emerald-400" />
                            </div>
                            <h3 className="text-xl font-semibold mb-2">Full Observability</h3>
                            <p className="text-gray-400">See every step, tool call, and token in real-time.</p>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: 0.2 }}
                            className="text-center"
                        >
                            <div className="w-16 h-16 rounded-2xl bg-accent-500/10 border border-accent-500/20 flex items-center justify-center mx-auto mb-4">
                                <Shield className="w-8 h-8 text-accent-400" />
                            </div>
                            <h3 className="text-xl font-semibold mb-2">Enterprise Ready</h3>
                            <p className="text-gray-400">Built on production-grade infrastructure.</p>
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-10 border-t border-white/5">
                <div className="container mx-auto px-6 text-center text-gray-500">
                    <p>Built with ❤️ using agenticaiframework</p>
                </div>
            </footer>
        </div>
    );
}
