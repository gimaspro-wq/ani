"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Navbar } from "@/components/blocks/navbar";
import { Footer } from "@/components/blocks/footer";
import { useHistory } from "@/hooks/use-server-progress";
import { useWatchProgress } from "@/hooks/use-watch-progress";
import { backendAPI } from "@/lib/api/backend";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { determineResumeAction, formatRelativeTime, formatProgress, DEFAULT_EPISODE_DURATION_SECONDS } from "@/lib/resume-logic";
import { Trash2, Trash } from "lucide-react";
import { toast } from "sonner";

interface HistoryItemData {
  id?: number;
  animeId: string;
  episodeNumber: number;
  poster?: string;
  name?: string;
  currentTime: number;
  duration: number;
  updatedAt: number;
}

export default function HistoryPage() {
  const isAuthenticated = backendAPI.isAuthenticated();
  const { items: serverHistory, isLoading, deleteEntry, clearAll, isDeleting, isClearing } = useHistory({ limit: 100 });
  const { getAllRecentlyWatched, clearProgress: clearLocalProgress } = useWatchProgress();
  const [showClearDialog, setShowClearDialog] = useState(false);

  // Get local history
  const localHistory = getAllRecentlyWatched(100);

  // For authenticated users, we show server history
  // For guests, we show local history
  const historyItems: HistoryItemData[] = isAuthenticated && serverHistory.length > 0
    ? serverHistory.map(item => {
        // Extract episode number from episode_id (format: "animeId-ep-N")
        const episodeMatch = item.episode_id.match(/-ep-(\d+)$/);
        const episodeNumber = episodeMatch ? parseInt(episodeMatch[1], 10) : 1;
        
        return {
          id: item.id,
          animeId: item.title_id,
          episodeNumber,
          currentTime: item.position_seconds || 0,
          duration: DEFAULT_EPISODE_DURATION_SECONDS,
          updatedAt: new Date(item.watched_at).getTime(),
        };
      })
    : localHistory;

  const handleDeleteEntry = (item: HistoryItemData) => {
    if (isAuthenticated && item.id) {
      deleteEntry(item.id, {
        onSuccess: () => {
          toast.success("History entry removed");
        },
        onError: () => {
          toast.error("Failed to remove history entry");
        },
      });
    } else {
      // For guests, clear local progress
      clearLocalProgress(item.animeId, item.episodeNumber);
      toast.success("History entry removed");
    }
  };

  const handleClearAll = () => {
    if (isAuthenticated) {
      clearAll('rpc', {
        onSuccess: () => {
          toast.success("History cleared");
          setShowClearDialog(false);
        },
        onError: () => {
          toast.error("Failed to clear history");
        },
      });
    } else {
      // For guests, clear all local progress
      localHistory.forEach(item => {
        clearLocalProgress(item.animeId, item.episodeNumber);
      });
      toast.success("History cleared");
      setShowClearDialog(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <main className="pt-14 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="py-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold">Watch History</h1>
              <p className="text-sm text-muted-foreground mt-1">
                Recently watched episodes
              </p>
            </div>
            {historyItems.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowClearDialog(true)}
                disabled={isClearing}
              >
                <Trash className="w-4 h-4 mr-2" />
                Clear All
              </Button>
            )}
          </div>

          {/* Loading state */}
          {isLoading && (
            <div className="space-y-4">
              {Array.from({ length: 5 }).map((_, index) => (
                <div key={index} className="flex gap-4 p-4 rounded-lg border border-border">
                  <Skeleton className="w-24 h-36 rounded-md" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-5 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                    <Skeleton className="h-3 w-1/4" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Empty state */}
          {!isLoading && historyItems.length === 0 && (
            <div className="text-center py-16 text-muted-foreground">
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
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <p className="text-lg mb-2">No watch history</p>
              <p className="text-sm">Start watching anime to build your history</p>
            </div>
          )}

          {/* History list */}
          {!isLoading && historyItems.length > 0 && (
            <div className="space-y-3">
              {historyItems.map((item, index) => {
                const action = determineResumeAction({
                  animeId: item.animeId,
                  episodeNumber: item.episodeNumber,
                  currentTime: item.currentTime,
                  duration: item.duration,
                  updatedAt: item.updatedAt,
                });

                return (
                  <div
                    key={`${item.animeId}-${item.episodeNumber}-${index}`}
                    className="flex flex-col sm:flex-row gap-4 p-4 rounded-lg border border-border hover:border-foreground/30 transition-colors group"
                  >
                    <div className="flex gap-4 flex-1 min-w-0">
                      {/* Poster */}
                      <Link
                        href={`/anime/${item.animeId}`}
                        className="relative w-20 sm:w-24 aspect-3/4 rounded-md overflow-hidden bg-foreground/5 shrink-0"
                      >
                        {item.poster ? (
                          <Image
                            src={item.poster}
                            alt={item.name || item.animeId}
                            fill
                            className="object-cover transition-transform duration-300 group-hover:scale-105"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                            <svg className="w-8 h-8 opacity-30" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
                            </svg>
                          </div>
                        )}
                      </Link>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <Link
                          href={`/anime/${item.animeId}`}
                          className="block hover:text-foreground transition-colors"
                        >
                          <h3 className="font-medium line-clamp-1">
                            {item.name || item.animeId}
                          </h3>
                        </Link>
                        <p className="text-sm text-muted-foreground mt-1">
                          Episode {item.episodeNumber}
                        </p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                          <span>{formatProgress(item.currentTime, item.duration)}</span>
                          <span>•</span>
                          <span>{formatRelativeTime(item.updatedAt)}</span>
                        </div>
                      </div>

                      {/* Actions - Desktop */}
                      <div className="hidden sm:flex items-center gap-2 shrink-0">
                        <Button
                          asChild
                          size="sm"
                        >
                          <Link href={`/watch/${item.animeId}/${action.episodeNumber}`}>
                            {action.label}
                          </Link>
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteEntry(item)}
                          disabled={isDeleting}
                          className="text-muted-foreground hover:text-destructive"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>

                    {/* Actions - Mobile */}
                    <div className="flex sm:hidden items-center gap-2">
                      <Button
                        asChild
                        size="sm"
                        className="flex-1"
                      >
                        <Link href={`/watch/${item.animeId}/${action.episodeNumber}`}>
                          {action.label}
                        </Link>
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteEntry(item)}
                        disabled={isDeleting}
                        className="text-muted-foreground hover:text-destructive"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>

      <Footer />

      {/* Clear all confirmation dialog */}
      <Dialog open={showClearDialog} onOpenChange={setShowClearDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Clear watch history?</DialogTitle>
            <DialogDescription>
              This will remove all watch history entries. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowClearDialog(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleClearAll} disabled={isClearing}>
              {isClearing ? "Clearing..." : "Clear History"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
