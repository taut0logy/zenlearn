"use client";

import * as React from "react";
import { FileText, Code, Presentation, Loader2, MapPin } from "lucide-react";
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from "@/components/ui/command";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { useDebounce } from "@/hooks/use-debounce";
import { searchMaterials, SearchResult } from "@/lib/api/cms";
import { cn } from "@/lib/utils";

interface SearchCommandProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSelectResult?: (result: SearchResult) => void;
}

const fileTypeIcons: Record<string, React.ReactNode> = {
    pdf: <FileText className="h-5 w-5 text-red-500" />,
    pptx: <Presentation className="h-5 w-5 text-orange-500" />,
    code: <Code className="h-5 w-5 text-green-500" />,
    slides: <Presentation className="h-5 w-5 text-orange-500" />,
    PowerPoint: <Presentation className="h-5 w-5 text-orange-500" />,
    "PDF Document": <FileText className="h-5 w-5 text-red-500" />,
    Document: <FileText className="h-5 w-5 text-blue-500" />,
};

// Format relevance score as percentage, capped at 100%
function formatRelevance(score: number): string {
    const percentage = Math.min(Math.round(score * 100), 100);
    return `${percentage}%`;
}

// Get color class based on relevance score
function getRelevanceColor(score: number): string {
    if (score >= 0.8) return "text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400";
    if (score >= 0.5) return "text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30 dark:text-yellow-400";
    return "text-orange-600 bg-orange-100 dark:bg-orange-900/30 dark:text-orange-400";
}

export function SearchCommand({ open, onOpenChange, onSelectResult }: SearchCommandProps) {
    const [query, setQuery] = React.useState("");
    const [results, setResults] = React.useState<SearchResult[]>([]);
    const [isLoading, setIsLoading] = React.useState(false);

    const debouncedQuery = useDebounce(query, 300);

    React.useEffect(() => {
        if (!debouncedQuery || debouncedQuery.length < 2) {
            setResults([]);
            return;
        }

        const fetchResults = async () => {
            setIsLoading(true);
            try {
                const response = await searchMaterials(debouncedQuery, { limit: 10 });
                setResults(response.results || []);
            } catch (error) {
                console.error("[SearchCommand] Search failed:", error);
                setResults([]);
            } finally {
                setIsLoading(false);
            }
        };

        fetchResults();
    }, [debouncedQuery]);

    const handleSelect = (result: SearchResult) => {
        if (onSelectResult) {
            onSelectResult(result);
        } else {
            // Default: open file in new tab
            const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

            // The filepath from search may be an absolute path or a relative URL
            // We need to extract just the /contents/... portion
            let urlPath = result.filepath;

            // Handle Windows absolute paths (e.g., D:\...\contents\...)
            const contentsMatch = result.filepath.match(/[/\\]contents[/\\].*/i);
            if (contentsMatch) {
                urlPath = contentsMatch[0].replace(/\\/g, '/');
                // Ensure it starts with /
                if (!urlPath.startsWith('/')) {
                    urlPath = '/' + urlPath;
                }
            }

            window.open(`${backendUrl}${urlPath}`, "_blank");
        }
        onOpenChange(false);
        setQuery("");
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogHeader className="sr-only">
                <DialogTitle>Search Materials</DialogTitle>
                <DialogDescription>Search for course materials</DialogDescription>
            </DialogHeader>
            <DialogContent className="overflow-hidden p-0 max-w-2xl w-[90vw]" showCloseButton={false}>
                {/* shouldFilter={false} disables cmdk's client-side filtering since we do server-side search */}
                <Command shouldFilter={false} className="[&_[cmdk-group-heading]]:text-muted-foreground">
                    <CommandInput
                        placeholder="Search course materials with AI..."
                        value={query}
                        onValueChange={setQuery}
                        className="h-14 text-base"
                    />
                    <CommandList className="max-h-[500px]">
                        {isLoading && (
                            <div className="flex items-center justify-center py-12">
                                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                                <span className="ml-3 text-muted-foreground">Searching...</span>
                            </div>
                        )}

                        {!isLoading && debouncedQuery.length >= 2 && results.length === 0 && (
                            <CommandEmpty className="py-12">
                                <div className="text-center">
                                    <p className="text-lg font-medium">No results found</p>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        Try different keywords or upload more materials
                                    </p>
                                </div>
                            </CommandEmpty>
                        )}

                        {!isLoading && results.length > 0 && (
                            <CommandGroup heading={`Found ${results.length} matching files`}>
                                {results.map((result, index) => (
                                    <CommandItem
                                        key={`${result.filepath}-${index}`}
                                        value={result.filename}
                                        onSelect={() => handleSelect(result)}
                                        className="flex flex-col items-start gap-2 p-4 cursor-pointer border-b last:border-b-0 hover:bg-accent/50"
                                    >
                                        {/* File header */}
                                        <div className="flex items-center gap-3 w-full">
                                            <div className="flex-shrink-0 p-2 rounded-lg bg-muted">
                                                {fileTypeIcons[result.file_type] || <FileText className="h-5 w-5" />}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="font-semibold text-base truncate">{result.filename}</p>
                                                <p className="text-xs text-muted-foreground">{result.file_type}</p>
                                            </div>
                                            <span className={cn(
                                                "px-2 py-1 rounded-full text-xs font-medium flex-shrink-0",
                                                getRelevanceColor(result.relevance_score)
                                            )}>
                                                {formatRelevance(result.relevance_score)} match
                                            </span>
                                        </div>

                                        {/* Matching sections */}
                                        {result.matching_sections && result.matching_sections.length > 0 && (
                                            <div className="w-full pl-12 space-y-2">
                                                {result.matching_sections.slice(0, 2).map((section, sIdx) => (
                                                    <div
                                                        key={sIdx}
                                                        className="bg-muted/50 rounded-lg p-3 border-l-2 border-primary/50"
                                                    >
                                                        <div className="flex items-center gap-1.5 text-xs text-primary font-medium mb-1">
                                                            <MapPin className="h-3 w-3" />
                                                            {section.location}
                                                        </div>
                                                        <p className="text-sm text-muted-foreground line-clamp-2">
                                                            {section.content_preview.substring(0, 150)}...
                                                        </p>
                                                    </div>
                                                ))}
                                                {result.matching_sections.length > 2 && (
                                                    <p className="text-xs text-muted-foreground">
                                                        +{result.matching_sections.length - 2} more matching sections
                                                    </p>
                                                )}
                                            </div>
                                        )}
                                    </CommandItem>
                                ))}
                            </CommandGroup>
                        )}

                        {!isLoading && !debouncedQuery && (
                            <div className="py-12 text-center">
                                <p className="text-base font-medium text-muted-foreground">
                                    Search course materials with AI
                                </p>
                                <p className="text-sm text-muted-foreground/70 mt-1">
                                    Try searching for topics, concepts, or keywords
                                </p>
                            </div>
                        )}
                    </CommandList>
                </Command>
            </DialogContent>
        </Dialog>
    );
}
