import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from '@/components/providers';
import { Toaster } from 'react-hot-toast';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
    title: 'AgentBuilder - UI-first AI Agent Platform',
    description: 'Build, run, and observe AI agents with ease. Create single-agent workflows, multi-agent orchestrations, and monitor execution in real-time.',
    keywords: ['AI', 'agents', 'automation', 'LLM', 'workflow', 'orchestration'],
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" className="dark">
            <body className={inter.className}>
                <Providers>
                    {children}
                    <Toaster
                        position="bottom-right"
                        toastOptions={{
                            style: {
                                background: 'rgba(15, 23, 42, 0.9)',
                                color: '#fff',
                                border: '1px solid rgba(255, 255, 255, 0.1)',
                                backdropFilter: 'blur(12px)',
                            },
                        }}
                    />
                </Providers>
            </body>
        </html>
    );
}
