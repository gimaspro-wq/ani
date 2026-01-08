"use client";

import { Button } from "@/components/ui/button";
import { useLibrary } from "@/hooks/use-library";
import { backendAPI, type LibraryStatus } from "@/lib/api/backend";
import { toast } from "sonner";
import { Heart, Star, Trash2, MoreVertical } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface QuickActionsProps {
  titleId: string;
  provider?: string;
  showLabels?: boolean;
  variant?: "default" | "compact";
}

export function QuickActions({
  titleId,
  provider = "rpc",
  showLabels = false,
  variant = "default",
}: QuickActionsProps) {
  const isAuthenticated = backendAPI.isAuthenticated();
  const { items, updateItem, deleteItem, isUpdating, isDeleting } = useLibrary({ provider });

  // Find the current library item for this title
  const libraryItem = items.find((item) => item.title_id === titleId);
  const isFavorite = libraryItem?.is_favorite || false;
  const currentStatus = libraryItem?.status;

  const handleToggleFavorite = () => {
    if (!isAuthenticated) {
      toast.error("Sign in to manage your library");
      return;
    }

    updateItem(
      {
        titleId,
        isFavorite: !isFavorite,
        status: currentStatus,
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

  const handleUpdateStatus = (status: LibraryStatus) => {
    if (!isAuthenticated) {
      toast.error("Sign in to manage your library");
      return;
    }

    updateItem(
      {
        titleId,
        status,
        provider,
      },
      {
        onSuccess: () => {
          toast.success(`Status updated to ${status}`);
        },
        onError: () => {
          toast.error("Failed to update status");
        },
      }
    );
  };

  const handleRemoveFromLibrary = () => {
    if (!isAuthenticated) {
      toast.error("Sign in to manage your library");
      return;
    }

    deleteItem(
      { titleId, provider },
      {
        onSuccess: () => {
          toast.success("Removed from library");
        },
        onError: () => {
          toast.error("Failed to remove from library");
        },
      }
    );
  };

  if (!isAuthenticated) {
    return null;
  }

  if (variant === "compact") {
    return (
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          onClick={(e) => {
            e.preventDefault();
            handleToggleFavorite();
          }}
          disabled={isUpdating}
          className={isFavorite ? "text-red-500" : "text-muted-foreground"}
        >
          <Heart className={`w-4 h-4 ${isFavorite ? "fill-current" : ""}`} />
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              onClick={(e) => e.preventDefault()}
              disabled={isUpdating || isDeleting}
            >
              <MoreVertical className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => handleUpdateStatus("watching")}>
              Set as Watching
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleUpdateStatus("planned")}>
              Set as Planned
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleUpdateStatus("completed")}>
              Set as Completed
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleUpdateStatus("dropped")}>
              Set as Dropped
            </DropdownMenuItem>
            {libraryItem && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleRemoveFromLibrary} className="text-destructive">
                  <Trash2 className="w-4 h-4 mr-2" />
                  Remove from Library
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button
        variant={isFavorite ? "default" : "outline"}
        size={showLabels ? "sm" : "icon"}
        onClick={handleToggleFavorite}
        disabled={isUpdating}
        className={isFavorite ? "bg-red-500 hover:bg-red-600" : ""}
      >
        <Heart className={`w-4 h-4 ${showLabels ? "mr-2" : ""} ${isFavorite ? "fill-current" : ""}`} />
        {showLabels && (isFavorite ? "Favorited" : "Favorite")}
      </Button>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="outline"
            size={showLabels ? "sm" : "icon"}
            disabled={isUpdating || isDeleting}
          >
            <Star className={`w-4 h-4 ${showLabels ? "mr-2" : ""}`} />
            {showLabels && (currentStatus || "Add to List")}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={() => handleUpdateStatus("watching")}>
            Watching
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => handleUpdateStatus("planned")}>
            Planned
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => handleUpdateStatus("completed")}>
            Completed
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => handleUpdateStatus("dropped")}>
            Dropped
          </DropdownMenuItem>
          {libraryItem && (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={handleRemoveFromLibrary}
                className="text-destructive"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Remove from Library
              </DropdownMenuItem>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
