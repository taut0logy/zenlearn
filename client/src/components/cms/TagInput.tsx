"use client";

import * as React from "react";
import { X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Command, CommandGroup, CommandItem, CommandList } from "@/components/ui/command";
import { Command as CommandPrimitive } from "cmdk";
import { useDebounce } from "@/hooks/use-debounce";

interface TagInputProps {
    value: string[];
    onChange: (tags: string[]) => void;
    placeholder?: string;
    suggestions?: string[];
    onSearch?: (query: string) => void;
}

export function TagInput({ value, onChange, placeholder = "Add tag...", suggestions = [], onSearch }: TagInputProps) {
    const inputRef = React.useRef<HTMLInputElement>(null);
    const [inputValue, setInputValue] = React.useState("");
    const [open, setOpen] = React.useState(false);

    // Debounce the input value
    const debouncedInputValue = useDebounce(inputValue, 300);

    // Track previous debounced value to prevent unnecessary calls
    const prevDebouncedValue = React.useRef<string>("");

    React.useEffect(() => {
        // Only call onSearch when debounced value actually changes and is different from previous
        if (onSearch && debouncedInputValue !== prevDebouncedValue.current) {
            prevDebouncedValue.current = debouncedInputValue;
            onSearch(debouncedInputValue);
        }
    }, [debouncedInputValue, onSearch]);

    // If onSearch is provided, we assume suggestions are externally filtered/loaded
    // Otherwise we filter locally.
    const filteredSuggestions = onSearch
        ? suggestions.filter(s => !value.includes(s)) // Just remove selected from the externally loaded list
        : suggestions.filter((s) => !value.includes(s) && s.toLowerCase().includes(inputValue.toLowerCase()));

    const handleUnselect = (tag: string) => {
        onChange(value.filter((s) => s !== tag));
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
        const input = inputRef.current;
        if (input) {
            if (e.key === "Delete" || e.key === "Backspace") {
                if (input.value === "" && value.length > 0) {
                    handleUnselect(value[value.length - 1]);
                }
            }

            if (e.key === "Enter") {
                if (open && filteredSuggestions.length > 0) {
                    return;
                }

                if (inputValue.trim() !== "") {
                    e.preventDefault();
                    if (!value.includes(inputValue.trim())) {
                        onChange([...value, inputValue.trim()]);
                        setInputValue("");
                    }
                }
            }

            if (e.key === "Tab" && open && filteredSuggestions.length > 0) {
                e.preventDefault();
                selectSuggestion(filteredSuggestions[0]);
            }
        }
    };

    const selectSuggestion = (tag: string) => {
        if (!value.includes(tag)) {
            onChange([...value, tag]);
            setInputValue("");
            // Keep open if onSearch is active to show more? Usually closing is better UX for tags.
            setOpen(false);
            setTimeout(() => {
                inputRef.current?.focus();
            }, 0);
        }
    }

    return (
        <Command onKeyDown={handleKeyDown} className="overflow-visible bg-transparent">
            <div
                className="group border border-input px-3 py-2 text-sm ring-offset-background rounded-md focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2"
            >
                <div className="flex flex-wrap gap-1">
                    {value.map((tag) => (
                        <Badge key={tag} variant="secondary">
                            {tag}
                            <button
                                className="ml-1 ring-offset-background rounded-full outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                                onKeyDown={(e) => {
                                    if (e.key === "Enter") {
                                        handleUnselect(tag);
                                    }
                                }}
                                onMouseDown={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                }}
                                onClick={() => handleUnselect(tag)}
                            >
                                <X className="h-3 w-3 text-muted-foreground hover:text-foreground" />
                            </button>
                        </Badge>
                    ))}
                    <CommandPrimitive.Input
                        ref={inputRef}
                        value={inputValue}
                        onValueChange={setInputValue}
                        onBlur={() => {
                            setTimeout(() => setOpen(false), 200);
                        }}
                        onFocus={() => setOpen(true)}
                        placeholder={placeholder}
                        className="ml-2 bg-transparent outline-none placeholder:text-muted-foreground flex-1 min-w-[50px]"
                    />
                </div>
            </div>
            {open && filteredSuggestions.length > 0 && (
                <div className="relative mt-2">
                    <div className="absolute top-0 z-10 w-full rounded-md border bg-popover text-popover-foreground shadow-md outline-none animate-in">
                        <CommandList>
                            <CommandGroup className="h-full overflow-auto">
                                {filteredSuggestions.map((suggestion) => (
                                    <CommandItem
                                        key={suggestion}
                                        onSelect={() => selectSuggestion(suggestion)}
                                        className="cursor-pointer"
                                        onMouseDown={(e) => {
                                            e.preventDefault();
                                            e.stopPropagation();
                                        }}
                                    >
                                        {suggestion}
                                    </CommandItem>
                                ))}
                            </CommandGroup>
                        </CommandList>
                    </div>
                </div>
            )}
        </Command>
    );
}
