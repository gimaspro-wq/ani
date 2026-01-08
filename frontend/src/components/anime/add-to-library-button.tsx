"use client";

import { useState } from "react";
import { useLibrary, useIsInLibrary } from "@/hooks/use-library";
import type { LibraryStatus } from "@/lib/api/backend";
import { toast } from "sonner";

interface AddToLibraryButtonProps {
  titleId: string;
  titleName: string;
  provider?: string;
}

const STATUS_OPTIONS: { value: LibraryStatus; label: string }[] = [
  { value: "watching", label: "Watching" },
  { value: "planned", label: "Plan to Watch" },
  { value: "completed", label: "Completed" },
  { value: "dropped", label: "Dropped" },
];

export function AddToLibraryButton({
  titleId,
  titleName,
  provider = "rpc",
}: AddToLibraryButtonProps) {
  const { updateItem, deleteItem, isUpdating, isDeleting, isAuthenticated } =
    useLibrary();
  const { isInLibrary, status } = useIsInLibrary(titleId, provider);
  const [isOpen, setIsOpen] = useState(false);

  const handleStatusChange = (newStatus: LibraryStatus) => {
    if (!isAuthenticated) {
      toast.error("Please login to use this feature");
      return;
    }

    updateItem(
      { titleId, status: newStatus, provider },
      {
        onSuccess: () => {
          toast.success(`Added to ${newStatus}`);
          setIsOpen(false);
        },
        onError: () => {
          toast.error("Failed to update library");
        },
      }
    );
  };

  const handleRemove = () => {
    if (!isAuthenticated) {
      return;
    }

    deleteItem(
      { titleId, provider },
      {
        onSuccess: () => {
          toast.success("Removed from library");
          setIsOpen(false);
        },
        onError: () => {
          toast.error("Failed to remove from library");
        },
      }
    );
  };

  const currentStatusLabel =
    STATUS_OPTIONS.find((opt) => opt.value === status)?.label || "Add to Library";

  const isLoading = isUpdating || isDeleting;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-foreground/10 text-sm font-medium hover:bg-foreground/20 transition-colors disabled:opacity-50"
      >
        {isLoading ? (
          <>
            <svg
              className="w-4 h-4 animate-spin"
              fill="none"
              viewBox="0 0 24 24"
            >
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
            <span>Updating...</span>
          </>
        ) : (
          <>
            {isInLibrary ? (
              <svg
                className="w-4 h-4"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            ) : (
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
            )}
            <span>{currentStatusLabel}</span>
            <svg
              className={`w-4 h-4 transition-transform ${isOpen ? "rotate-180" : ""}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </>
        )}
      </button>

      {/* Dropdown menu */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full mt-2 left-0 z-50 w-48 rounded-lg bg-card border border-border shadow-xl overflow-hidden">
            {STATUS_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => handleStatusChange(option.value)}
                disabled={isLoading}
                className={`w-full text-left px-4 py-2.5 text-sm transition-colors ${
                  status === option.value
                    ? "bg-foreground/10 text-foreground"
                    : "text-muted-foreground hover:bg-foreground/5 hover:text-foreground"
                }`}
              >
                {option.label}
              </button>
            ))}
            {isInLibrary && (
              <>
                <div className="h-px bg-border" />
                <button
                  onClick={handleRemove}
                  disabled={isLoading}
                  className="w-full text-left px-4 py-2.5 text-sm text-red-500 hover:bg-red-500/10 transition-colors"
                >
                  Remove from Library
                </button>
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}
