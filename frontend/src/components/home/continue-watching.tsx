"use client";

import { useMemo } from "react";
import Link from "next/link";
import Image from "next/image";
import { useHistory } from "@/hooks/use-server-progress";
import { useWatchProgress } from "@/hooks/use-watch-progress";
import { backendAPI } from "@/lib/api/backend";
import { Skeleton } from "@/components/ui/skeleton";
import { determineResumeAction } from "@/lib/resume-logic";

interface ContinueWatchingItem {
  animeId: string;
  episodeNumber: number;
  poster?: string;
  name?: string;
  currentTime: number;
  duration: number;
  updatedAt: number;
}

export function ContinueWatching() {
  const isAuthenticated = backendAPI.isAuthenticated();
  const { items: historyItems, isLoading: historyLoading } = useHistory({ limit: 50 });
  const { getAllRecentlyWatched } = useWatchProgress();

  // Merge, deduplicate, and sort watch data
  const continueWatchingItems = useMemo(() => {
    const itemsByTitle = new Map<string, ContinueWatchingItem>();

    // Get local progress
    const localProgress = getAllRecentlyWatched(50);
    
    // Add local progress to map
    for (const progress of localProgress) {
      const existing = itemsByTitle.get(progress.animeId);
      // Keep the most recent one
      if (!existing || progress.updatedAt > existing.updatedAt) {
        itemsByTitle.set(progress.animeId, progress);
      }
    }

    // Convert to array and sort by updatedAt descending (most recent first)
    const items = Array.from(itemsByTitle.values())
      .sort((a, b) => b.updatedAt - a.updatedAt)
      .slice(0, 10); // Limit to 10 items

    return items;
  }, [getAllRecentlyWatched]);

  if (historyLoading) {
    return (
      <div className="space-y-6">
        <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
          Continue Watching
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {Array.from({ length: 5 }).map((_, index) => (
            <div key={index} className="space-y-2">
              <Skeleton className="aspect-3/4 rounded-lg" />
              <Skeleton className="h-3 w-3/4 rounded" />
              <Skeleton className="h-2 w-1/2 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (continueWatchingItems.length === 0) {
    return (
      <div className="space-y-6">
        <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
          Continue Watching
        </h2>
        <div className="text-center py-12 text-muted-foreground">
          <svg
            className="w-16 h-16 mx-auto mb-4 opacity-30"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
            />
          </svg>
          <p className="text-lg mb-2">Start watching anime</p>
          <p className="text-sm">Your watch progress will appear here</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
          Continue Watching
        </h2>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {continueWatchingItems.map((item) => {
          const progressPercent = Math.round(
            (item.currentTime / item.duration) * 100
          );
          
          // Determine whether to resume or play next episode
          const action = determineResumeAction({
            animeId: item.animeId,
            episodeNumber: item.episodeNumber,
            currentTime: item.currentTime,
            duration: item.duration,
            updatedAt: item.updatedAt,
          });

          return (
            <Link
              key={`${item.animeId}-${item.episodeNumber}`}
              href={`/watch/${item.animeId}/${action.episodeNumber}`}
              className="group block"
            >
              <div className="relative aspect-3/4 rounded-lg overflow-hidden bg-foreground/5">
                {item.poster ? (
                  <Image
                    src={item.poster}
                    alt={item.name || item.animeId}
                    fill
                    className="object-cover transition-transform duration-300 group-hover:scale-105"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                    <svg
                      className="w-12 h-12 opacity-30"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
                    </svg>
                  </div>
                )}

                {/* Progress bar */}
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-black/50">
                  <div
                    className="h-full bg-cyan transition-all"
                    style={{ width: `${Math.min(progressPercent, 100)}%` }}
                  />
                </div>

                {/* Episode badge */}
                <div className="absolute top-2 left-2 px-2 py-1 rounded bg-black/70 text-xs font-medium text-white">
                  EP {action.episodeNumber}
                </div>
                
                {/* Resume/Next indicator */}
                {action.type === 'next' && (
                  <div className="absolute top-2 right-2 px-2 py-1 rounded bg-cyan/90 text-xs font-medium text-white">
                    Next
                  </div>
                )}
              </div>
              <h3 className="mt-2 text-sm text-muted-foreground line-clamp-1 group-hover:text-foreground transition-colors">
                {item.name || item.animeId}
              </h3>
              <p className="text-xs text-muted-foreground/60">
                {action.type === 'next' ? 'Ready for next episode' : `${progressPercent}% watched`}
              </p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
