'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { FileText, BookOpen, Code, ExternalLink } from 'lucide-react';
import * as HoverCardPrimitive from "@radix-ui/react-hover-card";
import { AnimatePresence, motion } from "motion/react";

interface SourceCitationProps {
    filename: string;
    location?: string;
    contentExcerpt?: string;
    fileUrl?: string;
    className?: string;
}

/**
 * Renders a source citation as a clickable badge/pill with hover popup.
 * Format expected: [Source: filename, location] or [Source: filename, location | content excerpt]
 */
export function SourceCitation({
    filename,
    location,
    contentExcerpt,
    fileUrl,
    className
}: SourceCitationProps) {
    const [isOpen, setIsOpen] = React.useState(false);

    // Determine file type icon based on extension
    const getFileIcon = () => {
        const ext = filename.split('.').pop()?.toLowerCase();
        switch (ext) {
            case 'pdf':
                return <FileText className="h-3 w-3" />;
            case 'pptx':
            case 'ppt':
                return <BookOpen className="h-3 w-3" />;
            case 'py':
            case 'js':
            case 'ts':
            case 'java':
            case 'cpp':
            case 'c':
                return <Code className="h-3 w-3" />;
            default:
                return <FileText className="h-3 w-3" />;
        }
    };

    const getFileTypeColor = () => {
        const ext = filename.split('.').pop()?.toLowerCase();
        switch (ext) {
            case 'pdf':
                return 'bg-red-500/10 text-red-600 border-red-500/20 hover:bg-red-500/20';
            case 'pptx':
            case 'ppt':
                return 'bg-orange-500/10 text-orange-600 border-orange-500/20 hover:bg-orange-500/20';
            case 'py':
            case 'js':
            case 'ts':
            case 'java':
            case 'cpp':
            case 'c':
                return 'bg-blue-500/10 text-blue-600 border-blue-500/20 hover:bg-blue-500/20';
            default:
                return 'bg-primary/10 text-primary border-primary/20 hover:bg-primary/20';
        }
    };

    const citationBadge = (
        <span
            className={cn(
                'inline-flex items-center gap-1 px-2 py-0.5 rounded-full',
                'text-xs font-medium border',
                'transition-colors cursor-pointer',
                getFileTypeColor(),
                className
            )}
        >
            {getFileIcon()}
            <span className="max-w-[120px] truncate">{filename}</span>
            {location && (
                <>
                    <span className="opacity-50">•</span>
                    <span className="opacity-70 max-w-[80px] truncate">{location}</span>
                </>
            )}
        </span>
    );

    // If there's content to show in popup, wrap in hover card
    if (contentExcerpt) {
        return (
            <HoverCardPrimitive.Root
                openDelay={100}
                closeDelay={50}
                onOpenChange={setIsOpen}
            >
                <HoverCardPrimitive.Trigger asChild>
                    {fileUrl ? (
                        <a href={fileUrl} target="_blank" rel="noopener noreferrer">
                            {citationBadge}
                        </a>
                    ) : (
                        citationBadge
                    )}
                </HoverCardPrimitive.Trigger>

                <HoverCardPrimitive.Portal>
                    <HoverCardPrimitive.Content
                        className="z-50"
                        side="top"
                        align="center"
                        sideOffset={8}
                    >
                        <AnimatePresence>
                            {isOpen && (
                                <motion.div
                                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                    transition={{ duration: 0.15 }}
                                    className={cn(
                                        'w-80 max-w-[90vw] p-3 rounded-lg shadow-xl',
                                        'bg-popover border border-border',
                                        'text-popover-foreground'
                                    )}
                                >
                                    <div className="flex items-center gap-2 mb-2">
                                        {getFileIcon()}
                                        <span className="font-medium text-sm truncate">{filename}</span>
                                        {location && (
                                            <span className="text-xs text-muted-foreground">• {location}</span>
                                        )}
                                    </div>
                                    <div className="text-xs text-muted-foreground bg-muted/50 rounded p-2 max-h-32 overflow-y-auto">
                                        "{contentExcerpt}"
                                    </div>
                                    {fileUrl && (
                                        <a
                                            href={fileUrl}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="mt-2 flex items-center gap-1 text-xs text-primary hover:underline"
                                        >
                                            <ExternalLink className="h-3 w-3" />
                                            Open file
                                        </a>
                                    )}
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </HoverCardPrimitive.Content>
                </HoverCardPrimitive.Portal>
            </HoverCardPrimitive.Root>
        );
    }

    // Simple badge without popup
    if (fileUrl) {
        return (
            <a href={fileUrl} target="_blank" rel="noopener noreferrer">
                {citationBadge}
            </a>
        );
    }

    return citationBadge;
}

interface SourcesSectionProps {
    sources: Array<{
        filename: string;
        location?: string;
        contentExcerpt?: string;
        fileUrl?: string;
    }>;
    className?: string;
}

/**
 * Renders the "Sources Used" section at the end of a message.
 */
export function SourcesSection({ sources, className }: SourcesSectionProps) {
    if (!sources.length) return null;

    return (
        <div
            className={cn(
                'mt-4 p-3 rounded-lg',
                'bg-gradient-to-r from-muted/50 to-muted/30',
                'border border-muted-foreground/10',
                className
            )}
        >
            <div className="flex items-center gap-2 mb-3 text-sm font-medium text-muted-foreground">
                <BookOpen className="h-4 w-4" />
                <span>📚 Sources Used</span>
            </div>
            <div className="flex flex-wrap gap-2">
                {sources.map((source, index) => (
                    <SourceCitation
                        key={`${source.filename}-${index}`}
                        filename={source.filename}
                        location={source.location}
                        contentExcerpt={source.contentExcerpt}
                        fileUrl={source.fileUrl}
                    />
                ))}
            </div>
        </div>
    );
}

/**
 * Parse content for source citations and extract them.
 * Supports both simple and extended formats:
 * - [Source: filename, location]
 * - [Source: filename, location | content excerpt]
 */
export function extractSources(content: string): Array<{
    filename: string;
    location?: string;
    contentExcerpt?: string;
}> {
    // Extended pattern with optional content excerpt
    const sourcePattern = /\[Source:\s*([^,\]|]+)(?:,\s*([^|\]]+))?(?:\s*\|\s*([^\]]+))?\]/g;
    const sources: Array<{ filename: string; location?: string; contentExcerpt?: string }> = [];
    const seen = new Set<string>();

    let match;
    while ((match = sourcePattern.exec(content)) !== null) {
        const filename = match[1].trim();
        const location = match[2]?.trim();
        const contentExcerpt = match[3]?.trim();
        const key = `${filename}|${location || ''}`;

        if (!seen.has(key)) {
            seen.add(key);
            sources.push({ filename, location, contentExcerpt });
        }
    }

    return sources;
}

/**
 * Transform inline [Source: ...] citations to styled spans.
 * Supports extended format with content excerpts.
 */
export function transformSourceCitations(content: string): string {
    // Extended pattern with optional content excerpt
    const sourcePattern = /\[Source:\s*([^,\]|]+)(?:,\s*([^|\]]+))?(?:\s*\|\s*([^\]]+))?\]/g;

    return content.replace(sourcePattern, (match, filename, location, contentExcerpt) => {
        const trimmedFilename = filename.trim();
        const trimmedLocation = location?.trim();
        const trimmedExcerpt = contentExcerpt?.trim();

        const displayText = trimmedLocation
            ? `📎 ${trimmedFilename}, ${trimmedLocation}`
            : `📎 ${trimmedFilename}`;

        // Include data attributes for the excerpt
        const excerptAttr = trimmedExcerpt
            ? ` data-excerpt="${trimmedExcerpt.replace(/"/g, '&quot;')}"`
            : '';

        return `<span class="source-citation" data-source="${trimmedFilename}" data-location="${trimmedLocation || ''}"${excerptAttr} title="Click to see more">${displayText}</span>`;
    });
}
