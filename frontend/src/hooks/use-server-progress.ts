"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { backendAPI, type Progress, type History } from "@/lib/api/backend";
import { useWatchProgress as useLocalWatchProgress } from "./use-watch-progress";
import { useCallback } from "react";

/**
 * Hook for server-synced progress tracking.
 * Falls back to local storage when user is not authenticated.
 */
export function useServerProgress(params?: {
  provider?: string;
  titleId?: string;
}) {
  const queryClient = useQueryClient();
  const isAuthenticated = backendAPI.isAuthenticated();
  const localProgress = useLocalWatchProgress();

  // Query for progress items
  const { data: items = [], isLoading, error } = useQuery({
    queryKey: ['progress', params],
    queryFn: () => backendAPI.getProgress(params),
    enabled: isAuthenticated,
    staleTime: 1000 * 60 * 2, // 2 minutes
    gcTime: 1000 * 60 * 10, // 10 minutes
  });

  // Mutation to update progress
  const updateMutation = useMutation({
    mutationFn: ({
      episodeId,
      titleId,
      positionSeconds,
      durationSeconds,
      provider = 'rpc',
    }: {
      episodeId: string;
      titleId: string;
      positionSeconds: number;
      durationSeconds: number;
      provider?: string;
    }) =>
      backendAPI.updateProgress(
        episodeId,
        {
          title_id: titleId,
          position_seconds: positionSeconds,
          duration_seconds: durationSeconds,
        },
        provider
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['progress'] });
      queryClient.invalidateQueries({ queryKey: ['history'] });
    },
  });

  // Unified save progress function that syncs to both local and server
  const saveProgress = useCallback(
    (
      animeId: string,
      episodeNumber: number,
      currentTime: number,
      duration: number,
      metadata?: { poster?: string; name?: string }
    ) => {
      // Always save to local storage
      localProgress.saveProgress(
        animeId,
        episodeNumber,
        currentTime,
        duration,
        metadata
      );

      // If authenticated, also save to server
      if (isAuthenticated) {
        const episodeId = `${animeId}-ep-${episodeNumber}`;
        updateMutation.mutate({
          episodeId,
          titleId: animeId,
          positionSeconds: currentTime,
          durationSeconds: duration,
        });
      }
    },
    [isAuthenticated, localProgress, updateMutation]
  );

  // Get progress for a specific episode (server or local)
  const getProgress = useCallback(
    (animeId: string, episodeNumber: number) => {
      if (isAuthenticated) {
        const episodeId = `${animeId}-ep-${episodeNumber}`;
        const serverProgress = items.find((p) => p.episode_id === episodeId);
        if (serverProgress) {
          return {
            animeId,
            episodeNumber,
            currentTime: serverProgress.position_seconds,
            duration: serverProgress.duration_seconds,
            updatedAt: new Date(serverProgress.updated_at).getTime(),
          };
        }
      }
      
      // Fall back to local progress
      return localProgress.getProgress(animeId, episodeNumber);
    },
    [isAuthenticated, items, localProgress]
  );

  return {
    items,
    isLoading,
    error,
    isAuthenticated,
    saveProgress,
    getProgress,
    isSyncing: updateMutation.isPending,
  };
}

/**
 * Hook for watch history.
 */
export function useHistory(params?: {
  provider?: string;
  limit?: number;
}) {
  const queryClient = useQueryClient();
  const isAuthenticated = backendAPI.isAuthenticated();

  const { data: items = [], isLoading, error } = useQuery({
    queryKey: ['history', params],
    queryFn: () => backendAPI.getHistory(params),
    enabled: isAuthenticated,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 30, // 30 minutes
  });

  // Mutation to delete a single history entry
  const deleteMutation = useMutation({
    mutationFn: (historyId: number) => backendAPI.deleteHistoryEntry(historyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['history'] });
    },
  });

  // Mutation to clear all history
  const clearMutation = useMutation({
    mutationFn: (provider: string = 'rpc') => backendAPI.clearHistory(provider),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['history'] });
    },
  });

  return {
    items,
    isLoading,
    error,
    isAuthenticated,
    deleteEntry: deleteMutation.mutate,
    clearAll: clearMutation.mutate,
    isDeleting: deleteMutation.isPending,
    isClearing: clearMutation.isPending,
  };
}
