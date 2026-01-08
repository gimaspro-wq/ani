"use client";

import { useState, useEffect, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { backendAPI } from "@/lib/api/backend";
import { toast } from "sonner";

const STORAGE_KEY_PROGRESS = "anirohi-watch-progress";
const STORAGE_KEY_SAVED = "anirohi-saved-series";
const IMPORT_COMPLETED_KEY = "anirohi-import-completed";

/**
 * Get local progress data from localStorage
 */
function getLocalProgress() {
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
function getLocalSavedSeries() {
  if (typeof window === "undefined") return [];
  try {
    const stored = localStorage.getItem(STORAGE_KEY_SAVED);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

/**
 * Clear local user data after successful import
 */
function clearLocalData() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_KEY_PROGRESS);
  localStorage.removeItem(STORAGE_KEY_SAVED);
  localStorage.setItem(IMPORT_COMPLETED_KEY, "true");
}

/**
 * Check if import has already been completed
 */
function isImportCompleted() {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(IMPORT_COMPLETED_KEY) === "true";
}

/**
 * Hook to handle login merge flow.
 * 
 * Usage:
 * 
 * ```tsx
 * const { triggerMerge, isMerging } = useLoginMerge();
 * 
 * // After successful login
 * await backendAPI.login(email, password);
 * triggerMerge();
 * ```
 */
export function useLoginMerge() {
  const queryClient = useQueryClient();
  const [isMerging, setIsMerging] = useState(false);
  const [hasLocalData, setHasLocalData] = useState(false);

  // Check if there's local data on mount
  useEffect(() => {
    if (typeof window === "undefined") return;
    
    const progress = localStorage.getItem(STORAGE_KEY_PROGRESS);
    const saved = localStorage.getItem(STORAGE_KEY_SAVED);
    
    setHasLocalData(!!(progress || saved));
  }, []);

  const triggerMerge = useCallback(async () => {
    if (!backendAPI.isAuthenticated()) {
      console.warn("Cannot merge: user not authenticated");
      return;
    }

    // Skip if import already completed
    if (isImportCompleted()) {
      console.log("Import already completed, skipping");
      return;
    }

    if (!hasLocalData) {
      console.log("No local data to merge");
      return;
    }

    setIsMerging(true);
    toast.loading("Syncing your data...", { id: "merge-toast" });

    try {
      const localProgress = getLocalProgress();
      const localSaved = getLocalSavedSeries();

      const result = await backendAPI.importLegacyData({
        progress: localProgress,
        savedSeries: localSaved,
        provider: "rpc",
      });

      if (result.success) {
        const totalImported = result.progress_imported + result.library_imported;
        const totalSkipped = result.progress_skipped + result.library_skipped;
        
        // Clear local data after successful import
        clearLocalData();
        
        toast.success(
          `Synced ${totalImported} items${totalSkipped > 0 ? ` (${totalSkipped} already up-to-date)` : ""}`,
          { id: "merge-toast" }
        );
      } else {
        toast.error("Failed to sync your data.", {
          id: "merge-toast",
          action: {
            label: "Retry",
            onClick: () => triggerMerge(),
          },
        });
      }

      // Invalidate queries to refresh UI with merged data
      queryClient.invalidateQueries({ queryKey: ["library"] });
      queryClient.invalidateQueries({ queryKey: ["progress"] });
      queryClient.invalidateQueries({ queryKey: ["history"] });
    } catch (error) {
      console.error("Merge failed:", error);
      toast.error("Failed to sync your data.", {
        id: "merge-toast",
        action: {
          label: "Retry",
          onClick: () => triggerMerge(),
        },
      });
    } finally {
      setIsMerging(false);
    }
  }, [hasLocalData, queryClient]);

  return {
    triggerMerge,
    isMerging,
    hasLocalData: hasLocalData && !isImportCompleted(),
  };
}
