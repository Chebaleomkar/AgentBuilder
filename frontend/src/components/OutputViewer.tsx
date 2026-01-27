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
import { Database } from 'lucide-react';

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
    const { content, structured, sources, knowledgeAtoms, metadata } = useMemo(() => {
        if (!data) return { content: '', structured: null, sources: [], knowledgeAtoms: [], metadata: {} };

        let rawContent = '';
        let structured: any = null;
        let sources: any[] = [];
        let knowledgeAtoms: any[] = [];
        let metadata: any = {};

        // Helper to recursively find content in nested results
        const findContent = (obj: any): any => {
            if (!obj) return null;
            if (typeof obj === 'string') return obj;

            // Priority 1: Structured fields
            if (obj.content || obj.summary || obj.title || obj.key_points) {
                return obj;
            }

            // Priority 2: Look into 'result' or 'response'
            if (obj.result) return findContent(obj.result);
            if (obj.response) return findContent(obj.response);

            return null;
        };

        const result = findContent(data);

        if (typeof result === 'string') {
            rawContent = result;
        } else if (result && typeof result === 'object') {
            structured = result;
            rawContent = result.content || result.response || '';

            // If rawContent still looks like JSON (e.g. LLM double wrapped it), try to parse it
            if (rawContent.trim().startsWith('{')) {
                try {
                    const parsed = JSON.parse(rawContent);
                    if (parsed.content) rawContent = parsed.content;
                } catch (e) {
                    // Not valid JSON or no content field, keep as is
                }
            }
        } else {
            rawContent = JSON.stringify(data, null, 2);
        }

        // Clean up rawContent from any leftover JSON structure that might have leaked
        if (rawContent.includes('"title":') && rawContent.includes('"content":')) {
            // Regex to find a JSON block and take only the content or the part after it
            rawContent = rawContent.replace(/\{[\s\S]*?"content":\s*"(.*?)"[\s\S]*?\}/g, '$1');
        }

        // Extract metadata and sources from original data
        if (data.tool_results?.web_search) {
            sources = data.tool_results.web_search;
        }

        // Parse RAG search results if they exist as a string
        if (data.tool_results?.rag_search && typeof data.tool_results.rag_search === 'string') {
            const atomMatches = data.tool_results.rag_search.matchAll(/ATOM \d+ \(Source: (.*?) \| Confidence: (\d+)%\):\n([\s\S]*?)(?=\nATOM \d+|$|### END)/g);
            for (const match of atomMatches) {
                knowledgeAtoms.push({
                    source: match[1],
                    confidence: match[2],
                    text: match[3].trim()
                });
            }
        }

        // If structured has sources list, combine them
        if (structured?.sources) {
            const extraSources = Array.isArray(structured.sources)
                ? structured.sources.map((s: any) => typeof s === 'string' ? { title: s, url: '#' } : s)
                : [];
            sources = [...sources, ...extraSources];
        }

        if (data.token_usage) metadata.tokens = data.token_usage;
        if (data.provider) metadata.provider = data.provider;
        if (data.model) metadata.model = data.model;
        if (data.duration_ms) metadata.duration_ms = data.duration_ms;

        return { content: rawContent, structured, sources, knowledgeAtoms, metadata };
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

                        {/* Structured Title */}
                        {structured?.title && (
                            <h2 className="text-2xl font-bold text-white mb-2 leading-tight">
                                {structured.title}
                            </h2>
                        )}

                        {/* Structured Summary */}
                        {structured?.summary && (
                            <div className="bg-primary-500/10 border border-primary-500/20 rounded-xl p-4 flex gap-4">
                                <Lightbulb className="w-6 h-6 text-primary-400 flex-shrink-0 mt-1" />
                                <div>
                                    <div className="text-sm font-semibold text-primary-400 uppercase tracking-wider mb-1">
                                        Summary
                                    </div>
                                    <p className="text-gray-300 leading-relaxed">
                                        {structured.summary}
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Grounding Context Selector (RAG Atoms) */}
                        {knowledgeAtoms.length > 0 && (
                            <div className="bg-emerald-500/5 border border-emerald-500/10 rounded-xl overflow-hidden mb-6">
                                <div className="px-4 py-2 bg-emerald-500/10 border-b border-emerald-500/10 flex items-center justify-between">
                                    <div className="flex items-center gap-2 text-[10px] font-bold text-emerald-400 uppercase tracking-widest">
                                        <Database className="w-3 h-3" />
                                        Knowledge Base Grounding
                                    </div>
                                    <div className="text-[10px] text-emerald-500/60 font-mono">
                                        {knowledgeAtoms.length} Context Atoms
                                    </div>
                                </div>
                                <div className="p-4 flex gap-3 overflow-x-auto scrollbar-hide">
                                    {knowledgeAtoms.map((atom: any, i: number) => (
                                        <div key={i} className="flex-shrink-0 w-64 bg-dark-300/50 border border-white/5 rounded-lg p-3 group hover:border-emerald-500/30 transition-colors">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-[10px] font-semibold text-gray-400 truncate max-w-[120px]">
                                                    {atom.source}
                                                </span>
                                                <span className="text-[10px] font-bold text-emerald-400">
                                                    {atom.confidence}%
                                                </span>
                                            </div>
                                            <p className="text-[11px] text-gray-500 line-clamp-3 leading-relaxed">
                                                {atom.text}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Main Content - Rendered Markdown */}
                        {content && (
                            <div className="prose prose-invert prose-sm max-w-none 
                                prose-headings:text-white prose-headings:font-bold prose-headings:mb-4 prose-headings:mt-8
                                prose-h1:text-3xl prose-h1:mb-6
                                prose-h2:text-2xl prose-h2:border-b prose-h2:border-white/5 prose-h2:pb-2
                                prose-h3:text-xl
                                prose-p:text-gray-300 prose-p:leading-relaxed prose-p:mb-5 prose-p:text-[15px]
                                prose-strong:text-white prose-strong:font-bold
                                prose-ul:my-5 prose-ol:my-5 prose-li:text-gray-300 prose-li:my-2 prose-li:text-[15px]
                                prose-code:text-primary-400 prose-code:bg-dark-300 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:before:content-none prose-code:after:content-none
                                prose-pre:bg-dark-300 prose-pre:border prose-pre:border-white/10 prose-pre:rounded-xl prose-pre:p-4
                                prose-a:text-primary-400 prose-a:no-underline hover:prose-a:underline font-semibold
                                prose-blockquote:border-l-4 prose-blockquote:border-primary-500 prose-blockquote:bg-primary-500/5 prose-blockquote:py-2 prose-blockquote:px-6 prose-blockquote:rounded-r-xl prose-blockquote:text-gray-300
                                prose-hr:border-white/10 prose-hr:my-8
                                bg-dark-400/40 rounded-2xl p-8 border border-white/5 shadow-2xl"
                            >
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                    {content}
                                </ReactMarkdown>
                            </div>
                        )}

                        {/* Structured Key Points and Recommendations */}
                        <div className="grid md:grid-cols-2 gap-4">
                            {structured?.key_points && Array.isArray(structured.key_points) && structured.key_points.length > 0 && (
                                <div className="card bg-dark-200/30 border-white/5">
                                    <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                                        <List className="w-4 h-4 text-accent-400" />
                                        Key Highlights
                                    </h3>
                                    <ul className="space-y-2">
                                        {structured.key_points.map((point: string, i: number) => (
                                            <li key={i} className="flex gap-3 text-sm text-gray-400">
                                                <span className="text-accent-400 font-bold">•</span>
                                                {point}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {structured?.recommendations && Array.isArray(structured.recommendations) && structured.recommendations.length > 0 && (
                                <div className="card bg-dark-200/30 border-white/5">
                                    <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                                        <BookOpen className="w-4 h-4 text-emerald-400" />
                                        Next Steps
                                    </h3>
                                    <ul className="space-y-2">
                                        {structured.recommendations.map((rec: string, i: number) => (
                                            <li key={i} className="flex gap-3 text-sm text-gray-400">
                                                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 flex-shrink-0" />
                                                {rec}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
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
