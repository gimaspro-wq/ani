import Image from "next/image";
import type { AnimeDetail } from "@/lib/types";
import { cn } from "@/lib/utils";

interface AnimeHeaderProps {
  anime: AnimeDetail;
  className?: string;
}

export function AnimeHeader({ anime, className }: AnimeHeaderProps) {
  return (
    <section
      className={cn(
        "relative overflow-hidden rounded-2xl border border-border bg-foreground/[0.02]",
        className,
      )}
    >
      <div className="grid gap-6 p-6 md:grid-cols-[220px_1fr] lg:grid-cols-[260px_1fr]">
        <div className="relative h-full min-h-[280px] overflow-hidden rounded-xl bg-foreground/5">
          {anime.poster ? (
            <Image
              src={anime.poster}
              alt={anime.title}
              fill
              sizes="(min-width: 1024px) 260px, 40vw"
              className="object-cover"
              priority
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
              Нет постера
            </div>
          )}
        </div>

        <div className="flex flex-col gap-4">
          <div className="space-y-2">
            <p className="text-xs uppercase tracking-wide text-muted-foreground/70">
              {anime.year ?? "Неизвестно"} · {anime.status ?? "Статус неизвестен"}
            </p>
            <h1 className="text-3xl font-semibold text-foreground lg:text-4xl">
              {anime.title}
            </h1>
            {anime.alternative_titles?.length ? (
              <p className="text-sm text-muted-foreground">
                {anime.alternative_titles.join(" • ")}
              </p>
            ) : null}
          </div>

          {anime.description ? (
            <p className="text-muted-foreground leading-relaxed">
              {anime.description}
            </p>
          ) : (
            <p className="text-muted-foreground/70">Описание отсутствует.</p>
          )}

          {anime.genres?.length ? (
            <div className="flex flex-wrap gap-2">
              {anime.genres.map((genre) => (
                <span
                  key={genre}
                  className="rounded-full bg-foreground/5 px-3 py-1 text-xs text-muted-foreground"
                >
                  {genre}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
