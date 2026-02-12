"use client";

import * as React from "react";
import { ChevronDown, Check, X, CheckSquare, Square, ToggleLeft, Search } from "lucide-react";
import { cn } from "@/lib/utils";

export interface MultiSelectOption {
  value: string;
  label: string;
  description?: string;
}

export interface MultiSelectOptionGroup {
  label: string;
  options: MultiSelectOption[];
}

interface MultiSelectProps {
  options: MultiSelectOption[];
  selected: string[];
  onChange: (selected: string[]) => void;
  placeholder?: string;
  emptyText?: string;
  className?: string;
  disabled?: boolean;
  size?: "default" | "sm";
  /** Optional grouped options. If provided, takes precedence over `options`. */
  groups?: MultiSelectOptionGroup[];
  /** Show a search/filter input in the dropdown. */
  searchable?: boolean;
  searchPlaceholder?: string;
}

export function MultiSelect({
  options,
  selected,
  onChange,
  placeholder = "Select...",
  emptyText = "All",
  className,
  disabled = false,
  size = "default",
  groups,
  searchable = false,
  searchPlaceholder = "Filter...",
}: MultiSelectProps) {
  const isSmall = size === "sm";
  const [isOpen, setIsOpen] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState("");
  const containerRef = React.useRef<HTMLDivElement>(null);
  const searchInputRef = React.useRef<HTMLInputElement>(null);

  // Flatten groups into options for operations like selectAll, display, etc.
  const allOptions = React.useMemo(() => {
    if (groups && groups.length > 0) {
      return groups.flatMap((g) => g.options);
    }
    return options;
  }, [groups, options]);

  // Filter groups/options by search query
  const filteredGroups = React.useMemo(() => {
    if (!searchable || !searchQuery.trim()) return groups;
    if (!groups) return groups;
    const q = searchQuery.toLowerCase();
    return groups
      .map((g) => ({
        ...g,
        options: g.options.filter(
          (o) => o.label.toLowerCase().includes(q) || o.value.toLowerCase().includes(q)
        ),
      }))
      .filter((g) => g.options.length > 0);
  }, [groups, searchQuery, searchable]);

  const filteredOptions = React.useMemo(() => {
    if (!searchable || !searchQuery.trim()) return options;
    const q = searchQuery.toLowerCase();
    return options.filter(
      (o) => o.label.toLowerCase().includes(q) || o.value.toLowerCase().includes(q)
    );
  }, [options, searchQuery, searchable]);

  // Close dropdown when clicking outside
  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery("");
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Auto-focus search input when dropdown opens
  React.useEffect(() => {
    if (isOpen && searchable) {
      setTimeout(() => searchInputRef.current?.focus(), 0);
    }
  }, [isOpen, searchable]);

  const toggleOption = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter((v) => v !== value));
    } else {
      onChange([...selected, value]);
    }
  };

  const clearAll = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    onChange([]);
  };

  const selectAll = () => {
    onChange(allOptions.map((o) => o.value));
  };

  const invertSelection = () => {
    const newSelected = allOptions
      .filter((o) => !selected.includes(o.value))
      .map((o) => o.value);
    onChange(newSelected);
  };

  const allSelected = allOptions.length > 0 && selected.length === allOptions.length;
  const noneSelected = selected.length === 0;

  const displayText = selected.length === 0
    ? emptyText
    : selected.length === 1
      ? allOptions.find(o => o.value === selected[0])?.label || selected[0]
      : `${selected.length} selected`;

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={cn(
          "flex items-center justify-between w-full",
          "border rounded-md bg-background",
          "hover:bg-accent hover:text-accent-foreground",
          "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
          disabled && "opacity-50 cursor-not-allowed",
          isOpen && "ring-2 ring-ring ring-offset-2",
          isSmall ? "px-2 py-1 text-xs" : "px-3 py-2 text-sm"
        )}
      >
        <span className={cn(
          "truncate",
          selected.length === 0 && "text-muted-foreground"
        )}>
          {displayText}
        </span>
        <div className={cn("flex items-center gap-0.5", isSmall ? "ml-1" : "ml-2")}>
          {selected.length > 0 && (
            <span
              onClick={clearAll}
              className="p-0.5 hover:bg-muted rounded"
            >
              <X className={isSmall ? "h-2.5 w-2.5" : "h-3 w-3"} />
            </span>
          )}
          <ChevronDown className={cn(
            "transition-transform",
            isSmall ? "h-3 w-3" : "h-4 w-4",
            isOpen && "rotate-180"
          )} />
        </div>
      </button>

      {isOpen && (
        <div className={cn(
          "absolute z-50 w-full mt-1 bg-popover border rounded-md shadow-lg max-h-60 overflow-auto",
          isSmall && "min-w-[160px]"
        )}>
          {allOptions.length === 0 ? (
            <div className={cn(
              "text-muted-foreground",
              isSmall ? "px-2 py-1.5 text-xs" : "px-3 py-2 text-sm"
            )}>
              No options available
            </div>
          ) : (
            <>
              {/* Select All / Clear All / Invert toolbar */}
              <div className={cn(
                "flex items-center gap-1 border-b bg-muted/50 sticky top-0",
                isSmall ? "px-2 py-1" : "px-2 py-1.5"
              )}>
                <button
                  type="button"
                  onClick={selectAll}
                  disabled={allSelected}
                  className={cn(
                    "flex items-center gap-1 px-2 py-0.5 rounded text-xs",
                    "hover:bg-accent hover:text-accent-foreground",
                    "disabled:opacity-50 disabled:cursor-not-allowed"
                  )}
                >
                  <CheckSquare className="h-3 w-3" />
                  All
                </button>
                <button
                  type="button"
                  onClick={clearAll}
                  disabled={noneSelected}
                  className={cn(
                    "flex items-center gap-1 px-2 py-0.5 rounded text-xs",
                    "hover:bg-accent hover:text-accent-foreground",
                    "disabled:opacity-50 disabled:cursor-not-allowed"
                  )}
                >
                  <Square className="h-3 w-3" />
                  None
                </button>
                <button
                  type="button"
                  onClick={invertSelection}
                  className={cn(
                    "flex items-center gap-1 px-2 py-0.5 rounded text-xs",
                    "hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <ToggleLeft className="h-3 w-3" />
                  Invert
                </button>
              </div>
              {/* Search filter input */}
              {searchable && (
                <div className={cn("border-b sticky top-[33px] bg-popover", isSmall ? "px-2 py-1" : "px-2 py-1.5")}>
                  <div className="relative">
                    <Search className={cn("absolute left-2 top-1/2 -translate-y-1/2 text-muted-foreground", isSmall ? "h-3 w-3" : "h-3.5 w-3.5")} />
                    <input
                      ref={searchInputRef}
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder={searchPlaceholder}
                      className={cn(
                        "w-full bg-muted/50 border rounded pl-7 pr-2 outline-none focus:ring-1 focus:ring-ring",
                        isSmall ? "py-0.5 text-xs" : "py-1 text-sm"
                      )}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>
                </div>
              )}
              {/* No results message */}
              {searchable && searchQuery.trim() && (
                (filteredGroups ? filteredGroups.length === 0 : filteredOptions.length === 0)
              ) && (
                <div className={cn(
                  "text-muted-foreground text-center",
                  isSmall ? "px-2 py-2 text-xs" : "px-3 py-3 text-sm"
                )}>
                  No matches
                </div>
              )}
              {/* Render grouped options if groups provided, otherwise flat options */}
              {filteredGroups && filteredGroups.length > 0 ? (
                filteredGroups.map((group, groupIndex) => (
                  <React.Fragment key={group.label}>
                    {/* Group header */}
                    <div className={cn(
                      "text-xs font-semibold text-muted-foreground uppercase tracking-wide bg-muted/30",
                      isSmall ? "px-2 py-1" : "px-3 py-1.5",
                      groupIndex > 0 && "border-t"
                    )}>
                      {group.label}
                    </div>
                    {/* Group options */}
                    {group.options.map((option) => (
                      <div
                        key={option.value}
                        onClick={() => toggleOption(option.value)}
                        className={cn(
                          "flex items-center gap-2 cursor-pointer",
                          "hover:bg-accent hover:text-accent-foreground",
                          selected.includes(option.value) && "bg-accent/50",
                          isSmall ? "px-2 py-1.5 text-xs" : "px-3 py-2 text-sm"
                        )}
                      >
                        <div className={cn(
                          "flex items-center justify-center border rounded shrink-0",
                          selected.includes(option.value)
                            ? "bg-primary border-primary text-primary-foreground"
                            : "border-input",
                          isSmall ? "w-3 h-3" : "w-4 h-4"
                        )}>
                          {selected.includes(option.value) && (
                            <Check className={isSmall ? "h-2 w-2" : "h-3 w-3"} />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="truncate">{option.label}</div>
                          {option.description && !isSmall && (
                            <div className="text-xs text-muted-foreground truncate">
                              {option.description}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </React.Fragment>
                ))
              ) : (
                filteredOptions.map((option) => (
                  <div
                    key={option.value}
                    onClick={() => toggleOption(option.value)}
                    className={cn(
                      "flex items-center gap-2 cursor-pointer",
                      "hover:bg-accent hover:text-accent-foreground",
                      selected.includes(option.value) && "bg-accent/50",
                      isSmall ? "px-2 py-1.5 text-xs" : "px-3 py-2 text-sm"
                    )}
                  >
                    <div className={cn(
                      "flex items-center justify-center border rounded shrink-0",
                      selected.includes(option.value)
                        ? "bg-primary border-primary text-primary-foreground"
                        : "border-input",
                      isSmall ? "w-3 h-3" : "w-4 h-4"
                    )}>
                      {selected.includes(option.value) && (
                        <Check className={isSmall ? "h-2 w-2" : "h-3 w-3"} />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="truncate">{option.label}</div>
                      {option.description && !isSmall && (
                        <div className="text-xs text-muted-foreground truncate">
                          {option.description}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
