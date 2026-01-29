'use client';

import { useState, useCallback } from 'react';
import { Check, Copy } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CopyButtonProps {
    text: string;
    className?: string;
    variant?: 'icon' | 'text';
}

export function CopyButton({ text, className, variant = 'icon' }: CopyButtonProps) {
    const [copied, setCopied] = useState(false);

    const handleCopy = useCallback(async () => {
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    }, [text]);

    if (variant === 'text') {
        return (
            <button
                onClick={handleCopy}
                className={cn(
                    'flex items-center gap-1.5 px-2 py-1 text-xs rounded',
                    'text-muted-foreground hover:text-foreground',
                    'hover:bg-muted transition-colors',
                    className
                )}
            >
                {copied ? (
                    <>
                        <Check className="h-3.5 w-3.5" />
                        Copied!
                    </>
                ) : (
                    <>
                        <Copy className="h-3.5 w-3.5" />
                        Copy
                    </>
                )}
            </button>
        );
    }

    return (
        <button
            onClick={handleCopy}
            className={cn(
                'p-1.5 rounded-md',
                'text-muted-foreground hover:text-foreground',
                'hover:bg-muted/80 transition-colors',
                className
            )}
            title={copied ? 'Copied!' : 'Copy to clipboard'}
        >
            {copied ? (
                <Check className="h-4 w-4 text-green-500" />
            ) : (
                <Copy className="h-4 w-4" />
            )}
        </button>
    );
}
