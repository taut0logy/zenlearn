'use client';

import { useState, useEffect } from 'react';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MarkdownRenderer } from './markdown-renderer';
import { Loader2, Download, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ContentViewerModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    contentUrl?: string; // e.g. "view-content://filename.md" or actual URL
    title?: string;
}

export function ContentViewerModal({
    open,
    onOpenChange,
    contentUrl,
    title = 'Course Content'
}: ContentViewerModalProps) {
    const [content, setContent] = useState<string>('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [baseUrl, setBaseUrl] = useState<string>('');
    const [downloadUrl, setDownloadUrl] = useState<string>('');

    useEffect(() => {
        if (!contentUrl || !open) return;

        const loadContent = async () => {
            setIsLoading(true);
            setError(null);

            try {
                // Parse the URL
                // Format: view-content://filename.md
                // Actual fetch URL: API_BASE_URL/../../contents/generated/filename.md
                // But simplified: http://localhost:8000/contents/generated/filename.md

                let fetchUrl = '';
                let filename = '';

                if (contentUrl.startsWith('view-content://')) {
                    filename = contentUrl.replace('view-content://', '');
                    // Construct fetch URL assuming backend runs on port 8000
                    // In production, this should be dynamic based on API config
                    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
                    // Go up from /api/v1 to /contents
                    const rootBase = apiBase.replace('/api/v1', '');
                    fetchUrl = `${rootBase}/contents/generated/${filename}`;
                } else {
                    fetchUrl = contentUrl;
                    filename = fetchUrl.split('/').pop() || 'document.md';
                }

                setDownloadUrl(fetchUrl);

                // Set base URL for relative images
                // e.g. if file is at .../generated/doc.md, images at ./img.png
                // base should be .../generated/
                const lastSlash = fetchUrl.lastIndexOf('/');
                setBaseUrl(fetchUrl.substring(0, lastSlash + 1));

                const response = await fetch(fetchUrl);

                if (!response.ok) {
                    throw new Error(`Failed to load content (${response.status})`);
                }

                const text = await response.text();
                setContent(text);
            } catch (err) {
                console.error('Error loading content:', err);
                setError(err instanceof Error ? err.message : 'Unknown error');
            } finally {
                setIsLoading(false);
            }
        };

        loadContent();
    }, [contentUrl, open]);

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-4xl h-[85vh] flex flex-col p-0 gap-0">
                <DialogHeader className="px-6 py-4 border-b">
                    <div className="flex items-center justify-between">
                        <DialogTitle>{title}</DialogTitle>
                        {downloadUrl && (
                            <Button variant="ghost" size="sm" asChild>
                                <a href={downloadUrl} download target="_blank" rel="noopener noreferrer">
                                    <Download className="h-4 w-4 mr-2" />
                                    Download
                                </a>
                            </Button>
                        )}
                    </div>
                </DialogHeader>

                <div className="flex-1 overflow-hidden relative bg-white dark:bg-zinc-950">
                    {isLoading ? (
                        <div className="absolute inset-0 flex items-center justify-center">
                            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                        </div>
                    ) : error ? (
                        <div className="absolute inset-0 flex flex-col items-center justify-center text-destructive p-6 text-center">
                            <AlertCircle className="h-10 w-10 mb-2" />
                            <p className="font-semibold">Failed to load content</p>
                            <p className="text-sm text-balance mt-1 opacity-80">{error}</p>
                        </div>
                    ) : (
                        <ScrollArea className="h-full">
                            <div className="px-8 py-8 max-w-3xl mx-auto">
                                <MarkdownRenderer
                                    content={content}
                                    className="pb-10"
                                    baseImageUrl={baseUrl}
                                />
                            </div>
                        </ScrollArea>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    );
}
