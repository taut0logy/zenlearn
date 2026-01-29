'use client';

import { useEffect, useRef, useState } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';

interface LatexRendererProps {
    content: string;
    className?: string;
}

// Box type configurations with colors and icons
const BOX_STYLES = {
    definitionbox: {
        bgColor: 'bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900',
        borderColor: 'border-l-4 border-blue-500',
        titleBg: 'bg-blue-500',
        titleText: 'text-white',
        icon: '📚',
        defaultTitle: 'Definition'
    },
    theorembox: {
        bgColor: 'bg-gradient-to-r from-green-50 to-emerald-100 dark:from-green-950 dark:to-emerald-900',
        borderColor: 'border-l-4 border-green-500',
        titleBg: 'bg-green-500',
        titleText: 'text-white',
        icon: '🎯',
        defaultTitle: 'Theorem'
    },
    examplebox: {
        bgColor: 'bg-gradient-to-r from-orange-50 to-amber-100 dark:from-orange-950 dark:to-amber-900',
        borderColor: 'border-l-4 border-orange-500',
        titleBg: 'bg-orange-500',
        titleText: 'text-white',
        icon: '💡',
        defaultTitle: 'Example'
    },
    notebox: {
        bgColor: 'bg-gradient-to-r from-gray-50 to-slate-100 dark:from-gray-800 dark:to-slate-800',
        borderColor: 'border-l-4 border-gray-400',
        titleBg: 'bg-gray-500',
        titleText: 'text-white',
        icon: '📝',
        defaultTitle: 'Note'
    },
    warningbox: {
        bgColor: 'bg-gradient-to-r from-red-50 to-rose-100 dark:from-red-950 dark:to-rose-900',
        borderColor: 'border-l-4 border-red-500',
        titleBg: 'bg-red-500',
        titleText: 'text-white',
        icon: '⚠️',
        defaultTitle: 'Warning'
    },
    proofbox: {
        bgColor: 'bg-gradient-to-r from-purple-50 to-violet-100 dark:from-purple-950 dark:to-violet-900',
        borderColor: 'border-l-4 border-purple-500',
        titleBg: 'bg-purple-500',
        titleText: 'text-white',
        icon: '✏️',
        defaultTitle: 'Proof'
    }
};

export function LatexRenderer({ content, className }: LatexRendererProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [processedContent, setProcessedContent] = useState<string>('');
    
    useEffect(() => {
        if (!content) return;
        
        // Process content and render LaTeX
        const html = processLatexContent(content);
        setProcessedContent(html);
    }, [content]);
    
    useEffect(() => {
        if (!containerRef.current || !processedContent) return;
        
        // Set HTML content
        containerRef.current.innerHTML = processedContent;
        
        // Initialize Mermaid diagrams
        initMermaidDiagrams(containerRef.current);
    }, [processedContent]);
    
    return (
        <div 
            ref={containerRef}
            className={`latex-content prose prose-slate dark:prose-invert max-w-none ${className || ''}`}
        />
    );
}

function processLatexContent(content: string): string {
    let result = content;
    
    // Process custom colored boxes FIRST (before other LaTeX processing)
    result = processColoredBoxes(result);
    
    // Process Mermaid diagrams
    result = processMermaidDiagrams(result);
    
    // Process code blocks
    result = processCodeBlocks(result);
    
    // Process tables
    result = processLatexTables(result);
    
    // Process display math: \[ ... \] or $$ ... $$
    result = result.replace(/\\\[([\\s\S]*?)\\\]|\$\$([\\s\S]*?)\$\$/g, (match, p1, p2) => {
        const latex = p1 || p2;
        try {
            return `<div class="my-4 overflow-x-auto text-center">${katex.renderToString(latex.trim(), { displayMode: true, throwOnError: false })}</div>`;
        } catch (e) {
            return `<pre class="text-red-500 bg-red-50 p-2 rounded">${latex}</pre>`;
        }
    });
    
    // Process inline math: $ ... $ or \( ... \)
    result = result.replace(/\\\(([\\s\S]*?)\\\)|\$([^$\n]+?)\$/g, (match, p1, p2) => {
        const latex = p1 || p2;
        try {
            return katex.renderToString(latex.trim(), { displayMode: false, throwOnError: false });
        } catch (e) {
            return `<code class="text-red-500">${latex}</code>`;
        }
    });
    
    // Process LaTeX structural commands
    result = processStructuralLatex(result);
    
    return result;
}

function processColoredBoxes(content: string): string {
    let result = content;
    
    // Process each box type
    for (const [boxType, styles] of Object.entries(BOX_STYLES)) {
        // Match \begin{boxtype}[optional title] ... \end{boxtype}
        const regex = new RegExp(
            `\\\\begin\\{${boxType}\\}(?:\\[([^\\]]+)\\])?([\\s\\S]*?)\\\\end\\{${boxType}\\}`,
            'g'
        );
        
        result = result.replace(regex, (match, titleOpt, boxContent) => {
            // Extract custom title if provided (format: title=Custom Title)
            let title = styles.defaultTitle;
            if (titleOpt) {
                const titleMatch = titleOpt.match(/title=(.+)/);
                if (titleMatch) {
                    title = titleMatch[1].trim();
                } else {
                    title = titleOpt.trim();
                }
            }
            
            return `
<div class="${styles.bgColor} ${styles.borderColor} rounded-lg shadow-md my-4 overflow-hidden">
    <div class="${styles.titleBg} ${styles.titleText} px-4 py-2 font-bold flex items-center gap-2">
        <span>${styles.icon}</span>
        <span>${escapeHtml(title)}</span>
    </div>
    <div class="p-4">
        ${processInnerContent(boxContent.trim())}
    </div>
</div>`;
        });
    }
    
    return result;
}

function processMermaidDiagrams(content: string): string {
    // Match \begin{mermaid}[optional type] ... \end{mermaid}
    return content.replace(
        /\\begin\{mermaid\}(?:\[([^\]]+)\])?([\s\S]*?)\\end\{mermaid\}/g,
        (match, diagramType, diagramContent) => {
            const type = diagramType || 'flowchart';
            const cleanContent = diagramContent.trim()
                .replace(/\\n/g, '\n')  // Convert literal \n to newlines
                .replace(/\\\\/g, '');  // Remove LaTeX line breaks
            
            return `
<div class="mermaid-container my-4 p-4 bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700">
    <div class="text-xs text-gray-500 mb-2 flex items-center gap-1">
        <span>📊</span>
        <span>Diagram (${type})</span>
    </div>
    <div class="mermaid-diagram" data-diagram="${encodeURIComponent(cleanContent)}">
        <pre class="text-sm bg-gray-50 dark:bg-gray-900 p-3 rounded">${escapeHtml(cleanContent)}</pre>
    </div>
</div>`;
        }
    );
}

function processCodeBlocks(content: string): string {
    // Match \begin{codebox}[language] ... \end{codebox}
    return content.replace(
        /\\begin\{codebox\}(?:\[([^\]]+)\])?([\s\S]*?)\\end\{codebox\}/g,
        (match, language, codeContent) => {
            const lang = language || 'text';
            const cleanCode = codeContent.trim();
            
            return `
<div class="code-block my-4 rounded-lg overflow-hidden shadow-md">
    <div class="bg-gray-800 text-gray-200 px-4 py-2 text-sm flex items-center justify-between">
        <span class="flex items-center gap-2">
            <span>💻</span>
            <span>${escapeHtml(lang)}</span>
        </span>
        <button onclick="navigator.clipboard.writeText(this.closest('.code-block').querySelector('code').textContent)" class="text-xs bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded transition-colors">
            Copy
        </button>
    </div>
    <pre class="bg-gray-900 p-4 overflow-x-auto"><code class="language-${lang} text-sm text-gray-100">${escapeHtml(cleanCode)}</code></pre>
</div>`;
        }
    );
}

function processLatexTables(content: string): string {
    // Match LaTeX table environment
    return content.replace(
        /\\begin\{table\}[\s\S]*?\\begin\{tabular\}\{([^}]+)\}([\s\S]*?)\\end\{tabular\}[\s\S]*?(?:\\caption\{([^}]+)\})?[\s\S]*?\\end\{table\}/g,
        (match, alignment, tableContent, caption) => {
            // Parse table content
            const lines = tableContent.split('\\\\').filter((line: string) => 
                line.trim() && 
                !line.includes('\\toprule') && 
                !line.includes('\\midrule') && 
                !line.includes('\\bottomrule')
            );
            
            if (lines.length === 0) return match;
            
            // First line is headers
            const headers = lines[0].split('&').map((h: string) => 
                h.replace(/\\textbf\{([^}]+)\}/g, '$1').trim()
            );
            
            // Rest are data rows
            const rows = lines.slice(1).map((line: string) => 
                line.split('&').map((cell: string) => cell.trim())
            );
            
            let tableHtml = `
<div class="my-4 overflow-x-auto">
    <table class="min-w-full border-collapse bg-white dark:bg-gray-800 shadow-md rounded-lg overflow-hidden">
        <thead class="bg-gradient-to-r from-indigo-500 to-purple-500 text-white">
            <tr>
                ${headers.map((h: string) => `<th class="px-4 py-3 text-left font-semibold">${escapeHtml(h)}</th>`).join('')}
            </tr>
        </thead>
        <tbody>
            ${rows.map((row: string[], i: number) => `
                <tr class="${i % 2 === 0 ? 'bg-gray-50 dark:bg-gray-700' : 'bg-white dark:bg-gray-800'}">
                    ${row.map((cell: string) => `<td class="px-4 py-3 border-t border-gray-200 dark:border-gray-600">${escapeHtml(cell)}</td>`).join('')}
                </tr>
            `).join('')}
        </tbody>
    </table>
    ${caption ? `<p class="text-center text-sm text-gray-500 mt-2">${escapeHtml(caption)}</p>` : ''}
</div>`;
            
            return tableHtml;
        }
    );
}

function processInnerContent(content: string): string {
    // Process math within boxes
    let result = content;
    
    // Display math
    result = result.replace(/\\\[([\\s\S]*?)\\\]|\$\$([\\s\S]*?)\$\$/g, (match, p1, p2) => {
        const latex = p1 || p2;
        try {
            return `<div class="my-2 overflow-x-auto">${katex.renderToString(latex.trim(), { displayMode: true, throwOnError: false })}</div>`;
        } catch (e) {
            return `<pre class="text-red-500">${latex}</pre>`;
        }
    });
    
    // Inline math
    result = result.replace(/\\\(([\\s\S]*?)\\\)|\$([^$\n]+?)\$/g, (match, p1, p2) => {
        const latex = p1 || p2;
        try {
            return katex.renderToString(latex.trim(), { displayMode: false, throwOnError: false });
        } catch (e) {
            return `<code class="text-red-500">${latex}</code>`;
        }
    });
    
    // Basic formatting
    result = result.replace(/\\textbf\{([^}]+)\}/g, '<strong>$1</strong>');
    result = result.replace(/\\textit\{([^}]+)\}/g, '<em>$1</em>');
    result = result.replace(/\\underline\{([^}]+)\}/g, '<u>$1</u>');
    
    // Line breaks
    result = result.replace(/\\\\/g, '<br/>');
    result = result.replace(/\n\n/g, '<br/><br/>');
    
    return result;
}

function processStructuralLatex(content: string): string {
    let result = content;
    
    // Sections with styled headers
    result = result.replace(
        /\\section\{([^}]+)\}/g, 
        '<h2 class="text-2xl font-bold mt-8 mb-4 pb-2 border-b-2 border-indigo-500 text-gray-800 dark:text-gray-100">$1</h2>'
    );
    result = result.replace(
        /\\subsection\{([^}]+)\}/g, 
        '<h3 class="text-xl font-semibold mt-6 mb-3 text-gray-700 dark:text-gray-200">$1</h3>'
    );
    result = result.replace(
        /\\subsubsection\{([^}]+)\}/g, 
        '<h4 class="text-lg font-medium mt-4 mb-2 text-gray-600 dark:text-gray-300">$1</h4>'
    );
    
    // Text formatting
    result = result.replace(/\\textbf\{([^}]+)\}/g, '<strong>$1</strong>');
    result = result.replace(/\\textit\{([^}]+)\}/g, '<em>$1</em>');
    result = result.replace(/\\underline\{([^}]+)\}/g, '<u>$1</u>');
    result = result.replace(/\\emph\{([^}]+)\}/g, '<em>$1</em>');
    
    // Lists with styled bullets
    result = result.replace(/\\begin\{itemize\}([\s\S]*?)\\end\{itemize\}/g, (match, items) => {
        const listItems = items
            .split('\\item')
            .filter((item: string) => item.trim())
            .map((item: string) => `<li class="ml-2">${item.trim()}</li>`)
            .join('');
        return `<ul class="list-disc pl-6 my-3 space-y-1">${listItems}</ul>`;
    });
    
    result = result.replace(/\\begin\{enumerate\}([\s\S]*?)\\end\{enumerate\}/g, (match, items) => {
        const listItems = items
            .split('\\item')
            .filter((item: string) => item.trim())
            .map((item: string) => `<li class="ml-2">${item.trim()}</li>`)
            .join('');
        return `<ol class="list-decimal pl-6 my-3 space-y-1">${listItems}</ol>`;
    });
    
    // Clean up escape sequences
    result = result.replace(/\\&/g, '&');
    result = result.replace(/\\_/g, '_');
    result = result.replace(/\\%/g, '%');
    result = result.replace(/\\#/g, '#');
    result = result.replace(/\\\$/g, '$');
    
    // Convert newlines
    result = result.replace(/\n\n+/g, '<br/><br/>');
    
    return result;
}

function escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function initMermaidDiagrams(container: HTMLElement) {
    // Check if Mermaid is available
    const mermaidContainers = container.querySelectorAll('.mermaid-diagram');
    if (mermaidContainers.length === 0) return;
    
    try {
        // Dynamically import mermaid
        const mermaid = (await import('mermaid')).default;
        
        mermaid.initialize({
            startOnLoad: false,
            theme: 'default',
            securityLevel: 'loose',
            flowchart: {
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }
        });
        
        mermaidContainers.forEach(async (elem, index) => {
            const diagramData = elem.getAttribute('data-diagram');
            if (!diagramData) return;
            
            try {
                const decoded = decodeURIComponent(diagramData);
                const { svg } = await mermaid.render(`mermaid-${index}`, decoded);
                elem.innerHTML = svg;
            } catch (e) {
                console.error('Mermaid rendering error:', e);
                // Keep the pre element as fallback
            }
        });
    } catch (e) {
        console.warn('Mermaid not available, diagrams will show as text');
    }
}
