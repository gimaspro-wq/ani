"use client";

import { useState, useEffect, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { mergeLocalDataToServer } from "@/lib/auth/merge-local-data";
import { backendAPI } from "@/lib/api/backend";
import { toast } from "sonner";

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
    
    const progress = localStorage.getItem("anirohi-watch-progress");
    const saved = localStorage.getItem("anirohi-saved-series");
    
    setHasLocalData(!!(progress || saved));
  }, []);

  const triggerMerge = useCallback(async () => {
    if (!backendAPI.isAuthenticated()) {
      console.warn("Cannot merge: user not authenticated");
      return;
    }

    if (!hasLocalData) {
      console.log("No local data to merge");
      return;
    }

    setIsMerging(true);
    toast.loading("Syncing your data...", { id: "merge-toast" });

    try {
      const result = await mergeLocalDataToServer();

      if (result.success) {
        toast.success(
          `Synced ${result.progressCount} progress items and ${result.libraryCount} library items`,
          { id: "merge-toast" }
        );
      } else {
        toast.error(
          `Sync completed with errors. ${result.progressCount} progress and ${result.libraryCount} library items synced.`,
          { 
            id: "merge-toast",
            action: {
              label: "Retry",
              onClick: () => triggerMerge(),
            },
          }
        );
        console.error("Merge errors:", result.errors);
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
    hasLocalData,
  };
}
