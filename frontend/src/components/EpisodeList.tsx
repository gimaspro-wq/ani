import Link from "next/link";
import type { Episode } from "@/lib/types";
import { cn } from "@/lib/utils";

interface EpisodeListProps {
  episodes: Episode[];
  slug: string;
  currentNumber?: number;
  className?: string;
}

export function EpisodeListSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className="rounded-lg border border-border bg-foreground/[0.02] p-4"
        >
          <div className="h-4 w-1/2 rounded bg-foreground/10 animate-pulse" />
          <div className="mt-2 h-3 w-3/4 rounded bg-foreground/10 animate-pulse" />
        </div>
      ))}
    </div>
  );
}

export function EpisodeList({ episodes, slug, currentNumber, className }: EpisodeListProps) {
  if (!episodes?.length) {
    return (
      <div className="rounded-lg border border-border bg-foreground/[0.02] p-6 text-center text-muted-foreground">
        Серии пока недоступны
      </div>
    );
  }

  return (
    <div className={cn("space-y-3", className)}>
      <h2 className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
        Список серий
      </h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {episodes.map((episode) => {
          const isActive = episode.number === currentNumber;
          return (
            <Link
              key={episode.id ?? episode.number}
              href={`/anime/${slug}/episode/${episode.number}`}
              className={cn(
                "flex flex-col rounded-lg border border-border bg-foreground/[0.02] p-4 transition hover:border-cyan/60 hover:bg-cyan/5",
                isActive && "border-cyan/70 bg-cyan/5 shadow-[0_0_0_1px_rgba(45,212,191,0.3)]",
              )}
            >
              <span className="text-xs text-muted-foreground/70">Серия {episode.number}</span>
              <span className="mt-1 line-clamp-2 text-sm text-foreground">
                {episode.title || `Эпизод ${episode.number}`}
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
