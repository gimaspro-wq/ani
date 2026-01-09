"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import type { Episode } from "@/lib/types";
import { VideoPlayer } from "./VideoPlayer";
import { cn } from "@/lib/utils";

interface EpisodePlayerWrapperProps {
  slug: string;
  episodes: Episode[];
  currentNumber: number;
  sources: Episode["video_sources"];
  animeTitle: string;
}

export function EpisodePlayerWrapper({
  slug,
  episodes,
  currentNumber,
  sources,
  animeTitle,
}: EpisodePlayerWrapperProps) {
  const router = useRouter();

  const { prev, next } = useMemo(() => {
    let prevEpisode: Episode | undefined;
    let nextEpisode: Episode | undefined;

    for (const ep of episodes) {
      if (ep.number < currentNumber) {
        if (!prevEpisode || ep.number > prevEpisode.number) {
          prevEpisode = ep;
        }
      } else if (ep.number > currentNumber) {
        if (!nextEpisode || ep.number < nextEpisode.number) {
          nextEpisode = ep;
        }
      }
    }

    return { prev: prevEpisode, next: nextEpisode };
  }, [episodes, currentNumber]);

  const goTo = (num: number | undefined) => {
    if (!num) return;
    router.push(`/anime/${slug}/episode/${num}`);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => goTo(prev?.number)}
          disabled={!prev}
          className={cn(
            "rounded-lg border border-border px-3 py-2 text-sm transition hover:border-cyan/60 hover:text-cyan",
            !prev && "cursor-not-allowed opacity-50 hover:border-border hover:text-muted-foreground",
          )}
        >
          ← Предыдущая
        </button>
        <button
          type="button"
          onClick={() => goTo(next?.number)}
          disabled={!next}
          className={cn(
            "rounded-lg border border-border px-3 py-2 text-sm transition hover:border-cyan/60 hover:text-cyan",
            !next && "cursor-not-allowed opacity-50 hover:border-border hover:text-muted-foreground",
          )}
        >
          Следующая →
        </button>
      </div>

      <VideoPlayer
        sources={sources}
        title={animeTitle}
        onEnded={() => {
          if (next) {
            goTo(next.number);
          }
        }}
      />
    </div>
  );
}
