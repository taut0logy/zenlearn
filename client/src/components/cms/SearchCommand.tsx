"use client";

import * as React from "react";
import { FileText, Code, Presentation, Loader2, MapPin, Search, Sparkles, FileQuestion, ArrowRight } from "lucide-react";
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

const fileTypeConfig: Record<string, { icon: React.ReactNode; gradient: string }> = {
    pdf: {
        icon: <FileText className="h-5 w-5" />,
        gradient: "from-red-500 to-rose-600",
    },
    pptx: {
        icon: <Presentation className="h-5 w-5" />,
        gradient: "from-orange-500 to-amber-600",
    },
    code: {
        icon: <Code className="h-5 w-5" />,
        gradient: "from-emerald-500 to-teal-600",
    },
    slides: {
        icon: <Presentation className="h-5 w-5" />,
        gradient: "from-orange-500 to-amber-600",
    },
    PowerPoint: {
        icon: <Presentation className="h-5 w-5" />,
        gradient: "from-orange-500 to-amber-600",
    },
    "PDF Document": {
        icon: <FileText className="h-5 w-5" />,
        gradient: "from-red-500 to-rose-600",
    },
    Document: {
        icon: <FileText className="h-5 w-5" />,
        gradient: "from-blue-500 to-indigo-600",
    },
};

const defaultFileConfig = {
    icon: <FileText className="h-5 w-5" />,
    gradient: "from-gray-500 to-slate-600",
};

// Format relevance score as percentage, capped at 100%
function formatRelevance(score: number): string {
    const percentage = Math.min(Math.round(score * 100), 100);
    return `${percentage}%`;
}

// Get color class based on relevance score
function getRelevanceStyle(score: number): { bg: string; text: string; border: string } {
    if (score >= 0.8) return {
        bg: "bg-emerald-500/10",
        text: "text-emerald-600 dark:text-emerald-400",
        border: "border-emerald-500/30",
    };
    if (score >= 0.5) return {
        bg: "bg-amber-500/10",
        text: "text-amber-600 dark:text-amber-400",
        border: "border-amber-500/30",
    };
    return {
        bg: "bg-orange-500/10",
        text: "text-orange-600 dark:text-orange-400",
        border: "border-orange-500/30",
    };
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
            <DialogContent
                className="overflow-hidden p-0 max-w-3xl w-[95vw] bg-background/95 backdrop-blur-xl border-border/50 shadow-2xl"
                showCloseButton={false}
            >
                {/* shouldFilter={false} disables cmdk's client-side filtering since we do server-side search */}
                <Command shouldFilter={false} className="[&_[cmdk-group-heading]]:text-muted-foreground">
                    {/* Search Input */}
                    <div className="border-b border-border/50">
                        <CommandInput
                            placeholder="Search your course materials..."
                            value={query}
                            onValueChange={setQuery}
                            className="h-14 text-base border-0 focus:ring-0 py-4"
                        />
                    </div>

                    <CommandList className="max-h-[450px] overflow-y-auto">
                        {/* Loading State */}
                        {isLoading && (
                            <div className="flex flex-col items-center justify-center py-16 px-4">
                                <div className="relative">
                                    <div className="absolute inset-0 rounded-full bg-primary/20 animate-ping" />
                                    <div className="relative p-4 rounded-full bg-gradient-to-br from-primary/20 to-emerald-500/20">
                                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                                    </div>
                                </div>
                                <p className="mt-4 text-base font-medium text-foreground">Searching with AI...</p>
                                <p className="text-sm text-muted-foreground mt-1">Finding the most relevant content</p>
                            </div>
                        )}

                        {/* No Results */}
                        {!isLoading && debouncedQuery.length >= 2 && results.length === 0 && (
                            <CommandEmpty className="py-16">
                                <div className="flex flex-col items-center text-center px-4">
                                    <div className="p-4 rounded-2xl bg-muted/50 mb-4">
                                        <FileQuestion className="h-10 w-10 text-muted-foreground" />
                                    </div>
                                    <p className="text-lg font-semibold">No results found</p>
                                    <p className="text-sm text-muted-foreground mt-1 max-w-xs">
                                        Try different keywords or check if you&apos;ve uploaded the materials you&apos;re looking for
                                    </p>
                                </div>
                            </CommandEmpty>
                        )}

                        {/* Results */}
                        {!isLoading && results.length > 0 && (
                            <CommandGroup
                                heading={
                                    <div className="flex items-center gap-2 px-2 py-3">
                                        <Sparkles className="h-4 w-4 text-primary" />
                                        <span className="text-sm font-medium">
                                            Found {results.length} matching {results.length === 1 ? 'file' : 'files'}
                                        </span>
                                    </div>
                                }
                            >
                                {results.map((result, index) => {
                                    const config = fileTypeConfig[result.file_type] || defaultFileConfig;
                                    const relevanceStyle = getRelevanceStyle(result.relevance_score);

                                    return (
                                        <CommandItem
                                            key={`${result.filepath}-${index}`}
                                            value={result.filename}
                                            onSelect={() => handleSelect(result)}
                                            className="group flex flex-col items-start gap-3 p-4 mx-2 my-1 cursor-pointer rounded-xl border border-transparent hover:border-border/50 hover:bg-accent/50 transition-all duration-200 data-[selected=true]:bg-accent/50 data-[selected=true]:border-border/50"
                                        >
                                            {/* File header */}
                                            <div className="flex items-center gap-3 w-full">
                                                {/* File icon with gradient */}
                                                <div className={cn(
                                                    "flex-shrink-0 p-2.5 rounded-xl bg-gradient-to-br text-white shadow-lg shadow-black/10",
                                                    config.gradient
                                                )}>
                                                    {config.icon}
                                                </div>

                                                {/* File info */}
                                                <div className="flex-1 min-w-0">
                                                    <p className="font-semibold text-base truncate group-hover:text-primary transition-colors">
                                                        {result.filename}
                                                    </p>
                                                    <p className="text-xs text-muted-foreground mt-0.5">
                                                        {result.file_type}
                                                    </p>
                                                </div>

                                                {/* Relevance badge */}
                                                <div className={cn(
                                                    "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border",
                                                    relevanceStyle.bg,
                                                    relevanceStyle.text,
                                                    relevanceStyle.border
                                                )}>
                                                    <span className="w-1.5 h-1.5 rounded-full bg-current" />
                                                    {formatRelevance(result.relevance_score)}
                                                </div>

                                                {/* Arrow indicator */}
                                                <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
                                            </div>

                                            {/* Matching sections */}
                                            {result.matching_sections && result.matching_sections.length > 0 && (
                                                <div className="w-full pl-14 space-y-2">
                                                    {result.matching_sections.slice(0, 2).map((section, sIdx) => (
                                                        <div
                                                            key={sIdx}
                                                            className="relative bg-muted/30 rounded-lg p-3 border-l-2 border-primary/40 hover:border-primary/70 transition-colors"
                                                        >
                                                            <div className="flex items-center gap-1.5 text-xs font-medium text-primary mb-1.5">
                                                                <MapPin className="h-3 w-3" />
                                                                <span>{section.location}</span>
                                                            </div>
                                                            <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed">
                                                                {section.content_preview.substring(0, 150)}...
                                                            </p>
                                                        </div>
                                                    ))}
                                                    {result.matching_sections.length > 2 && (
                                                        <p className="text-xs text-muted-foreground pl-1 flex items-center gap-1">
                                                            <span className="w-1 h-1 rounded-full bg-muted-foreground" />
                                                            {result.matching_sections.length - 2} more matching sections
                                                        </p>
                                                    )}
                                                </div>
                                            )}
                                        </CommandItem>
                                    );
                                })}
                            </CommandGroup>
                        )}

                        {/* Empty State - No Query */}
                        {!isLoading && !debouncedQuery && (
                            <div className="py-12 px-6">
                                <div className="flex flex-col items-center text-center">
                                    <div className="relative mb-5">
                                        <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-primary/20 to-emerald-500/20 blur-xl" />
                                        <div className="relative p-4 rounded-2xl bg-gradient-to-br from-primary/10 to-emerald-500/10 border border-primary/20">
                                            <Search className="h-8 w-8 text-primary" />
                                        </div>
                                    </div>
                                    <h3 className="text-lg font-semibold mb-1">Find your materials</h3>
                                    <p className="text-sm text-muted-foreground max-w-sm">
                                        Search for any topic, concept, or keyword in your uploaded files.
                                    </p>

                                    {/* Search suggestions */}
                                    <div className="mt-5 flex flex-wrap justify-center gap-2">
                                        {['algorithms', 'data structures', 'recursion', 'functions'].map((suggestion) => (
                                            <button
                                                key={suggestion}
                                                onClick={() => setQuery(suggestion)}
                                                className="px-3 py-1.5 text-sm rounded-full bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground border border-border/50 hover:border-border transition-all"
                                            >
                                                {suggestion}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}
                    </CommandList>

                    {/* Footer */}
                    <div className="border-t border-border/50 px-4 py-2 flex items-center justify-center text-xs text-muted-foreground bg-muted/30">
                        <div className="flex items-center gap-4">
                            <span className="flex items-center gap-1.5">
                                <kbd className="px-1.5 py-0.5 rounded bg-muted border border-border/50 font-mono">↑↓</kbd>
                                Navigate
                            </span>
                            <span className="flex items-center gap-1.5">
                                <kbd className="px-1.5 py-0.5 rounded bg-muted border border-border/50 font-mono">↵</kbd>
                                Open
                            </span>
                            <span className="flex items-center gap-1.5">
                                <kbd className="px-1.5 py-0.5 rounded bg-muted border border-border/50 font-mono">Esc</kbd>
                                Close
                            </span>
                        </div>
                    </div>
                </Command>
            </DialogContent>
        </Dialog>
    );
}
