'use client';

import { useEffect, useRef, useState, useId } from 'react';
import mermaid from 'mermaid';
import { cn } from '@/lib/utils';
import { CopyButton } from './copy-button';
import { AlertCircle, RefreshCw } from 'lucide-react';

// Initialize mermaid with dark theme
let mermaidInitialized = false;

function initializeMermaid() {
    if (mermaidInitialized) return;
    
    mermaid.initialize({
        startOnLoad: false,
        theme: 'dark',
        securityLevel: 'loose',
        fontFamily: 'inherit',
        flowchart: {
            useMaxWidth: true,
            htmlLabels: true,
        },
        sequence: {
            useMaxWidth: true,
        },
    });
    mermaidInitialized = true;
}

interface MermaidDiagramProps {
    chart: string;
    className?: string;
}

/**
 * Sanitize mermaid chart to fix common syntax issues from LLM output.
 * Mermaid has strict requirements for special characters in node labels.
 */
function sanitizeMermaidChart(chart: string): string {
    const lines = chart.split('\n');
    const sanitizedLines = lines.map(line => {
        let sanitized = line;
        
        // Fix node labels inside square brackets [text]
        sanitized = sanitized.replace(/\[([^\]]+)\]/g, (match, content) => {
            let fixed = content;
            // Remove or replace parentheses - common issue
            fixed = fixed.replace(/\(([^)]*)\)/g, ' $1 ');
            // Remove angle brackets
            fixed = fixed.replace(/[<>]/g, '');
            // Replace equals with "is"
            fixed = fixed.replace(/\s*=\s*/g, ' equals ');
            // Clean up multiple spaces
            fixed = fixed.replace(/\s+/g, ' ').trim();
            return `[${fixed}]`;
        });
        
        // Fix node labels inside curly braces {text} (decision nodes)
        sanitized = sanitized.replace(/\{([^}]+)\}/g, (match, content) => {
            let fixed = content;
            // Remove parentheses
            fixed = fixed.replace(/\(([^)]*)\)/g, ' $1 ');
            // Remove angle brackets
            fixed = fixed.replace(/[<>]/g, '');
            // Clean up spaces
            fixed = fixed.replace(/\s+/g, ' ').trim();
            return `{${fixed}}`;
        });
        
        // Fix edge labels |text|
        sanitized = sanitized.replace(/\|([^|]+)\|/g, (match, content) => {
            let fixed = content;
            // Remove special chars from edge labels
            fixed = fixed.replace(/[<>{}[\]()]/g, '');
            fixed = fixed.replace(/\s+/g, ' ').trim();
            return `|${fixed}|`;
        });
        
        return sanitized;
    });
    return sanitizedLines.join('\n');
}

export function MermaidDiagram({ chart, className }: MermaidDiagramProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [svg, setSvg] = useState<string>('');
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const uniqueId = useId().replace(/:/g, '-');

    const renderDiagram = async () => {
        if (!chart.trim()) {
            setError('Empty diagram');
            setIsLoading(false);
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            initializeMermaid();
            
            // Sanitize the chart to fix common LLM syntax issues
            const sanitizedChart = sanitizeMermaidChart(chart.trim());
            
            // First validate the syntax without rendering
            // This prevents mermaid from adding error elements to the DOM
            try {
                await mermaid.parse(sanitizedChart);
            } catch (parseErr) {
                // Syntax error - show fallback without DOM pollution
                setError('Invalid diagram syntax');
                setIsLoading(false);
                return;
            }
            
            const id = `mermaid-${uniqueId}-${Date.now()}`;
            const { svg: renderedSvg } = await mermaid.render(id, sanitizedChart);
            setSvg(renderedSvg);
            
            // Clean up any orphaned mermaid error elements that might have been created
            document.querySelectorAll('#d' + id).forEach(el => el.remove());
        } catch (err) {
            // Clean up any orphaned mermaid elements
            document.querySelectorAll('[id^="mermaid-"]').forEach(el => {
                if (el.closest('.mermaid-container') === null && 
                    el.tagName !== 'DIV' || 
                    el.classList.contains('error-icon')) {
                    el.remove();
                }
            });
            console.error('Mermaid render error:', err);
            setError('Failed to render diagram');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        renderDiagram();
        
        // Cleanup function to remove any orphaned mermaid elements
        return () => {
            // Remove orphaned error elements that mermaid creates outside our container
            document.querySelectorAll('[id^="dmermaid-"]').forEach(el => el.remove());
            document.querySelectorAll('.error-icon').forEach(el => {
                if (!el.closest('.mermaid-container')) {
                    el.remove();
                }
            });
        };
    }, [chart]);

    if (isLoading) {
        return (
            <div className={cn(
                'mermaid-container my-4 p-8 rounded-lg bg-muted/50 border',
                'flex items-center justify-center',
                className
            )}>
                <RefreshCw className="h-5 w-5 animate-spin text-muted-foreground" />
                <span className="ml-2 text-sm text-muted-foreground">Rendering diagram...</span>
            </div>
        );
    }

    if (error) {
        // Fallback: Show the mermaid code as a regular code block
        return (
            <div className={cn(
                'mermaid-container my-4 rounded-lg bg-[#1e1e1e] overflow-hidden',
                className
            )}>
                {/* Header */}
                <div className="flex justify-between items-center px-4 py-2 bg-[#2d2d2d] border-b border-[#404040]">
                    <span className="text-xs font-mono text-muted-foreground uppercase">
                        mermaid (source)
                    </span>
                    <CopyButton text={chart} />
                </div>
                
                {/* Code as fallback */}
                <pre className="p-4 overflow-x-auto">
                    <code className="text-sm font-mono text-[#d4d4d4] whitespace-pre">
                        {chart}
                    </code>
                </pre>
            </div>
        );
    }

    return (
        <div className={cn(
            'mermaid-container my-4 rounded-lg bg-muted/30 border overflow-hidden',
            className
        )}>
            {/* Header */}
            <div className="flex justify-between items-center px-4 py-2 bg-muted/50 border-b">
                <span className="text-xs font-mono text-muted-foreground uppercase">
                    Mermaid Diagram
                </span>
                <CopyButton text={chart} />
            </div>
            
            {/* Diagram */}
            <div 
                ref={containerRef}
                className="p-4 overflow-x-auto flex justify-center"
                dangerouslySetInnerHTML={{ __html: svg }}
            />
        </div>
    );
}
