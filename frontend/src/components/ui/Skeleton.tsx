import { clsx } from 'clsx';

interface SkeletonProps {
    className?: string;
    variant?: 'text' | 'rect' | 'circle';
    animation?: 'pulse' | 'wave' | 'none';
}

export function Skeleton({
    className,
    variant = 'rect',
    animation = 'pulse'
}: SkeletonProps) {
    return (
        <div
            className={clsx(
                'bg-white/5',
                variant === 'circle' ? 'rounded-full' : 'rounded-lg',
                animation === 'pulse' && 'animate-pulse',
                animation === 'wave' && 'relative overflow-hidden before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_2s_infinite] before:bg-gradient-to-r before:from-transparent before:via-white/5 before:to-transparent',
                className
            )}
        />
    );
}

export function AgentCardSkeleton() {
    return (
        <div className="card h-full flex flex-col">
            <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                    <Skeleton className="w-10 h-10" variant="circle" />
                    <div className="space-y-2">
                        <Skeleton className="w-24 h-5" />
                        <Skeleton className="w-16 h-3" />
                    </div>
                </div>
                <Skeleton className="w-12 h-6 rounded-full" />
            </div>
            <div className="space-y-2 mb-6 flex-1">
                <Skeleton className="w-full h-3" />
                <Skeleton className="w-[90%] h-3" />
            </div>
            <div className="flex items-center justify-between mt-auto pt-4 border-t border-white/5">
                <div className="flex gap-2">
                    <Skeleton className="w-12 h-5" />
                    <Skeleton className="w-12 h-5" />
                </div>
                <Skeleton className="w-8 h-8 rounded-lg" />
            </div>
        </div>
    );
}

export function AgentDetailSkeleton() {
    return (
        <div className="space-y-8">
            <div className="flex items-start justify-between mb-8">
                <div className="flex items-center gap-4">
                    <Skeleton className="w-10 h-10 rounded-lg" />
                    <div className="space-y-2">
                        <div className="flex items-center gap-3">
                            <Skeleton className="w-48 h-10" />
                            <Skeleton className="w-16 h-6 rounded-full" />
                        </div>
                        <Skeleton className="w-32 h-4" />
                    </div>
                </div>
                <div className="flex gap-2">
                    <Skeleton className="w-32 h-10" />
                    <Skeleton className="w-10 h-10 rounded-lg" />
                </div>
            </div>
            <div className="flex gap-4 border-b border-white/5 mb-8">
                <Skeleton className="w-24 h-10" />
                <Skeleton className="w-24 h-10" />
            </div>
            <div className="grid lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                    <Skeleton className="w-full h-64 border border-white/5 rounded-2xl" />
                    <Skeleton className="w-full h-48 border border-white/5 rounded-2xl" />
                </div>
                <div className="space-y-6">
                    <Skeleton className="w-full h-56 border border-white/5 rounded-2xl" />
                    <Skeleton className="w-full h-32 border border-white/5 rounded-2xl" />
                </div>
            </div>
        </div>
    );
}

export function WorkflowCardSkeleton() {
    return (
        <div className="card h-full flex flex-col">
            <div className="flex items-center gap-3 mb-4">
                <Skeleton className="w-8 h-8" />
                <Skeleton className="w-32 h-6" />
            </div>
            <Skeleton className="w-full h-12 mb-6" />
            <div className="space-y-3 mt-auto">
                <div className="flex items-center justify-between">
                    <Skeleton className="w-20 h-4" />
                    <div className="flex -space-x-2">
                        {[1, 2, 3].map(i => (
                            <Skeleton key={i} className="w-7 h-7 border-2 border-dark-100" variant="circle" />
                        ))}
                    </div>
                </div>
                <div className="flex justify-between pt-4 border-t border-white/5">
                    <Skeleton className="w-20 h-4" />
                    <Skeleton className="w-16 h-4" />
                </div>
            </div>
        </div>
    );
}
