'use client';

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { 
    Info, 
    AlertTriangle, 
    Lightbulb, 
    AlertCircle,
    CheckCircle,
    HelpCircle
} from 'lucide-react';

export type CalloutType = 'note' | 'warning' | 'info' | 'tip' | 'danger' | 'success' | 'question';

interface CalloutConfig {
    icon: typeof Info;
    className: string;
    title: string;
}

const calloutConfigs: Record<CalloutType, CalloutConfig> = {
    note: {
        icon: Info,
        className: 'bg-blue-500/10 border-blue-500 text-blue-700 dark:text-blue-300',
        title: 'Note',
    },
    info: {
        icon: Info,
        className: 'bg-cyan-500/10 border-cyan-500 text-cyan-700 dark:text-cyan-300',
        title: 'Info',
    },
    warning: {
        icon: AlertTriangle,
        className: 'bg-yellow-500/10 border-yellow-500 text-yellow-700 dark:text-yellow-300',
        title: 'Warning',
    },
    tip: {
        icon: Lightbulb,
        className: 'bg-green-500/10 border-green-500 text-green-700 dark:text-green-300',
        title: 'Tip',
    },
    danger: {
        icon: AlertCircle,
        className: 'bg-red-500/10 border-red-500 text-red-700 dark:text-red-300',
        title: 'Danger',
    },
    success: {
        icon: CheckCircle,
        className: 'bg-emerald-500/10 border-emerald-500 text-emerald-700 dark:text-emerald-300',
        title: 'Success',
    },
    question: {
        icon: HelpCircle,
        className: 'bg-purple-500/10 border-purple-500 text-purple-700 dark:text-purple-300',
        title: 'Question',
    },
};

interface CalloutProps {
    type: CalloutType;
    title?: string;
    children: ReactNode;
    className?: string;
}

export function Callout({ type, title, children, className }: CalloutProps) {
    const config = calloutConfigs[type] || calloutConfigs.note;
    const Icon = config.icon;
    const displayTitle = title || config.title;

    return (
        <div 
            className={cn(
                'callout my-4 p-4 rounded-lg border-l-4',
                config.className,
                className
            )}
        >
            <div className="flex items-start gap-3">
                <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                    {displayTitle && (
                        <div className="font-semibold text-sm mb-1">
                            {displayTitle}
                        </div>
                    )}
                    <div className="text-sm [&>p]:m-0">
                        {children}
                    </div>
                </div>
            </div>
        </div>
    );
}

// Blockquote component (standard markdown blockquotes)
interface BlockquoteProps {
    children: ReactNode;
    className?: string;
}

export function Blockquote({ children, className }: BlockquoteProps) {
    return (
        <blockquote 
            className={cn(
                'border-l-4 border-primary/50 pl-4 my-4 italic text-muted-foreground',
                '[&>p]:m-0',
                className
            )}
        >
            {children}
        </blockquote>
    );
}
