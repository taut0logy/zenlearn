'use client';

import { useState, useCallback } from 'react';
import { FileText, Download, Copy, Check, Sparkles, ChevronLeft, ChevronRight, Layers, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { NoteUploader } from '@/components/notes/NoteUploader';
import { LatexRenderer } from '@/components/notes/LatexRenderer';
import { digitizeNotes } from '@/lib/notes-api';

interface DigitizedNote {
    id: string;
    title: string;
    extractedText: string;
    latexContent: string;
    blocks: Array<{
        type: string;
        content: string;
        confidence: number;
        source_image: number;
    }>;
    imageCount: number;
    merged: boolean;
}

export default function NotesPage() {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<DigitizedNote | null>(null);
    const [uploadedImages, setUploadedImages] = useState<string[]>([]);
    const [currentImageIndex, setCurrentImageIndex] = useState(0);
    const [copied, setCopied] = useState(false);

    const handleUpload = useCallback(async (images: string[]) => {
        setIsLoading(true);
        setError(null);
        setUploadedImages(images);

        try {
            const data = await digitizeNotes(images);

            if (!data.success) {
                throw new Error(data.error || 'Failed to digitize notes');
            }

            setResult({
                id: data.id,
                title: data.title,
                extractedText: data.extracted_text,
                latexContent: data.latex_content,
                blocks: data.blocks || [],
                imageCount: data.image_count,
                merged: data.merged,
            });

        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setIsLoading(false);
        }
    }, []);

    const handleCopyLatex = useCallback(() => {
        if (result?.latexContent) {
            navigator.clipboard.writeText(result.latexContent);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    }, [result]);

    const handleDownloadLatex = useCallback(() => {
        if (result?.latexContent) {
            const blob = new Blob([result.latexContent], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${result.title.replace(/\s+/g, '_')}.tex`;
            a.click();
            URL.revokeObjectURL(url);
        }
    }, [result]);

    const handleReset = useCallback(() => {
        setResult(null);
        setError(null);
        setUploadedImages([]);
        setCurrentImageIndex(0);
    }, []);

    const nextImage = useCallback(() => {
        setCurrentImageIndex(prev =>
            prev < uploadedImages.length - 1 ? prev + 1 : prev
        );
    }, [uploadedImages.length]);

    const prevImage = useCallback(() => {
        setCurrentImageIndex(prev => prev > 0 ? prev - 1 : prev);
    }, []);

    return (
        <div className="flex flex-col h-[calc(100vh-4rem)] bg-background">
            {/* Header */}
            <div className="border-b border-border px-6 py-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-gradient-to-br from-violet-500/20 to-purple-500/20">
                            <FileText className="w-5 h-5 text-violet-500" />
                        </div>
                        <div>
                            <h1 className="text-xl font-semibold">Notes Digitizer</h1>
                            <p className="text-sm text-muted-foreground">
                                Convert handwritten notes to LaTeX
                            </p>
                        </div>
                    </div>

                    {result && (
                        <Button variant="ghost" size="sm" onClick={handleReset}>
                            <ArrowLeft className="w-4 h-4 mr-2" />
                            New Notes
                        </Button>
                    )}
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-hidden p-6">
                {!result ? (
                    // Upload State
                    <div className="max-w-4xl mx-auto space-y-6 h-full flex flex-col justify-center">
                        <div className="text-center space-y-2 mb-8">
                            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm">
                                <Sparkles className="w-4 h-4" />
                                AI-Powered
                            </div>
                            <h2 className="text-2xl font-bold">
                                Upload Your Handwritten Notes
                            </h2>
                            <p className="text-muted-foreground max-w-md mx-auto">
                                Upload up to 10 images. Our AI will extract text, recognize equations,
                                and convert everything into beautifully formatted LaTeX.
                            </p>
                        </div>

                        <NoteUploader onUpload={handleUpload} isLoading={isLoading} maxImages={10} />

                        {error && (
                            <div className="p-4 rounded-lg bg-destructive/10 text-destructive text-center">
                                {error}
                            </div>
                        )}
                    </div>
                ) : (
                    // Side-by-Side Results View
                    <div className="h-full flex flex-col max-w-[1600px] mx-auto">
                        {/* Result Header */}
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
                            <div>
                                <div className="flex items-center gap-2">
                                    <h2 className="text-2xl font-bold">{result.title}</h2>
                                    {result.merged && result.imageCount > 1 && (
                                        <span className="px-2 py-0.5 rounded-full bg-green-500/10 text-green-600 text-xs font-medium flex items-center gap-1">
                                            <Layers className="w-3 h-3" />
                                            Merged
                                        </span>
                                    )}
                                </div>
                                <p className="text-sm text-muted-foreground">
                                    {result.blocks.length} content blocks extracted from {result.imageCount} image{result.imageCount > 1 ? 's' : ''}
                                </p>
                            </div>
                            <div className="flex gap-2">
                                <Button variant="outline" size="sm" onClick={handleCopyLatex}>
                                    {copied ? (
                                        <><Check className="w-4 h-4 mr-1" /> Copied!</>
                                    ) : (
                                        <><Copy className="w-4 h-4 mr-1" /> Copy LaTeX</>
                                    )}
                                </Button>
                                <Button variant="outline" size="sm" onClick={handleDownloadLatex}>
                                    <Download className="w-4 h-4 mr-1" />
                                    Download
                                </Button>
                            </div>
                        </div>

                        {/* Side-by-Side Layout */}
                        <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-0">
                            {/* Left Panel - Input Images */}
                            <div className="flex flex-col border border-border rounded-xl overflow-hidden min-h-[300px] lg:min-h-0">
                                <div className="px-4 py-2 bg-muted/50 border-b border-border flex items-center justify-between">
                                    <span className="text-sm font-medium">Input Images</span>
                                    <span className="text-xs text-muted-foreground">
                                        {currentImageIndex + 1} / {uploadedImages.length}
                                    </span>
                                </div>

                                <div className="flex-1 relative bg-muted/20 flex items-center justify-center overflow-hidden">
                                    <img
                                        src={uploadedImages[currentImageIndex]}
                                        alt={`Note ${currentImageIndex + 1}`}
                                        className="max-w-full max-h-full object-contain p-4"
                                    />

                                    {/* Navigation arrows */}
                                    {uploadedImages.length > 1 && (
                                        <>
                                            <button
                                                onClick={prevImage}
                                                disabled={currentImageIndex === 0}
                                                className="absolute left-2 p-2 rounded-full bg-background/80 hover:bg-background disabled:opacity-30 disabled:cursor-not-allowed transition-all shadow-lg"
                                            >
                                                <ChevronLeft className="w-5 h-5" />
                                            </button>
                                            <button
                                                onClick={nextImage}
                                                disabled={currentImageIndex === uploadedImages.length - 1}
                                                className="absolute right-2 p-2 rounded-full bg-background/80 hover:bg-background disabled:opacity-30 disabled:cursor-not-allowed transition-all shadow-lg"
                                            >
                                                <ChevronRight className="w-5 h-5" />
                                            </button>
                                        </>
                                    )}
                                </div>

                                {/* Thumbnail strip */}
                                {uploadedImages.length > 1 && (
                                    <div className="px-2 py-2 bg-muted/30 border-t border-border flex gap-2 overflow-x-auto">
                                        {uploadedImages.map((img, idx) => (
                                            <button
                                                key={idx}
                                                onClick={() => setCurrentImageIndex(idx)}
                                                className={`flex-shrink-0 w-12 h-12 rounded-md overflow-hidden border-2 transition-all ${idx === currentImageIndex
                                                        ? 'border-primary ring-2 ring-primary/30'
                                                        : 'border-transparent hover:border-primary/50'
                                                    }`}
                                            >
                                                <img
                                                    src={img}
                                                    alt={`Thumbnail ${idx + 1}`}
                                                    className="w-full h-full object-cover"
                                                />
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Right Panel - LaTeX Output */}
                            <div className="flex flex-col border border-border rounded-xl overflow-hidden min-h-[300px] lg:min-h-0">
                                <div className="px-4 py-2 bg-muted/50 border-b border-border">
                                    <span className="text-sm font-medium">LaTeX Output</span>
                                </div>

                                <div className="flex-1 overflow-auto p-4">
                                    <LatexRenderer content={result.latexContent} />
                                </div>
                            </div>
                        </div>

                        {/* Collapsible sections for source and text */}
                        <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-4">
                            {/* LaTeX Source */}
                            <details className="border border-border rounded-xl overflow-hidden">
                                <summary className="px-4 py-2 bg-muted/50 cursor-pointer hover:bg-muted/70 transition-colors text-sm font-medium">
                                    LaTeX Source Code
                                </summary>
                                <pre className="p-4 text-xs overflow-auto max-h-[200px] bg-muted/20">
                                    <code>{result.latexContent}</code>
                                </pre>
                            </details>

                            {/* Extracted Plain Text */}
                            <details className="border border-border rounded-xl overflow-hidden">
                                <summary className="px-4 py-2 bg-muted/50 cursor-pointer hover:bg-muted/70 transition-colors text-sm font-medium">
                                    Extracted Plain Text
                                </summary>
                                <div className="p-4 text-sm whitespace-pre-wrap max-h-[200px] overflow-auto bg-muted/20">
                                    {result.extractedText || 'No plain text extracted'}
                                </div>
                            </details>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
