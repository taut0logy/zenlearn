import React, { useRef, useState } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Pencil, Loader2, AlertCircle } from "lucide-react";

interface AvatarUploadProps {
    currentAvatarUrl?: string | null;
    userName: string;
    name?: string;
    onFileSelect?: (file: File | null, previewUrl: string | null) => void;
    maxSizeMB?: number;
    className?: string;
    disabled?: boolean;
}

export function AvatarUpload({
    currentAvatarUrl,
    userName,
    name = "avatar",
    onFileSelect,
    maxSizeMB = 2,
    className = "",
    disabled = false,
}: AvatarUploadProps) {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [previewOverride, setPreviewOverride] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const preview = previewOverride || currentAvatarUrl || null;

    const getInitials = (name: string) => {
        if (!name) return "U";
        return name
            .split(" ")
            .map((n) => n[0])
            .join("")
            .toUpperCase()
            .slice(0, 2);
    };

    const handleClick = () => {
        if (!disabled) {
            fileInputRef.current?.click();
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setError(null);

        const validTypes = [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
        ];
        if (!validTypes.includes(file.type)) {
            setError("Please select a JPG, PNG, GIF, or WebP image.");
            if (onFileSelect) onFileSelect(null, null);
            return;
        }

        const maxBytes = maxSizeMB * 1024 * 1024;
        if (file.size > maxBytes) {
            setError(`Image must be smaller than ${maxSizeMB}MB.`);
            if (onFileSelect) onFileSelect(null, null);
            return;
        }

        setIsLoading(true);

        const reader = new FileReader();
        reader.onloadend = () => {
            const previewUrl = reader.result as string;
            setPreviewOverride(previewUrl);
            setIsLoading(false);
            if (onFileSelect) {
                onFileSelect(file, previewUrl);
            }
        };
        reader.onerror = () => {
            setError("Failed to read image file.");
            setIsLoading(false);
            if (onFileSelect) onFileSelect(null, null);
        };
        reader.readAsDataURL(file);

        e.target.value = "";
    };

    return (
        <div className={`flex items-start gap-6 ${className}`}>
            <div className="flex flex-col items-center">
                <div
                    className={`relative group w-32 h-32 ${!disabled ? "cursor-pointer" : "cursor-not-allowed"}`}
                    onClick={handleClick}
                    role="button"
                    tabIndex={0}
                    onKeyPress={(e) => e.key === "Enter" && handleClick()}
                    aria-label="Upload avatar image"
                >
                    <Avatar className="h-32 w-32 border-4 border-background shadow-lg">
                        {isLoading ? (
                            <AvatarFallback className="bg-muted">
                                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                            </AvatarFallback>
                        ) : (
                            <>
                                <AvatarImage
                                    src={preview || undefined}
                                    alt={userName}
                                />
                                <AvatarFallback className="text-3xl">
                                    {getInitials(userName)}
                                </AvatarFallback>
                            </>
                        )}
                    </Avatar>

                    <div className="absolute bottom-1 right-1 bg-primary text-primary-foreground rounded-full p-2 shadow-lg border-2 border-background transition-all group-hover:scale-110">
                        <Pencil className="h-4 w-4" />
                    </div>
                </div>

                <p className="text-sm text-muted-foreground mt-2 text-center">
                    JPG, PNG, WebP, or GIF. Max {maxSizeMB}MB.
                </p>

                {error && (
                    <div className="flex items-center gap-2 text-sm text-destructive mt-2">
                        <AlertCircle className="h-4 w-4 shrink-0" />
                        <span>{error}</span>
                    </div>
                )}
            </div>

            <input
                type="file"
                ref={fileInputRef}
                name={name}
                className="hidden"
                accept="image/jpeg,image/png,image/gif,image/webp"
                onChange={handleFileChange}
                disabled={disabled}
                aria-label="Select avatar image file"
            />
        </div>
    );
}
