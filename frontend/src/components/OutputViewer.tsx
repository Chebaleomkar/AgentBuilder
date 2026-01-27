'use client';

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    FileText, Code, Copy, Check, ChevronDown, ChevronUp,
    ExternalLink, Lightbulb, List, BookOpen, Search
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { clsx } from 'clsx';

interface OutputViewerProps {
    data: any;
    className?: string;
}

type ViewMode = 'formatted' | 'raw';

export default function OutputViewer({ data, className }: OutputViewerProps) {
    const [viewMode, setViewMode] = useState<ViewMode>('formatted');
    const [copied, setCopied] = useState(false);
    const [showSources, setShowSources] = useState(false);

    // Extract content from various response formats
    const { content, sources, metadata } = useMemo(() => {
        if (!data) return { content: '', sources: [], metadata: {} };

        let rawContent = '';
        let sources: any[] = [];
        let metadata: any = {};

        // Handle different response structures
        if (typeof data === 'string') {
            rawContent = data;
        } else if (data.result) {
            if (typeof data.result === 'string') {
                rawContent = data.result;
            } else if (data.result.response) {
                rawContent = data.result.response;
            } else {
                rawContent = JSON.stringify(data.result, null, 2);
            }
        } else if (data.raw_response) {
            rawContent = data.raw_response;
        } else if (data.response) {
            rawContent = data.response;
        } else {
            rawContent = JSON.stringify(data, null, 2);
        }

        // Extract web search results as sources
        if (data.tool_results?.web_search) {
            sources = data.tool_results.web_search;
        }

        // Extract metadata
        if (data.token_usage) {
            metadata.tokens = data.token_usage;
        }
        if (data.provider) {
            metadata.provider = data.provider;
        }
        if (data.model) {
            metadata.model = data.model;
        }
        if (data.duration_ms) {
            metadata.duration_ms = data.duration_ms;
        }

        return { content: rawContent, sources, metadata };
    }, [data]);

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(content);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    const rawJson = useMemo(() => {
        return JSON.stringify(data, null, 2);
    }, [data]);

    return (
        <div className={clsx('space-y-4', className)}>
            {/* View Mode Toggle */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 bg-dark-200 rounded-lg p-1">
                    <button
                        onClick={() => setViewMode('formatted')}
                        className={clsx(
                            'flex border items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all',
                            viewMode === 'formatted'
                                ? 'bg-primary-500 text-white'
                                : 'text-gray-400 hover:text-white'
                        )}
                    >
                        <FileText className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => setViewMode('raw')}
                        className={clsx(
                            'flex border items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all',
                            viewMode === 'raw'
                                ? 'bg-primary-500 text-white'
                                : 'text-gray-400 hover:text-white'
                        )}
                    >
                        <Code className="w-4 h-4" />
                    </button>
                </div>

                <button
                    onClick={handleCopy}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-dark-200 text-gray-400 hover:text-white transition-colors text-sm"
                >
                    {copied ? (
                        <>
                            <Check className="w-4 h-4 text-emerald-400" />
                            Copied!
                        </>
                    ) : (
                        <>
                            <Copy className="w-4 h-4" />
                            Copy
                        </>
                    )}
                </button>
            </div>

            {/* Content Area */}
            <AnimatePresence mode="wait">
                {viewMode === 'formatted' ? (
                    <motion.div
                        key="formatted"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="space-y-4"
                    >
                        {/* Metadata Bar */}
                        {Object.keys(metadata).length > 0 && (
                            <div className="flex flex-wrap gap-3 text-xs">
                                {metadata.provider && (
                                    <span className="px-2 py-1 bg-primary-500/20 text-primary-400 rounded-full">
                                        {metadata.provider}
                                    </span>
                                )}
                                {metadata.model && (
                                    <span className="px-2 py-1 bg-accent-500/20 text-accent-400 rounded-full">
                                        {metadata.model}
                                    </span>
                                )}
                                {metadata.duration_ms && (
                                    <span className="px-2 py-1 bg-white/5 text-gray-400 rounded-full">
                                        {metadata.duration_ms}ms
                                    </span>
                                )}
                                {metadata.tokens?.total_tokens && (
                                    <span className="px-2 py-1 bg-white/5 text-gray-400 rounded-full">
                                        {metadata.tokens.total_tokens} tokens
                                    </span>
                                )}
                            </div>
                        )}

                        {/* Main Content - Rendered Markdown */}
                        <div className="prose prose-invert prose-sm max-w-none 
                            prose-headings:text-white prose-headings:font-semibold prose-headings:mb-2 prose-headings:mt-4
                            prose-h1:text-xl prose-h2:text-lg prose-h3:text-base
                            prose-p:text-gray-300 prose-p:leading-relaxed prose-p:mb-3
                            prose-strong:text-white prose-strong:font-semibold
                            prose-ul:my-2 prose-ol:my-2 prose-li:text-gray-300 prose-li:my-1
                            prose-code:text-primary-400 prose-code:bg-dark-300 prose-code:px-1 prose-code:rounded
                            prose-pre:bg-dark-300 prose-pre:border prose-pre:border-white/10
                            prose-a:text-primary-400 prose-a:no-underline hover:prose-a:underline
                            prose-blockquote:border-primary-500 prose-blockquote:text-gray-400
                            prose-hr:border-white/10
                            bg-dark-200/50 rounded-xl p-6 border border-white/5"
                        >
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {content}
                            </ReactMarkdown>
                        </div>

                        {/* Sources Section */}
                        {sources.length > 0 && (
                            <div className="border border-white/10 rounded-xl overflow-hidden">
                                <button
                                    onClick={() => setShowSources(!showSources)}
                                    className="w-full flex items-center justify-between p-4 bg-dark-200/50 hover:bg-dark-200 transition-colors"
                                >
                                    <div className="flex items-center gap-2 text-sm font-medium">
                                        <Search className="w-4 h-4 text-primary-400" />
                                        <span>Sources ({sources.length})</span>
                                    </div>
                                    {showSources ? (
                                        <ChevronUp className="w-4 h-4 text-gray-400" />
                                    ) : (
                                        <ChevronDown className="w-4 h-4 text-gray-400" />
                                    )}
                                </button>

                                <AnimatePresence>
                                    {showSources && (
                                        <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: 'auto', opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            className="border-t border-white/10"
                                        >
                                            <div className="p-4 space-y-3">
                                                {sources.map((source, index) => (
                                                    <a
                                                        key={index}
                                                        href={source.url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="block p-3 rounded-lg bg-dark-300/50 hover:bg-dark-300 transition-colors group"
                                                    >
                                                        <div className="flex items-start gap-2">
                                                            <span className="flex-shrink-0 w-5 h-5 rounded bg-primary-500/20 text-primary-400 text-xs flex items-center justify-center font-medium">
                                                                {index + 1}
                                                            </span>
                                                            <div className="flex-1 min-w-0">
                                                                <h4 className="font-medium text-sm text-white group-hover:text-primary-400 transition-colors truncate">
                                                                    {source.title}
                                                                </h4>
                                                                <p className="text-xs text-gray-500 truncate mt-0.5">
                                                                    {source.url}
                                                                </p>
                                                                {source.snippet && (
                                                                    <p className="text-xs text-gray-400 mt-1 line-clamp-2">
                                                                        {source.snippet}
                                                                    </p>
                                                                )}
                                                            </div>
                                                            <ExternalLink className="w-4 h-4 text-gray-500 group-hover:text-primary-400 transition-colors flex-shrink-0" />
                                                        </div>
                                                    </a>
                                                ))}
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        )}
                    </motion.div>
                ) : (
                    <motion.div
                        key="raw"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                    >
                        <pre className="bg-dark-300 rounded-xl p-4 overflow-auto max-h-[500px] text-sm font-mono text-gray-300 border border-white/10">
                            <code>{rawJson}</code>
                        </pre>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
