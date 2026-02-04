'use client';

import ReactMarkdown, { Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import rehypeRaw from 'rehype-raw';
import { useMemo } from 'react';
import { ExternalLink as ExternalLinkIcon } from 'lucide-react';

import { CodeBlock, InlineCode } from './code-block';
import { MermaidDiagram } from './mermaid-diagram';
import { Callout, Blockquote, CalloutType } from './callout';
import { CopyButton } from './copy-button';
import { SourceCitation } from './source-citation';
import { LinkPreview } from '@/components/ui/link-preview';
import { cn } from '@/lib/utils';
import './markdown.css';

// Regex patterns for preprocessing
const CALLOUT_REGEX = /:::(note|warning|info|tip|danger|success|question)\s*\n([\s\S]*?):::/g;
// Extended citation format: [Source: filename, location | content excerpt OR url]
const SOURCE_CITATION_REGEX = /\[Source:\s*([^,\]|]+)(?:,\s*([^|\]]+))?(?:\s*\|\s*([^\]]+))?\]/g;

/**
 * Preprocess markdown to convert custom syntax to HTML
 * that can be parsed by rehype-raw
 */
function preprocessMarkdown(content: string): string {
    let processed = content;

    // Convert :::type ... ::: callouts to div elements
    processed = processed.replace(CALLOUT_REGEX, (_, type, innerContent) => {
        // Escape HTML in content but preserve markdown
        const escapedContent = innerContent.trim();
        return `<div data-callout="${type}">\n\n${escapedContent}\n\n</div>`;
    });

    // DEBUG: Log if we find any [Source: ...] patterns
    const sourceMatches = content.match(SOURCE_CITATION_REGEX);
    if (sourceMatches) {
        console.log('[MarkdownRenderer] Found Source citations:', sourceMatches);
    }

    // Transform [Source: filename, location | content excerpt OR url] to custom links
    // Use #citation-data: hash to avoid react-markdown stripping the URL
    processed = processed.replace(SOURCE_CITATION_REGEX, (match, filename, location, thirdPart) => {
        console.log('[MarkdownRenderer] Processing citation:', { match, filename, location, thirdPart });

        const trimmedFilename = filename.trim();
        const trimmedLocation = location?.trim() || '';
        const trimmedThirdPart = thirdPart?.trim() || '';

        const params = new URLSearchParams();
        params.set('filename', trimmedFilename);
        if (trimmedLocation) params.set('location', trimmedLocation);

        // Detect if third part is a URL or content excerpt
        if (trimmedThirdPart) {
            if (trimmedThirdPart.startsWith('http://') || trimmedThirdPart.startsWith('https://')) {
                params.set('fileUrl', trimmedThirdPart);
            } else {
                params.set('excerpt', trimmedThirdPart);
            }
        }

        // Use hash-based URL that react-markdown won't strip
        // Format: #citation-data:filename=...&location=...
        const citationUrl = `#citation-data:${params.toString()}`;
        console.log('[MarkdownRenderer] Generated citation URL:', citationUrl);

        // Display text in the link
        const displayText = trimmedLocation
            ? `📎 ${trimmedFilename}, ${trimmedLocation}`
            : `📎 ${trimmedFilename}`;

        return `[${displayText}](${citationUrl})`;
    });

    return processed;
}

interface MarkdownRendererProps {
    content: string;
    className?: string;
    showCopyButton?: boolean;
    isStreaming?: boolean;
    baseImageUrl?: string;
    onViewContent?: (url: string) => void;
}

export function MarkdownRenderer({
    content,
    className,
    showCopyButton = false,
    isStreaming = false,
    baseImageUrl,
    onViewContent
}: MarkdownRendererProps) {
    // Preprocess content for custom syntax
    const processedContent = useMemo(() => {
        return preprocessMarkdown(content);
    }, [content]);

    // Custom components for react-markdown
    const components: Components = useMemo(() => ({
        // Headings
        h1: ({ children }) => (
            <h1 className="text-2xl font-bold mt-6 mb-4 pb-2 border-b border-border">
                {children}
            </h1>
        ),
        h2: ({ children }) => (
            <h2 className="text-xl font-bold mt-5 mb-3 pb-1.5 border-b border-border/50">
                {children}
            </h2>
        ),
        h3: ({ children }) => (
            <h3 className="text-lg font-semibold mt-4 mb-2">{children}</h3>
        ),
        h4: ({ children }) => (
            <h4 className="text-base font-semibold mt-3 mb-2">{children}</h4>
        ),
        h5: ({ children }) => (
            <h5 className="text-sm font-semibold mt-3 mb-1">{children}</h5>
        ),
        h6: ({ children }) => (
            <h6 className="text-xs font-semibold mt-3 mb-1">{children}</h6>
        ),

        // Paragraphs
        p: ({ children }) => (
            <p className="my-2 leading-relaxed">{children}</p>
        ),

        // Code blocks and inline code
        code: ({ className: codeClassName, children, ...props }) => {
            const match = /language-(\w+)/.exec(codeClassName || '');
            const language = match ? match[1] : undefined;
            const codeString = String(children).replace(/\n$/, '');

            // Check if it's a code block (has language) or inline
            const isInline = !codeClassName && !codeString.includes('\n');

            if (isInline) {
                return <InlineCode>{children}</InlineCode>;
            }

            // Handle mermaid diagrams - show placeholder during streaming
            if (language === 'mermaid') {
                if (isStreaming) {
                    // Show code block placeholder while streaming
                    return (
                        <div className="my-4 p-4 rounded-lg bg-muted/50 border border-dashed border-muted-foreground/30">
                            <div className="flex items-center gap-2 text-muted-foreground text-sm">
                                <div className="animate-pulse">📊</div>
                                <span>Mermaid diagram (will render when complete)...</span>
                            </div>
                            <pre className="mt-2 text-xs text-muted-foreground overflow-hidden">
                                <code>{codeString.slice(0, 100)}...</code>
                            </pre>
                        </div>
                    );
                }
                return <MermaidDiagram chart={codeString} />;
            }

            // Regular code block with syntax highlighting
            return <CodeBlock language={language}>{codeString}</CodeBlock>;
        },

        // Pre tag - just pass through, code handles rendering
        pre: ({ children }) => <>{children}</>,

        // Links - use LinkPreview for external URLs and handle citations
        a: ({ href, children }) => {
            // DEBUG: Log all link hrefs to see what we're receiving
            console.log('[MarkdownRenderer] Link href:', href);

            // Handle citation links (hash-based to avoid react-markdown stripping)
            if (href?.startsWith('#citation-data:')) {
                try {
                    // Extract params from hash
                    // href format: #citation-data:filename=...&location=...&excerpt=...&fileUrl=...
                    const paramsString = href.replace('#citation-data:', '');
                    const p = new URLSearchParams(paramsString);

                    const filename = p.get('filename') || '';
                    const location = p.get('location') || undefined;
                    const excerpt = p.get('excerpt') || undefined;
                    const fileUrl = p.get('fileUrl') || undefined;

                    console.log('[MarkdownRenderer] Rendering SourceCitation:', { filename, location, excerpt, fileUrl });

                    return (
                        <SourceCitation
                            filename={filename}
                            location={location}
                            contentExcerpt={excerpt}
                            fileUrl={fileUrl}
                            onViewContent={onViewContent}
                        />
                    );
                } catch (e) {
                    // Fallback if parsing fails
                    console.error('Failed to parse citation URL', e);
                    return <span>{children}</span>;
                }
            }

            // Handle special content viewer links
            if (href?.startsWith('view-content://')) {
                return (
                    <a
                        href={href}
                        onClick={(e) => {
                            e.preventDefault();
                            onViewContent?.(href);
                        }}
                        className="text-primary font-medium hover:underline cursor-pointer inline-flex items-center gap-1.5"
                    >
                        {children}
                        <ExternalLinkIcon className="h-3 w-3" />
                    </a>
                );
            }

            const isExternal = href?.startsWith('http');

            // Use LinkPreview for external links if not streaming
            if (isExternal && !isStreaming) {
                return (
                    <LinkPreview
                        url={href || ''}
                        className="text-primary underline underline-offset-2 hover:text-primary/80 transition-colors inline-flex items-center gap-1"
                    >
                        {children}
                        <ExternalLinkIcon className="h-3 w-3" />
                    </LinkPreview>
                );
            }

            return (
                <a
                    href={href}
                    target={isExternal ? '_blank' : undefined}
                    rel={isExternal ? 'noopener noreferrer' : undefined}
                    className="text-primary underline underline-offset-2 hover:text-primary/80 transition-colors inline-flex items-center gap-1"
                >
                    {children}
                    {isExternal && <ExternalLinkIcon className="h-3 w-3" />}
                </a>
            );
        },

        // Lists
        ul: ({ children }) => (
            <ul className="list-disc ml-6 my-3 space-y-1">{children}</ul>
        ),
        ol: ({ children }) => (
            <ol className="list-decimal ml-6 my-3 space-y-1">{children}</ol>
        ),
        li: ({ children }) => (
            <li className="leading-relaxed">{children}</li>
        ),

        // Blockquotes
        blockquote: ({ children }) => (
            <Blockquote>{children}</Blockquote>
        ),

        // Tables
        table: ({ children }) => (
            <div className="overflow-x-auto my-4">
                <table className="w-full border-collapse text-sm">
                    {children}
                </table>
            </div>
        ),
        thead: ({ children }) => (
            <thead className="bg-muted">{children}</thead>
        ),
        tbody: ({ children }) => <tbody>{children}</tbody>,
        tr: ({ children }) => (
            <tr className="border-b border-border hover:bg-muted/50 transition-colors">
                {children}
            </tr>
        ),
        th: ({ children }) => (
            <th className="px-4 py-2 text-left font-semibold border border-border">
                {children}
            </th>
        ),
        td: ({ children }) => (
            <td className="px-4 py-2 border border-border">{children}</td>
        ),

        // Horizontal rule
        hr: () => <hr className="my-6 border-t border-border" />,

        // Images
        img: ({ src, alt }) => {
            // Handle relative paths if baseImageUrl is provided
            let finalSrc = src;
            if (baseImageUrl && typeof src === 'string' && !src.startsWith('http') && !src.startsWith('data:')) {
                // Ensure src doesn't start with ./
                const cleanSrc = src.startsWith('./') ? src.substring(2) : src;
                finalSrc = `${baseImageUrl}${cleanSrc}`;
            }

            return (
                <img
                    src={finalSrc}
                    alt={alt || ''}
                    className="max-w-full h-auto rounded-lg my-4 border border-border/50 shadow-sm"
                    loading="lazy"
                />
            );
        },

        // Strong and emphasis
        strong: ({ children }) => (
            <strong className="font-bold">{children}</strong>
        ),
        em: ({ children }) => (
            <em className="italic">{children}</em>
        ),
        del: ({ children }) => (
            <del className="line-through text-muted-foreground">{children}</del>
        ),

        // Handle callout divs from preprocessing
        div: ({ node, children, ...props }) => {
            const calloutType = (node?.properties?.dataCallout as CalloutType) ||
                (props as Record<string, unknown>)['data-callout'] as CalloutType;

            if (calloutType) {
                return <Callout type={calloutType}>{children}</Callout>;
            }
            return <div {...props}>{children}</div>;
        },

        // Handle source citation spans from preprocessing
        span: ({ node, children, ...props }) => {
            const nodeProps = node?.properties || {};
            const classNameProp = nodeProps.className;

            // className can be a string or array of strings
            const classNames = Array.isArray(classNameProp)
                ? classNameProp.join(' ')
                : (classNameProp as string || '');

            // Check if this is a source citation span
            if (classNames.includes('source-citation')) {
                const filename = nodeProps.dataSource as string || '';
                const location = nodeProps.dataLocation as string || undefined;
                const excerpt = nodeProps.dataExcerpt as string || undefined;

                return (
                    <SourceCitation
                        filename={filename}
                        location={location}
                        contentExcerpt={excerpt}
                        onViewContent={onViewContent}
                    />
                );
            }

            return <span {...props}>{children}</span>;
        },
    }), [isStreaming, baseImageUrl, onViewContent]);

    return (
        <div className={cn('markdown-content relative', className)}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm, remarkBreaks]}
                rehypePlugins={[rehypeRaw]}
                components={components}
            >
                {processedContent}
            </ReactMarkdown>

            {showCopyButton && (
                <div className="absolute top-0 right-0">
                    <CopyButton text={content} variant="text" />
                </div>
            )}
        </div>
    );
}
