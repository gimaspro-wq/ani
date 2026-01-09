import type { AnimeListItem } from "@/lib/types";
import { cn } from "@/lib/utils";
import { AnimeCard } from "./AnimeCard";

interface AnimeGridProps {
  anime: AnimeListItem[];
  isLoading?: boolean;
  className?: string;
}

export function AnimeGridSkeleton({ count = 12 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className="h-full rounded-lg border border-border bg-foreground/[0.02] p-2"
        >
          <div className="aspect-[3/4] w-full rounded-md bg-foreground/10 animate-pulse" />
          <div className="mt-2 space-y-2">
            <div className="h-4 w-3/4 rounded bg-foreground/10 animate-pulse" />
            <div className="h-3 w-1/2 rounded bg-foreground/10 animate-pulse" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function AnimeGrid({ anime, isLoading, className }: AnimeGridProps) {
  if (isLoading) {
    return <AnimeGridSkeleton />;
  }

  if (!anime?.length) {
    return (
      <div className="rounded-lg border border-border bg-foreground/[0.02] p-8 text-center text-muted-foreground">
        Каталог пока пуст
      </div>
    );
  }

  return (
    <div
      className={cn(
        "grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4",
        className,
      )}
    >
      {anime.map((item) => (
        <AnimeCard key={item.slug} anime={item} />
      ))}
    </div>
  );
}
