import Image from "next/image";
import Link from "next/link";
import type { AnimeListItem } from "@/lib/types";
import { cn } from "@/lib/utils";

interface AnimeCardProps {
  anime: AnimeListItem;
  className?: string;
}

export function AnimeCard({ anime, className }: AnimeCardProps) {
  const yearLabel = anime.year ?? "—";
  const statusLabel = anime.status ?? "—";

  return (
    <Link
      href={`/anime/${anime.slug}`}
      className={cn(
        "group block rounded-lg border border-border bg-foreground/[0.02] p-2 transition hover:-translate-y-1 hover:border-foreground/30",
        className,
      )}
    >
      <div className="relative aspect-[3/4] overflow-hidden rounded-md bg-foreground/5">
        {anime.poster ? (
          <Image
            src={anime.poster}
            alt={anime.title}
            fill
            className="object-cover transition-transform duration-300 group-hover:scale-105"
            sizes="(min-width: 1024px) 200px, 33vw"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-muted-foreground/70">
            Нет постера
          </div>
        )}
      </div>

      <div className="mt-2 space-y-1">
        <h3 className="line-clamp-2 text-sm font-medium text-foreground group-hover:text-cyan transition-colors">
          {anime.title}
        </h3>
        <p className="text-xs text-muted-foreground/70">
          {yearLabel} · {statusLabel}
        </p>
      </div>
    </Link>
  );
}
