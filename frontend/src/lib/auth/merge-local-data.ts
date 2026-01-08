/**
 * Merge local data (progress and library) with server data on login.
 * 
 * This utility handles the background sync process when a user logs in
 * with existing local data.
 * 
 * Strategy:
 * - Upload all local progress items to server
 * - Upload all local library items (saved series) to server
 * - Server wins on conflict (by updated_at timestamp)
 * - Non-blocking operation
 */

import { backendAPI } from "@/lib/api/backend";
import type { WatchProgress } from "@/hooks/use-watch-progress";
import type { SavedSeries } from "@/hooks/use-saved-series";

const STORAGE_KEY_PROGRESS = "anirohi-watch-progress";
const STORAGE_KEY_SAVED = "anirohi-saved-series";

interface MergeResult {
  success: boolean;
  progressCount: number;
  libraryCount: number;
  errors: string[];
}

/**
 * Get local progress data from localStorage
 */
function getLocalProgress(): WatchProgress[] {
  if (typeof window === "undefined") return [];
  try {
    const stored = localStorage.getItem(STORAGE_KEY_PROGRESS);
    if (!stored) return [];
    const data = JSON.parse(stored);
    return Object.values(data);
  } catch {
    return [];
  }
}

/**
 * Get local saved series from localStorage
 */
function getLocalSavedSeries(): SavedSeries[] {
  if (typeof window === "undefined") return [];
  try {
    const stored = localStorage.getItem(STORAGE_KEY_SAVED);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

/**
 * Merge local progress items to server
 */
async function mergeProgress(items: WatchProgress[]): Promise<{ success: number; errors: string[] }> {
  let success = 0;
  const errors: string[] = [];

  for (const item of items) {
    try {
      const episodeId = `${item.animeId}-ep-${item.episodeNumber}`;
      await backendAPI.updateProgress(
        episodeId,
        {
          title_id: item.animeId,
          position_seconds: item.currentTime,
          duration_seconds: item.duration,
        },
        "rpc"
      );
      success++;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      errors.push(`Failed to sync progress for ${item.animeId} EP${item.episodeNumber}: ${message}`);
    }
  }

  return { success, errors };
}

/**
 * Merge local library items (saved series) to server
 */
async function mergeLibrary(items: SavedSeries[]): Promise<{ success: number; errors: string[] }> {
  let success = 0;
  const errors: string[] = [];

  for (const item of items) {
    try {
      // Add to library with "planned" status by default
      await backendAPI.updateLibraryItem(
        item.id,
        { status: "planned", is_favorite: false },
        "rpc"
      );
      success++;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      errors.push(`Failed to sync library item ${item.name}: ${message}`);
    }
  }

  return { success, errors };
}

/**
 * Merge all local data to server
 * 
 * This is a non-blocking operation that runs in the background.
 * Errors are collected and returned, but don't prevent the merge from completing.
 */
export async function mergeLocalDataToServer(): Promise<MergeResult> {
  const localProgress = getLocalProgress();
  const localSaved = getLocalSavedSeries();

  const progressResult = await mergeProgress(localProgress);
  const libraryResult = await mergeLibrary(localSaved);

  const result: MergeResult = {
    success: progressResult.errors.length === 0 && libraryResult.errors.length === 0,
    progressCount: progressResult.success,
    libraryCount: libraryResult.success,
    errors: [...progressResult.errors, ...libraryResult.errors],
  };

  return result;
}

/**
 * Clear local data after successful merge (optional)
 * 
 * You may want to keep local data as a backup, or clear it to save space.
 */
export function clearLocalData(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_KEY_PROGRESS);
  localStorage.removeItem(STORAGE_KEY_SAVED);
}
