"use client";

import * as React from "react";
import { Folder, FileText, FileCode, MoreVertical, Download, Edit2, Trash2, ArrowUpDown, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
    ContextMenu,
    ContextMenuContent,
    ContextMenuItem,
    ContextMenuSeparator,
    ContextMenuTrigger,
} from "@/components/ui/context-menu";

export interface FileItem {
    id: string;
    name: string;
    type: "folder" | "file";
    fileType?: "pdf" | "pptx" | "code";
    url?: string;
    updatedAt?: string;
    description?: string;
    size?: string; // Mock size if needed
}

type SortField = "name" | "updatedAt" | "type";
type SortOrder = "asc" | "desc";

interface DriveExplorerProps {
    items: FileItem[];
    loading?: boolean;
    onNavigate: (item: FileItem) => void;
    onDownload?: (item: FileItem) => void;
    onDelete?: (items: FileItem[]) => void;
    onRename?: (item: FileItem) => void;
    currentPath: { name: string; id?: string }[];
    onBreadcrumbClick: (index: number) => void;
}

export function DriveExplorer({
    items,
    loading,
    onNavigate,
    onDownload,
    onDelete,
    onRename,
    currentPath,
    onBreadcrumbClick
}: DriveExplorerProps) {
    const [viewMode, setViewMode] = React.useState<"grid" | "list">("list");
    const [selectedIds, setSelectedIds] = React.useState<Set<string>>(new Set());
    const [sortField, setSortField] = React.useState<SortField>("name");
    const [sortOrder, setSortOrder] = React.useState<SortOrder>("asc");
    const [currentPage, setCurrentPage] = React.useState(1);
    const itemsPerPage = 20; // Or passed as prop

    // Keyboard Shortcuts
    React.useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === "Escape") {
                setSelectedIds(new Set());
            } else if ((e.ctrlKey || e.metaKey) && e.key === "a") {
                e.preventDefault();
                setSelectedIds(new Set(items.map(i => i.id)));
            } else if (e.key === "Delete" || e.key === "Backspace") {
                if (selectedIds.size > 0 && onDelete) {
                    const selectedItems = items.filter(i => selectedIds.has(i.id));
                    onDelete(selectedItems);
                }
            }
        };
        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [items, selectedIds, onDelete]);

    // Reset selection/page on path change
    React.useEffect(() => {
        setSelectedIds(new Set());
        setCurrentPage(1);
    }, [currentPath]);

    // Sorting
    const sortedItems = React.useMemo(() => {
        return [...items].sort((a, b) => {
            let aVal: any = a[sortField] || "";
            let bVal: any = b[sortField] || "";

            if (sortField === "updatedAt") {
                aVal = new Date(aVal).getTime();
                bVal = new Date(bVal).getTime();
            }

            if (aVal < bVal) return sortOrder === "asc" ? -1 : 1;
            if (aVal > bVal) return sortOrder === "asc" ? 1 : -1;
            return 0;
        });
    }, [items, sortField, sortOrder]);

    // Pagination
    const paginatedItems = sortedItems.slice(
        (currentPage - 1) * itemsPerPage,
        currentPage * itemsPerPage
    );
    const totalPages = Math.ceil(items.length / itemsPerPage);

    const toggleSelection = (id: string, multi: boolean) => {
        const newSet = new Set(multi ? selectedIds : []);
        if (newSet.has(id)) {
            newSet.delete(id);
        } else {
            newSet.add(id);
        }
        setSelectedIds(newSet);
    };

    const handleSort = (field: SortField) => {
        if (sortField === field) {
            setSortOrder(sortOrder === "asc" ? "desc" : "asc");
        } else {
            setSortField(field);
            setSortOrder("asc");
        }
    };

    const getIcon = (item: FileItem) => {
        if (item.type === "folder") return <Folder className={cn("text-blue-500 fill-blue-500/20", viewMode === "grid" ? "h-12 w-12" : "h-5 w-5")} />;
        if (item.fileType === "code") return <FileCode className={cn("text-green-500", viewMode === "grid" ? "h-12 w-12" : "h-5 w-5")} />;
        if (item.fileType === "pdf") return <FileText className={cn("text-red-500", viewMode === "grid" ? "h-12 w-12" : "h-5 w-5")} />;
        return <FileText className={cn("text-gray-500", viewMode === "grid" ? "h-12 w-12" : "h-5 w-5")} />;
    };

    if (loading) return <ExplorerSkeleton />;

    return (
        <div className="w-full space-y-4" onClick={() => setSelectedIds(new Set())}>
            {/* Toolbar */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b pb-4">
                <div className="flex items-center text-sm text-muted-foreground flex-wrap">
                    {currentPath.map((path, idx) => (
                        <React.Fragment key={idx}>
                            <button
                                onClick={(e) => { e.stopPropagation(); onBreadcrumbClick(idx); }}
                                className={cn("hover:text-foreground transition-colors px-1 rounded hover:bg-muted", idx === currentPath.length - 1 && "font-semibold text-foreground")}
                            >
                                {path.name}
                            </button>
                            {idx < currentPath.length - 1 && <span className="mx-1 text-muted-foreground/50">/</span>}
                        </React.Fragment>
                    ))}
                </div>

                <div className="flex items-center gap-2" onClick={e => e.stopPropagation()}>
                    {selectedIds.size > 0 && onDelete && (
                        <Button variant="destructive" size="sm" onClick={() => {
                            const selected = items.filter(i => selectedIds.has(i.id));
                            onDelete(selected);
                        }}>
                            <Trash2 className="mr-2 h-4 w-4" /> Delete ({selectedIds.size})
                        </Button>
                    )}
                    <div className="flex items-center gap-1 bg-muted/50 p-1 rounded-lg">
                        <Button variant={viewMode === "grid" ? "secondary" : "ghost"} size="icon" className="h-8 w-8" onClick={() => setViewMode("grid")}>
                            <div className="grid grid-cols-2 gap-[1px]">
                                <div className="w-1 h-1 bg-current rounded-[0.5px]" />
                                <div className="w-1 h-1 bg-current rounded-[0.5px]" />
                                <div className="w-1 h-1 bg-current rounded-[0.5px]" />
                                <div className="w-1 h-1 bg-current rounded-[0.5px]" />
                            </div>
                        </Button>
                        <Button variant={viewMode === "list" ? "secondary" : "ghost"} size="icon" className="h-8 w-8" onClick={() => setViewMode("list")}>
                            <div className="flex flex-col gap-[3px]">
                                <div className="w-3 h-[1px] bg-current" />
                                <div className="w-3 h-[1px] bg-current" />
                                <div className="w-3 h-[1px] bg-current" />
                            </div>
                        </Button>
                    </div>
                </div>
            </div>

            {items.length === 0 ? (
                <EmptyState />
            ) : viewMode === "list" ? (
                <div className="border rounded-md">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="w-[30px]">
                                    <Checkbox
                                        checked={selectedIds.size === items.length}
                                        onCheckedChange={(checked) => {
                                            if (checked) setSelectedIds(new Set(items.map(i => i.id)));
                                            else setSelectedIds(new Set());
                                        }}
                                    />
                                </TableHead>
                                <TableHead className="cursor-pointer" onClick={() => handleSort("name")}>
                                    Name {sortField === "name" && <ArrowUpDown className="ml-2 h-4 w-4 inline" />}
                                </TableHead>
                                <TableHead className="cursor-pointer" onClick={() => handleSort("updatedAt")}>
                                    Date Modified {sortField === "updatedAt" && <ArrowUpDown className="ml-2 h-4 w-4 inline" />}
                                </TableHead>
                                <TableHead>Type</TableHead>
                                <TableHead className="text-right">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {paginatedItems.map((item) => (
                                <ContextMenu key={item.id}>
                                    <ContextMenuTrigger asChild>
                                        <TableRow
                                            className={cn("cursor-pointer", selectedIds.has(item.id) && "bg-muted/50")}
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                if (e.ctrlKey || e.metaKey) toggleSelection(item.id, true);
                                                else onNavigate(item);
                                            }}
                                        >
                                            <TableCell onClick={e => e.stopPropagation()}>
                                                <Checkbox
                                                    checked={selectedIds.has(item.id)}
                                                    onCheckedChange={() => toggleSelection(item.id, true)}
                                                />
                                            </TableCell>
                                            <TableCell>
                                                <div className="flex items-center gap-2">
                                                    {getIcon(item)}
                                                    <span className="font-medium">{item.name}</span>
                                                </div>
                                            </TableCell>
                                            <TableCell className="text-muted-foreground text-sm">
                                                {item.updatedAt ? new Date(item.updatedAt).toLocaleDateString() : "-"}
                                            </TableCell>
                                            <TableCell className="text-muted-foreground text-sm">
                                                {item.type === "folder" ? "Folder" : item.fileType?.toUpperCase()}
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <ActionMenu
                                                    item={item}
                                                    onNavigate={onNavigate}
                                                    onDownload={onDownload}
                                                    onRename={onRename}
                                                    onDelete={onDelete ? (i: FileItem) => onDelete([i]) : undefined}
                                                />
                                            </TableCell>
                                        </TableRow>
                                    </ContextMenuTrigger>
                                    <ContextMenuContent>
                                        <ContextMenuItem onClick={() => onNavigate(item)}>Open</ContextMenuItem>
                                        {item.id !== "theory" && item.id !== "lab" && (
                                            <>
                                                {item.url && <ContextMenuItem onClick={() => window.open(`${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}${item.url}`, "_blank")}>Download</ContextMenuItem>}
                                                {onRename && <ContextMenuItem onClick={() => onRename(item)}>Rename</ContextMenuItem>}
                                                <ContextMenuSeparator />
                                                {onDelete && <ContextMenuItem className="text-destructive" onClick={() => onDelete([item])}>Delete</ContextMenuItem>}
                                            </>
                                        )}
                                        {(item.id === "theory" || item.id === "lab") && onDelete && (
                                            <ContextMenuItem className="text-destructive" onClick={() => onDelete([item])}>Empty Folder</ContextMenuItem>
                                        )}
                                    </ContextMenuContent>
                                </ContextMenu>
                            ))}
                        </TableBody>
                    </Table>
                </div>
            ) : (
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                    {paginatedItems.map((item) => (
                        <GridItem
                            key={item.id}
                            item={item}
                            selected={selectedIds.has(item.id)}
                            onToggle={(multi: boolean) => toggleSelection(item.id, multi)}
                            onNavigate={onNavigate}
                            getIcon={getIcon}
                            actions={
                                <ActionMenu
                                    item={item}
                                    onNavigate={onNavigate}
                                    onDownload={onDownload}
                                    onRename={onRename}
                                    onDelete={onDelete ? (i: FileItem) => onDelete([i]) : undefined}
                                />
                            }
                            // Pass handlers directly to GridItem to use in its ContextMenu
                            handlers={{ onRename, onDelete, onDownload }}
                        />
                    ))}
                </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="flex items-center justify-end space-x-2 py-4">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                        disabled={currentPage === 1}
                    >
                        <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <div className="text-sm text-muted-foreground">
                        Page {currentPage} of {totalPages}
                    </div>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                        disabled={currentPage === totalPages}
                    >
                        <ChevronRight className="h-4 w-4" />
                    </Button>
                </div>
            )}
        </div>
    );
}

// Helper to check if item is special folder
const isSpecialFolder = (item: FileItem) => item.id === "theory" || item.id === "lab";

// Sub-components to keep main component clean
function ActionMenu({ item, onNavigate, onDownload, onRename, onDelete, onEmpty }: any) {
    const isSpecial = isSpecialFolder(item);

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={e => e.stopPropagation()}>
                    <MoreVertical className="h-4 w-4" />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onNavigate(item)}>Open</DropdownMenuItem>

                {!isSpecial && item.type === "file" && item.url && (
                    <DropdownMenuItem onClick={() => {
                        // Fix download by opening in new tab or triggering fetch
                        if (onDownload) onDownload(item);
                        else window.open(`${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}${item.url}`, "_blank");
                    }}>
                        <Download className="mr-2 h-4 w-4" /> Download
                    </DropdownMenuItem>
                )}

                {!isSpecial && onRename && (
                    <DropdownMenuItem onClick={() => onRename(item)}>
                        <Edit2 className="mr-2 h-4 w-4" /> Rename
                    </DropdownMenuItem>
                )}

                {isSpecial && onDelete && (
                    <DropdownMenuItem className="text-destructive focus:text-destructive" onClick={() => onDelete(item)}>
                        <Trash2 className="mr-2 h-4 w-4" /> Empty Folder
                    </DropdownMenuItem>
                )}

                {!isSpecial && onDelete && (
                    <>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem className="text-destructive focus:text-destructive" onClick={() => onDelete(item)}>
                            <Trash2 className="mr-2 h-4 w-4" /> Delete
                        </DropdownMenuItem>
                    </>
                )}
            </DropdownMenuContent>
        </DropdownMenu>
    );
}

function GridItem({ item, selected, onToggle, onNavigate, getIcon, actions, handlers }: any) {
    const isSpecial = isSpecialFolder(item);
    // Use handlers passed from parent or fallback (though actions.props hack was removed)
    const { onRename, onDelete } = handlers || {};

    return (
        <ContextMenu>
            <ContextMenuTrigger>
                <div
                    className={cn(
                        "group relative flex flex-col items-center justify-between p-4 border rounded-lg hover:bg-accent/50 cursor-pointer transition-all hover:shadow-sm bg-card h-40",
                        selected && "border-primary bg-accent/20 ring-1 ring-primary"
                    )}
                    onClick={(e) => {
                        e.stopPropagation();
                        if (e.ctrlKey || e.metaKey) onToggle(true);
                        else onNavigate(item);
                    }}
                >
                    <div className={cn("absolute top-2 left-2 z-10", !selected && "opacity-0 group-hover:opacity-100 transition-opacity")}>
                        <Checkbox
                            checked={selected}
                            onCheckedChange={() => onToggle(true)}
                            onClick={(e) => e.stopPropagation()}
                        />
                    </div>
                    <div className="mb-3 transform group-hover:scale-105 transition-transform">
                        {getIcon(item)}
                    </div>
                    <div className="text-center w-full">
                        <div className="text-sm font-medium truncate" title={item.name}>{item.name}</div>
                        <div className="text-xs text-muted-foreground mt-1">
                            {item.type === "folder" ? item.name === "Theory" || item.name === "Lab" ? "Folder" : "Folder" : item.fileType?.toUpperCase()}
                        </div>
                    </div>
                    <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        {actions}
                    </div>
                </div>
            </ContextMenuTrigger>
            <ContextMenuContent>
                <ContextMenuItem onClick={() => onNavigate(item)}>Open</ContextMenuItem>
                {!isSpecial && item.type === "file" && (
                    <ContextMenuItem onClick={() => window.open(`${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}${item.url}`, "_blank")}>Download</ContextMenuItem>
                )}
                {!isSpecial && onRename && <ContextMenuItem onClick={() => onRename(item)}>Rename</ContextMenuItem>}

                {isSpecial && onDelete && <ContextMenuItem className="text-destructive" onClick={() => onDelete([item])}>Empty Folder</ContextMenuItem>}

                {!isSpecial && onDelete && (
                    <>
                        <ContextMenuSeparator />
                        <ContextMenuItem className="text-destructive" onClick={() => onDelete([item])}>Delete</ContextMenuItem>
                    </>
                )}
            </ContextMenuContent>
        </ContextMenu>
    );
}

function ExplorerSkeleton() {
    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
                <div className="flex gap-2"><Skeleton className="h-6 w-24" /><Skeleton className="h-6 w-24" /></div>
                <Skeleton className="h-8 w-20" />
            </div>
            <div className="space-y-2">
                {[...Array(5)].map((_, i) => (
                    <Skeleton key={i} className="h-12 w-full" />
                ))}
            </div>
        </div>
    );
}

function EmptyState() {
    return (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground border-2 border-dashed rounded-lg bg-muted/5">
            <Folder className="h-10 w-10 mb-2 opacity-50" />
            <p>Folder is empty</p>
        </div>
    );
}
