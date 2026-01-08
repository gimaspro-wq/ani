"use client";

import { useLibrary, useIsInLibrary } from "@/hooks/use-library";
import { toast } from "sonner";

interface FavoriteButtonProps {
  titleId: string;
  provider?: string;
}

export function FavoriteButton({
  titleId,
  provider = "rpc",
}: FavoriteButtonProps) {
  const { updateItem, isUpdating, isAuthenticated } = useLibrary();
  const { isFavorite, status } = useIsInLibrary(titleId, provider);

  const handleToggle = () => {
    if (!isAuthenticated) {
      toast.error("Please login to use this feature");
      return;
    }

    updateItem(
      {
        titleId,
        isFavorite: !isFavorite,
        status: status || "planned",
        provider,
      },
      {
        onSuccess: () => {
          toast.success(isFavorite ? "Removed from favorites" : "Added to favorites");
        },
        onError: () => {
          toast.error("Failed to update favorite");
        },
      }
    );
  };

  return (
    <button
      onClick={handleToggle}
      disabled={isUpdating}
      className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-foreground/10 text-sm font-medium hover:bg-foreground/20 transition-colors disabled:opacity-50"
      aria-label={isFavorite ? "Remove from favorites" : "Add to favorites"}
    >
      {isUpdating ? (
        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      ) : (
        <svg
          className={`w-4 h-4 transition-colors ${isFavorite ? "fill-red-500 text-red-500" : ""}`}
          fill={isFavorite ? "currentColor" : "none"}
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={isFavorite ? 0 : 2}
            d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
          />
        </svg>
      )}
      <span>{isFavorite ? "Favorite" : "Add to Favorites"}</span>
    </button>
  );
}
