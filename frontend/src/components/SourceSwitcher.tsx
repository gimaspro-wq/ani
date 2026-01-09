"use client";

import type { VideoSource } from "@/lib/types";
import { cn } from "@/lib/utils";

interface SourceSwitcherProps {
  sources: VideoSource[];
  activeId: string;
  onSelect: (id: string) => void;
}

export function SourceSwitcher({ sources, activeId, onSelect }: SourceSwitcherProps) {
  if (sources.length <= 1) return null;

  return (
    <div className="flex flex-wrap gap-2">
      {sources.map((source) => (
        <button
          key={source.id}
          type="button"
          onClick={() => onSelect(source.id)}
          className={cn(
            "rounded-md border border-border px-3 py-1.5 text-sm transition hover:border-cyan/60 hover:text-cyan",
            activeId === source.id && "border-cyan/80 bg-cyan/5 text-cyan",
          )}
        >
          {source.source_name || "Источник"}
        </button>
      ))}
    </div>
  );
}
