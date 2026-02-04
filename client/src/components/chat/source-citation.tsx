'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { FileText, BookOpen, Code, ExternalLink, Eye } from 'lucide-react';
import * as HoverCardPrimitive from "@radix-ui/react-hover-card";
import { AnimatePresence, motion } from "motion/react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';

interface SourceCitationProps {
    filename: string;
    location?: string;
    contentExcerpt?: string;
    fileUrl?: string;
    className?: string;
    onViewContent?: (url: string) => void;
}

/**
 * Renders a source citation as a clickable badge/pill with hover popup.
 * Click opens a detail modal. Hover shows quick preview.
 */
export function SourceCitation({
    filename,
    location,
    contentExcerpt,
    fileUrl,
    className,
    onViewContent
}: SourceCitationProps) {
    const [isHoverOpen, setIsHoverOpen] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);

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
                return 'bg-red-500/10 text-red-600 border-red-500/20 hover:bg-red-500/20 dark:text-red-400';
            case 'pptx':
            case 'ppt':
                return 'bg-orange-500/10 text-orange-600 border-orange-500/20 hover:bg-orange-500/20 dark:text-orange-400';
            case 'py':
            case 'js':
            case 'ts':
            case 'java':
            case 'cpp':
            case 'c':
                return 'bg-blue-500/10 text-blue-600 border-blue-500/20 hover:bg-blue-500/20 dark:text-blue-400';
            default:
                return 'bg-primary/10 text-primary border-primary/20 hover:bg-primary/20';
        }
    };

    const getFileTypeBadgeColor = () => {
        const ext = filename.split('.').pop()?.toLowerCase();
        switch (ext) {
            case 'pdf':
                return 'bg-red-500 text-white';
            case 'pptx':
            case 'ppt':
                return 'bg-orange-500 text-white';
            case 'py':
            case 'js':
            case 'ts':
            case 'java':
            case 'cpp':
            case 'c':
                return 'bg-blue-500 text-white';
            default:
                return 'bg-primary text-primary-foreground';
        }
    };

    const handleClick = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsModalOpen(true);
    };

    const handleViewSource = () => {
        if (fileUrl) {
            if (onViewContent) {
                // Use view-content protocol if callback provided
                const viewUrl = fileUrl.includes('/contents/')
                    ? `view-content://${fileUrl.split('/contents/')[1]}`
                    : fileUrl;
                onViewContent(viewUrl);
            } else {
                window.open(fileUrl, '_blank');
            }
        }
        setIsModalOpen(false);
    };

    const citationBadge = (
        <span
            className={cn(
                'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full',
                'text-xs font-medium border',
                'transition-all duration-200 cursor-pointer',
                'hover:shadow-md hover:scale-105',
                getFileTypeColor(),
                className
            )}
        >
            {getFileIcon()}
            <span className="max-w-[140px] truncate">{filename}</span>
            {location && (
                <>
                    <span className="opacity-40">•</span>
                    <span className="opacity-80 max-w-[100px] truncate">{location}</span>
                </>
            )}
        </span>
    );

    // Hover card popup content
    const popupContent = (
        <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.96 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            className={cn(
                'w-[28rem] max-w-[90vw] rounded-xl shadow-2xl overflow-hidden',
                'bg-popover border border-border',
                'text-popover-foreground'
            )}
        >
            {/* Header */}
            <div className="p-3 bg-gradient-to-r from-muted/80 to-muted/40 border-b border-border/50">
                <div className="flex items-center gap-2">
                    <div className={cn('p-1.5 rounded-md', getFileTypeBadgeColor())}>
                        {getFileIcon()}
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="font-semibold text-sm truncate">{filename}</p>
                        {location && (
                            <p className="text-xs text-muted-foreground">{location}</p>
                        )}
                    </div>
                </div>
            </div>

            {/* Content Preview */}
            {contentExcerpt ? (
                <div className="p-3">
                    <p className="text-xs text-muted-foreground mb-1.5 font-medium">
                        Matched Content:
                    </p>
                    <div className="text-sm text-foreground/80 bg-muted/30 rounded-lg p-3 max-h-40 overflow-y-auto border border-border/30 italic leading-relaxed">
                        "{contentExcerpt}"
                    </div>
                </div>
            ) : (
                <div className="p-3">
                    <p className="text-xs text-muted-foreground">
                        Click to view source details
                    </p>
                </div>
            )}

            {/* Footer */}
            <div className="px-3 pb-3 flex items-center gap-2">
                <Button
                    size="sm"
                    variant="secondary"
                    className="h-7 text-xs flex-1"
                    onClick={(e) => {
                        e.stopPropagation();
                        setIsModalOpen(true);
                    }}
                >
                    <Eye className="h-3 w-3 mr-1" />
                    View Details
                </Button>
                {fileUrl && (
                    <Button
                        size="sm"
                        variant="ghost"
                        className="h-7 text-xs"
                        onClick={(e) => {
                            e.stopPropagation();
                            window.open(fileUrl, '_blank');
                        }}
                    >
                        <ExternalLink className="h-3 w-3" />
                    </Button>
                )}
            </div>
        </motion.div>
    );

    return (
        <>
            {/* Hover Card */}
            <HoverCardPrimitive.Root
                openDelay={50}
                closeDelay={100}
                onOpenChange={(open) => setIsHoverOpen(open)}
            >
                <HoverCardPrimitive.Trigger asChild>
                    <button
                        type="button"
                        className="inline-flex border-0 bg-transparent p-0 m-0"
                        onClick={handleClick}
                    >
                        {citationBadge}
                    </button>
                </HoverCardPrimitive.Trigger>

                <HoverCardPrimitive.Content
                    className="[transform-origin:var(--radix-hover-card-content-transform-origin)] z-50"
                    side="top"
                    align="center"
                    sideOffset={10}
                >
                    <AnimatePresence>
                        {isHoverOpen && popupContent}
                    </AnimatePresence>
                </HoverCardPrimitive.Content>
            </HoverCardPrimitive.Root>

            {/* Detail Modal */}
            <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
                <DialogContent className="max-w-2xl">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-3">
                            <div className={cn('p-2 rounded-lg', getFileTypeBadgeColor())}>
                                {getFileIcon()}
                            </div>
                            <div>
                                <p className="text-lg">{filename}</p>
                                {location && (
                                    <p className="text-sm font-normal text-muted-foreground">
                                        {location}
                                    </p>
                                )}
                            </div>
                        </DialogTitle>
                    </DialogHeader>

                    <div className="space-y-4 mt-4">
                        {contentExcerpt && (
                            <div>
                                <h4 className="text-sm font-medium mb-2 text-muted-foreground">
                                    Referenced Content
                                </h4>
                                <ScrollArea className="max-h-72">
                                    <blockquote className="border-l-4 border-primary/30 pl-4 py-2 bg-muted/30 rounded-r-lg text-sm italic">
                                        "{contentExcerpt}"
                                    </blockquote>
                                </ScrollArea>
                            </div>
                        )}

                        <div className="flex gap-2 pt-2">
                            {fileUrl && (
                                <>
                                    <Button
                                        className="flex-1"
                                        onClick={handleViewSource}
                                    >
                                        <Eye className="h-4 w-4 mr-2" />
                                        View Full Source
                                    </Button>
                                    <Button
                                        variant="outline"
                                        onClick={() => window.open(fileUrl, '_blank')}
                                    >
                                        <ExternalLink className="h-4 w-4 mr-2" />
                                        Open File
                                    </Button>
                                </>
                            )}
                            {!fileUrl && (
                                <Button
                                    variant="secondary"
                                    className="flex-1"
                                    onClick={() => setIsModalOpen(false)}
                                >
                                    Close
                                </Button>
                            )}
                        </div>
                    </div>
                </DialogContent>
            </Dialog>
        </>
    );
}

interface SourcesSectionProps {
    sources: Array<{
        filename: string;
        location?: string;
        contentExcerpt?: string;
        fileUrl?: string;
    }>;
    className?: string;
    onViewContent?: (url: string) => void;
}

/**
 * Renders the "Sources Used" section at the end of a message.
 */
export function SourcesSection({ sources, className, onViewContent }: SourcesSectionProps) {
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
                        onViewContent={onViewContent}
                    />
                ))}
            </div>
        </div>
    );
}

/**
 * Parse content for source citations and extract them.
 */
export function extractSources(content: string): Array<{
    filename: string;
    location?: string;
    contentExcerpt?: string;
}> {
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
 */
export function transformSourceCitations(content: string): string {
    const sourcePattern = /\[Source:\s*([^,\]|]+)(?:,\s*([^|\]]+))?(?:\s*\|\s*([^\]]+))?\]/g;

    return content.replace(sourcePattern, (match, filename, location, contentExcerpt) => {
        const trimmedFilename = filename.trim();
        const trimmedLocation = location?.trim();
        const trimmedExcerpt = contentExcerpt?.trim();

        const displayText = trimmedLocation
            ? `📎 ${trimmedFilename}, ${trimmedLocation}`
            : `📎 ${trimmedFilename}`;

        const excerptAttr = trimmedExcerpt
            ? ` data-excerpt="${trimmedExcerpt.replace(/"/g, '&quot;')}"`
            : '';

        return `<span class="source-citation" data-source="${trimmedFilename}" data-location="${trimmedLocation || ''}"${excerptAttr} title="Click to see more">${displayText}</span>`;
    });
}
