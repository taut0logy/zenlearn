"use client";

import * as React from "react";
import { FileText, Code, Presentation, Loader2 } from "lucide-react";
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

interface SearchCommandProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSelectResult?: (result: SearchResult) => void;
}

const fileTypeIcons: Record<string, React.ReactNode> = {
    pdf: <FileText className="h-4 w-4 text-red-500" />,
    pptx: <Presentation className="h-4 w-4 text-orange-500" />,
    code: <Code className="h-4 w-4 text-green-500" />,
    slides: <Presentation className="h-4 w-4 text-orange-500" />,
    PowerPoint: <Presentation className="h-4 w-4 text-orange-500" />,
    "PDF Document": <FileText className="h-4 w-4 text-red-500" />,
};

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
                console.log("[SearchCommand] Fetching results for:", debouncedQuery);
                const response = await searchMaterials(debouncedQuery, { limit: 10 });
                console.log("[SearchCommand] API Response:", response);
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
            <DialogContent className="overflow-hidden p-0 max-w-lg" showCloseButton={false}>
                {/* shouldFilter={false} disables cmdk's client-side filtering since we do server-side search */}
                <Command shouldFilter={false} className="[&_[cmdk-group-heading]]:text-muted-foreground">
                    <CommandInput
                        placeholder="Search materials..."
                        value={query}
                        onValueChange={setQuery}
                    />
                    <CommandList className="max-h-[400px]">
                        {isLoading && (
                            <div className="flex items-center justify-center py-6">
                                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                            </div>
                        )}

                        {!isLoading && debouncedQuery.length >= 2 && results.length === 0 && (
                            <CommandEmpty>No results found.</CommandEmpty>
                        )}

                        {!isLoading && results.length > 0 && (
                            <CommandGroup heading={`${results.length} results`}>
                                {results.map((result, index) => (
                                    <CommandItem
                                        key={`${result.filepath}-${index}`}
                                        value={result.filename}
                                        onSelect={() => handleSelect(result)}
                                        className="flex flex-col items-start gap-1 py-3 cursor-pointer"
                                    >
                                        <div className="flex items-center gap-2 w-full">
                                            {fileTypeIcons[result.file_type] || <FileText className="h-4 w-4" />}
                                            <span className="font-medium">{result.filename}</span>
                                            <span className="ml-auto text-xs text-muted-foreground">
                                                {Math.round(result.relevance_score * 100)}% match
                                            </span>
                                        </div>
                                        {result.matching_sections?.[0] && (
                                            <div className="text-xs text-muted-foreground pl-6 line-clamp-2">
                                                <span className="font-medium">{result.matching_sections[0].location}:</span>{" "}
                                                {result.matching_sections[0].content_preview.substring(0, 100)}...
                                            </div>
                                        )}
                                    </CommandItem>
                                ))}
                            </CommandGroup>
                        )}

                        {!isLoading && !debouncedQuery && (
                            <div className="py-6 text-center text-sm text-muted-foreground">
                                Type to search course materials...
                            </div>
                        )}
                    </CommandList>
                </Command>
            </DialogContent>
        </Dialog>
    );
}
