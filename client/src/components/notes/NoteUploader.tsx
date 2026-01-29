'use client';

import { useState, useCallback, useRef } from 'react';
import { Upload, FileImage, X, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface NoteUploaderProps {
    onUpload: (imageBase64: string) => void;
    isLoading?: boolean;
}

export function NoteUploader({ onUpload, isLoading }: NoteUploaderProps) {
    const [dragActive, setDragActive] = useState(false);
    const [preview, setPreview] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    
    const handleDrag = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    }, []);
    
    const processFile = useCallback((file: File) => {
        if (!file.type.startsWith('image/')) {
            alert('Please upload an image file');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = (e) => {
            const base64 = e.target?.result as string;
            setPreview(base64);
        };
        reader.readAsDataURL(file);
    }, []);
    
    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            processFile(e.dataTransfer.files[0]);
        }
    }, [processFile]);
    
    const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            processFile(e.target.files[0]);
        }
    }, [processFile]);
    
    const handleUploadClick = useCallback(() => {
        if (preview) {
            onUpload(preview);
        }
    }, [preview, onUpload]);
    
    const clearPreview = useCallback(() => {
        setPreview(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    }, []);
    
    return (
        <div className="w-full max-w-2xl mx-auto">
            {!preview ? (
                <div
                    className={cn(
                        'border-2 border-dashed rounded-xl p-8 transition-colors cursor-pointer',
                        'flex flex-col items-center justify-center gap-4',
                        dragActive
                            ? 'border-primary bg-primary/5'
                            : 'border-muted-foreground/25 hover:border-primary/50'
                    )}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                >
                    <div className="p-4 rounded-full bg-primary/10">
                        <Upload className="w-8 h-8 text-primary" />
                    </div>
                    <div className="text-center">
                        <p className="text-lg font-medium">
                            Drop your handwritten notes here
                        </p>
                        <p className="text-sm text-muted-foreground mt-1">
                            or click to browse (PNG, JPG, WebP)
                        </p>
                    </div>
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={handleFileSelect}
                    />
                </div>
            ) : (
                <div className="space-y-4">
                    <div className="relative rounded-xl overflow-hidden border border-border">
                        <img
                            src={preview}
                            alt="Preview"
                            className="w-full max-h-[400px] object-contain bg-muted"
                        />
                        <button
                            onClick={clearPreview}
                            className="absolute top-2 right-2 p-1.5 rounded-full bg-background/80 hover:bg-background transition-colors"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    </div>
                    
                    <div className="flex gap-3 justify-center">
                        <Button
                            variant="outline"
                            onClick={clearPreview}
                            disabled={isLoading}
                        >
                            Choose Another
                        </Button>
                        <Button
                            onClick={handleUploadClick}
                            disabled={isLoading}
                            className="min-w-[140px]"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Digitizing...
                                </>
                            ) : (
                                <>
                                    <FileImage className="w-4 h-4 mr-2" />
                                    Digitize Note
                                </>
                            )}
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
}
