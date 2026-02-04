'use client';

import { useState, useCallback, useRef } from 'react';
import { Upload, X, Loader2, GripVertical, Image as ImageIcon, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface NoteUploaderProps {
    onUpload: (images: string[]) => void;
    isLoading?: boolean;
    maxImages?: number;
}

interface UploadedImage {
    id: string;
    base64: string;
    name: string;
}

export function NoteUploader({ onUpload, isLoading, maxImages = 10 }: NoteUploaderProps) {
    const [dragActive, setDragActive] = useState(false);
    const [images, setImages] = useState<UploadedImage[]>([]);
    const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
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

    const processFiles = useCallback((files: FileList | File[]) => {
        const fileArray = Array.from(files);
        const imageFiles = fileArray.filter(f => f.type.startsWith('image/'));

        if (imageFiles.length === 0) {
            alert('Please upload image files');
            return;
        }

        const remainingSlots = maxImages - images.length;
        const filesToProcess = imageFiles.slice(0, remainingSlots);

        if (fileArray.length > remainingSlots) {
            alert(`Only ${remainingSlots} more image(s) can be added. Maximum is ${maxImages}.`);
        }

        filesToProcess.forEach(file => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const base64 = e.target?.result as string;
                setImages(prev => [...prev, {
                    id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                    base64,
                    name: file.name
                }]);
            };
            reader.readAsDataURL(file);
        });
    }, [images.length, maxImages]);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            processFiles(e.dataTransfer.files);
        }
    }, [processFiles]);

    const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            processFiles(e.target.files);
        }
        // Reset input so same file can be selected again
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    }, [processFiles]);

    const handleUploadClick = useCallback(() => {
        if (images.length > 0) {
            onUpload(images.map(img => img.base64));
        }
    }, [images, onUpload]);

    const removeImage = useCallback((id: string) => {
        setImages(prev => prev.filter(img => img.id !== id));
    }, []);

    const clearAll = useCallback(() => {
        setImages([]);
    }, []);

    // Drag and drop reordering
    const handleDragStart = useCallback((e: React.DragEvent, index: number) => {
        setDraggedIndex(index);
        e.dataTransfer.effectAllowed = 'move';
    }, []);

    const handleDragOver = useCallback((e: React.DragEvent, index: number) => {
        e.preventDefault();
        if (draggedIndex === null || draggedIndex === index) return;

        setImages(prev => {
            const newImages = [...prev];
            const draggedItem = newImages[draggedIndex];
            newImages.splice(draggedIndex, 1);
            newImages.splice(index, 0, draggedItem);
            return newImages;
        });
        setDraggedIndex(index);
    }, [draggedIndex]);

    const handleDragEnd = useCallback(() => {
        setDraggedIndex(null);
    }, []);

    const canAddMore = images.length < maxImages;

    return (
        <div className="w-full max-w-4xl mx-auto">
            {images.length === 0 ? (
                // Initial Upload State
                <div
                    className={cn(
                        'border-2 border-dashed rounded-xl p-8 transition-all cursor-pointer',
                        'flex flex-col items-center justify-center gap-4',
                        'hover:shadow-lg',
                        dragActive
                            ? 'border-primary bg-primary/5 shadow-lg'
                            : 'border-muted-foreground/25 hover:border-primary/50'
                    )}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                >
                    <div className="p-4 rounded-full bg-gradient-to-br from-primary/20 to-primary/5">
                        <Upload className="w-8 h-8 text-primary" />
                    </div>
                    <div className="text-center">
                        <p className="text-lg font-medium">
                            Drop your handwritten notes here
                        </p>
                        <p className="text-sm text-muted-foreground mt-1">
                            Upload up to {maxImages} images (PNG, JPG, WebP)
                        </p>
                    </div>
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        multiple
                        className="hidden"
                        onChange={handleFileSelect}
                    />
                </div>
            ) : (
                // Gallery View with Images
                <div className="space-y-4">
                    {/* Image Gallery */}
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                        {images.map((img, index) => (
                            <div
                                key={img.id}
                                draggable
                                onDragStart={(e) => handleDragStart(e, index)}
                                onDragOver={(e) => handleDragOver(e, index)}
                                onDragEnd={handleDragEnd}
                                className={cn(
                                    'relative group rounded-lg overflow-hidden border-2 aspect-square',
                                    'bg-muted transition-all cursor-grab active:cursor-grabbing',
                                    draggedIndex === index
                                        ? 'border-primary ring-2 ring-primary/30 opacity-70'
                                        : 'border-border hover:border-primary/50'
                                )}
                            >
                                <img
                                    src={img.base64}
                                    alt={img.name}
                                    className="w-full h-full object-cover"
                                />

                                {/* Order badge */}
                                <div className="absolute top-1 left-1 bg-primary text-primary-foreground text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center shadow">
                                    {index + 1}
                                </div>

                                {/* Drag handle */}
                                <div className="absolute top-1 right-7 bg-background/80 rounded p-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <GripVertical className="w-3.5 h-3.5 text-muted-foreground" />
                                </div>

                                {/* Remove button */}
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        removeImage(img.id);
                                    }}
                                    className="absolute top-1 right-1 bg-destructive text-destructive-foreground rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity hover:scale-110"
                                >
                                    <X className="w-3.5 h-3.5" />
                                </button>

                                {/* Image name tooltip on hover */}
                                <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/70 to-transparent p-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <p className="text-white text-xs truncate">{img.name}</p>
                                </div>
                            </div>
                        ))}

                        {/* Add More Button */}
                        {canAddMore && (
                            <div
                                onClick={() => fileInputRef.current?.click()}
                                className={cn(
                                    'aspect-square rounded-lg border-2 border-dashed flex flex-col items-center justify-center',
                                    'cursor-pointer transition-all',
                                    'border-muted-foreground/25 hover:border-primary/50 hover:bg-primary/5'
                                )}
                            >
                                <Plus className="w-6 h-6 text-muted-foreground mb-1" />
                                <span className="text-xs text-muted-foreground">Add more</span>
                            </div>
                        )}
                    </div>

                    {/* Image Count */}
                    <div className="flex items-center justify-between text-sm text-muted-foreground">
                        <div className="flex items-center gap-2">
                            <ImageIcon className="w-4 h-4" />
                            <span>{images.length} of {maxImages} images</span>
                        </div>
                        <p className="text-xs">Drag to reorder • Images will be processed in order</p>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 justify-center pt-2">
                        <Button
                            variant="outline"
                            onClick={clearAll}
                            disabled={isLoading}
                        >
                            Clear All
                        </Button>
                        <Button
                            onClick={handleUploadClick}
                            disabled={isLoading || images.length === 0}
                            className="min-w-[160px] bg-gradient-to-r from-primary to-primary/80"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Digitizing...
                                </>
                            ) : (
                                <>
                                    <ImageIcon className="w-4 h-4 mr-2" />
                                    Digitize {images.length} Note{images.length > 1 ? 's' : ''}
                                </>
                            )}
                        </Button>
                    </div>
                </div>
            )}

            {/* Hidden file input for adding more */}
            <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                className="hidden"
                onChange={handleFileSelect}
            />
        </div>
    );
}
