'use client';

import { useMemo } from 'react';
import hljs from 'highlight.js';
import { CopyButton } from './copy-button';
import { cn } from '@/lib/utils';

interface CodeBlockProps {
    children: string;
    language?: string;
    showLineNumbers?: boolean;
    className?: string;
}

export function CodeBlock({ 
    children, 
    language, 
    showLineNumbers = false,
    className 
}: CodeBlockProps) {
    const code = String(children).replace(/\n$/, '');
    
    const highlightedCode = useMemo(() => {
        if (language && hljs.getLanguage(language)) {
            try {
                return hljs.highlight(code, { language }).value;
            } catch (e) {
                console.warn('Highlight.js error:', e);
            }
        }
        // Auto-detect language
        try {
            return hljs.highlightAuto(code).value;
        } catch (e) {
            return code;
        }
    }, [code, language]);

    const lines = showLineNumbers ? code.split('\n') : [];

    return (
        <div className={cn('code-block rounded-lg overflow-hidden my-4 bg-[#1e1e1e]', className)}>
            {/* Header */}
            <div className="code-header flex justify-between items-center px-4 py-2 bg-[#2d2d2d] border-b border-[#404040]">
                <span className="text-xs font-mono text-muted-foreground uppercase">
                    {language || 'text'}
                </span>
                <CopyButton text={code} />
            </div>
            
            {/* Code Content */}
            <div className="relative overflow-x-auto">
                {showLineNumbers ? (
                    <table className="w-full">
                        <tbody>
                            {lines.map((line, i) => (
                                <tr key={i} className="hover:bg-[#2a2a2a]">
                                    <td className="text-right pr-4 pl-4 py-0 text-xs text-muted-foreground select-none w-[1%] whitespace-nowrap">
                                        {i + 1}
                                    </td>
                                    <td className="pr-4 py-0">
                                        <code 
                                            className="text-sm font-mono"
                                            dangerouslySetInnerHTML={{ 
                                                __html: hljs.highlight(line, { language: language || 'plaintext' }).value || line 
                                            }} 
                                        />
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <pre className="p-4 overflow-x-auto">
                        <code 
                            className="text-sm font-mono hljs"
                            dangerouslySetInnerHTML={{ __html: highlightedCode }} 
                        />
                    </pre>
                )}
            </div>
        </div>
    );
}

// Inline code component
export function InlineCode({ children }: { children: React.ReactNode }) {
    return (
        <code className="px-1.5 py-0.5 rounded bg-muted font-mono text-sm text-primary">
            {children}
        </code>
    );
}
