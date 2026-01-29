'use client';

import { useState, useCallback } from 'react';
import { FileText, Download, Copy, Check, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { NoteUploader } from '@/components/notes/NoteUploader';
import { LatexRenderer } from '@/components/notes/LatexRenderer';
import { digitizeNote } from '@/lib/notes-api';

interface DigitizedNote {
    id: string;
    title: string;
    extractedText: string;
    latexContent: string;
    blocks: Array<{
        type: string;
        content: string;
        confidence: number;
    }>;
}

export default function NotesPage() {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<DigitizedNote | null>(null);
    const [copied, setCopied] = useState(false);
    
    const handleUpload = useCallback(async (imageBase64: string) => {
        setIsLoading(true);
        setError(null);
        
        try {
            const data = await digitizeNote(imageBase64);
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to digitize note');
            }
            
            setResult({
                id: data.id,
                title: data.title,
                extractedText: data.extracted_text,
                latexContent: data.latex_content,
                blocks: data.blocks || [],
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
    }, []);
    
    return (
        <div className="flex flex-col h-[calc(100vh-4rem)] bg-background">
            {/* Header */}
            <div className="border-b border-border px-6 py-4">
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
            </div>
            
            {/* Main Content */}
            <div className="flex-1 overflow-auto p-6">
                {!result ? (
                    <div className="max-w-2xl mx-auto space-y-6">
                        <div className="text-center space-y-2 mb-8">
                            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm">
                                <Sparkles className="w-4 h-4" />
                                AI-Powered
                            </div>
                            <h2 className="text-2xl font-bold">
                                Upload Your Handwritten Notes
                            </h2>
                            <p className="text-muted-foreground max-w-md mx-auto">
                                Our AI will extract text, recognize equations, and convert 
                                everything into beautifully formatted LaTeX.
                            </p>
                        </div>
                        
                        <NoteUploader onUpload={handleUpload} isLoading={isLoading} />
                        
                        {error && (
                            <div className="p-4 rounded-lg bg-destructive/10 text-destructive text-center">
                                {error}
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="max-w-4xl mx-auto space-y-6">
                        {/* Result Header */}
                        <div className="flex items-center justify-between">
                            <div>
                                <h2 className="text-2xl font-bold">{result.title}</h2>
                                <p className="text-sm text-muted-foreground">
                                    {result.blocks.length} content blocks extracted
                                </p>
                            </div>
                            <div className="flex gap-2">
                                <Button variant="outline" size="sm" onClick={handleReset}>
                                    New Note
                                </Button>
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
                        
                        {/* Rendered Output */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {/* LaTeX Source */}
                            <div className="border border-border rounded-xl overflow-hidden">
                                <div className="px-4 py-2 bg-muted/50 border-b border-border">
                                    <span className="text-sm font-medium">LaTeX Source</span>
                                </div>
                                <pre className="p-4 text-sm overflow-auto max-h-[500px] bg-muted/20">
                                    <code>{result.latexContent}</code>
                                </pre>
                            </div>
                            
                            {/* Rendered Preview */}
                            <div className="border border-border rounded-xl overflow-hidden">
                                <div className="px-4 py-2 bg-muted/50 border-b border-border">
                                    <span className="text-sm font-medium">Preview</span>
                                </div>
                                <div className="p-4 overflow-auto max-h-[500px]">
                                    <LatexRenderer content={result.latexContent} />
                                </div>
                            </div>
                        </div>
                        
                        {/* Extracted Text */}
                        <div className="border border-border rounded-xl overflow-hidden">
                            <div className="px-4 py-2 bg-muted/50 border-b border-border">
                                <span className="text-sm font-medium">Extracted Plain Text</span>
                            </div>
                            <div className="p-4 whitespace-pre-wrap text-sm">
                                {result.extractedText || 'No plain text extracted'}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
