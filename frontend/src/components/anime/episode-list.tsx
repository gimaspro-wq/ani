"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { orpc } from "@/lib/query/orpc";
import { useServerProgress } from "@/hooks/use-server-progress";
import { Spinner } from "@/components/ui/spinner";
import { determineResumeAction } from "@/lib/resume-logic";

interface EpisodeListProps {
  animeId: string;
  animeName: string;
}

export function EpisodeList({ animeId, animeName }: EpisodeListProps) {
  const { data: episodesData, isLoading } = useQuery({
    ...orpc.anime.getEpisodes.queryOptions({ input: { id: animeId } }),
    refetchOnWindowFocus: false,
  });

  const { getProgress } = useServerProgress({ titleId: animeId });

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner className="size-6 text-muted-foreground" />
      </div>
    );
  }

  if (!episodesData?.episodes || episodesData.episodes.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No episodes available
      </div>
    );
  }

  const episodes = episodesData.episodes;
  
  // Find the episode to resume/continue
  let resumeEpisodeNumber: number | null = null;
  
  // Get all progress for this anime
  const allProgress = episodes
    .map(ep => ({ episode: ep, progress: getProgress(animeId, ep.number) }))
    .filter(item => item.progress !== null);
  
  if (allProgress.length > 0) {
    // Sort by updatedAt to find the most recent
    const sorted = allProgress.sort((a, b) => 
      (b.progress?.updatedAt || 0) - (a.progress?.updatedAt || 0)
    );
    
    const mostRecent = sorted[0];
    if (mostRecent.progress) {
      const action = determineResumeAction({
        animeId,
        episodeNumber: mostRecent.episode.number,
        currentTime: mostRecent.progress.currentTime,
        duration: mostRecent.progress.duration,
        updatedAt: mostRecent.progress.updatedAt,
      }, episodes.length);
      
      resumeEpisodeNumber = action.episodeNumber;
    }
  }

  return (
    <div className="space-y-2">
      <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-4">
        Episodes
      </h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
        {episodes.map((episode) => {
          const episodeNumber = episode.number;
          const progress = getProgress(animeId, episodeNumber);
          const progressPercent = progress
            ? Math.round((progress.currentTime / progress.duration) * 100)
            : 0;
          const hasProgress = progress && progressPercent > 0 && progressPercent < 95;
          const isResumeEpisode = episodeNumber === resumeEpisodeNumber;

          return (
            <Link
              key={episode.episodeId}
              href={`/watch/${animeId}/${episodeNumber}`}
              className="group relative block"
            >
              <div
                className={`
                  relative rounded-lg border transition-colors overflow-hidden
                  ${isResumeEpisode ? "border-cyan bg-cyan/10 ring-2 ring-cyan/30" : 
                    hasProgress ? "border-cyan/50 bg-cyan/5" : 
                    "border-border bg-foreground/5"}
                  hover:border-foreground/30 hover:bg-foreground/10
                `}
              >
                <div className="aspect-video flex flex-col items-center justify-center p-4">
                  {/* Episode number */}
                  <div className="text-center">
                    <div className="text-lg font-medium text-foreground">
                      {episodeNumber}
                    </div>
                    {episode.title && episode.title !== `Episode ${episodeNumber}` && (
                      <div className="text-xs text-muted-foreground mt-1 line-clamp-2">
                        {episode.title}
                      </div>
                    )}
                  </div>

                  {/* Filler badge */}
                  {episode.isFiller && (
                    <div className="absolute top-2 right-2 px-2 py-0.5 rounded text-[10px] font-medium bg-amber-500/20 text-amber-500">
                      Filler
                    </div>
                  )}
                  
                  {/* Resume badge */}
                  {isResumeEpisode && (
                    <div className="absolute top-2 left-2 px-2 py-0.5 rounded text-[10px] font-medium bg-cyan/90 text-white">
                      Resume
                    </div>
                  )}
                </div>

                {/* Progress bar */}
                {hasProgress && (
                  <div className="absolute bottom-0 left-0 right-0 h-1 bg-foreground/10">
                    <div
                      className="h-full bg-cyan transition-all"
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>
                )}
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
