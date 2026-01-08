"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import Image from "next/image";
import { parseAsStringLiteral, useQueryState } from "nuqs";
import { useLibrary } from "@/hooks/use-library";
import type { LibraryStatus } from "@/lib/api/backend";
import { Navbar } from "@/components/blocks/navbar";
import { Footer } from "@/components/blocks/footer";
import { Spinner } from "@/components/ui/spinner";
import { QuickActions } from "@/components/anime/quick-actions";

const STATUS_TABS: Array<{ value: LibraryStatus | "all"; label: string }> = [
  { value: "all", label: "All" },
  { value: "watching", label: "Watching" },
  { value: "planned", label: "Plan to Watch" },
  { value: "completed", label: "Completed" },
  { value: "dropped", label: "Dropped" },
];

function LibraryContent() {
  const [status, setStatus] = useQueryState(
    "status",
    parseAsStringLiteral(["all", "watching", "planned", "completed", "dropped"] as const).withDefault("all")
  );
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);

  const { items, isLoading, isAuthenticated } = useLibrary({
    status: status !== "all" ? status : undefined,
    favorites: showFavoritesOnly || undefined,
  });

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="flex flex-col items-center justify-center min-h-[60vh] px-4">
          <svg
            className="w-16 h-16 text-muted-foreground/30 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
            />
          </svg>
          <h1 className="text-2xl font-heading text-foreground mb-2">
            Login Required
          </h1>
          <p className="text-muted-foreground text-center mb-6">
            Please login to access your library
          </p>
          <Link
            href={`/login?returnTo=${encodeURIComponent("/library")}`}
            className="px-6 py-3 rounded-lg bg-foreground text-background text-sm font-medium hover:bg-foreground/90 transition-colors"
          >
            Login
          </Link>
        </div>
        <Footer />
      </div>
    );
  }

  const filteredItems = items;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <div className="pt-20 pb-10 px-4">
        <div className="mx-auto max-w-7xl">
          <div className="mb-8">
            <h1 className="text-3xl font-heading text-foreground mb-2">
              My Library
            </h1>
            <p className="text-muted-foreground">
              Manage and track your anime collection
            </p>
          </div>

          {/* Tabs and Filters */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
            <div className="flex items-center gap-2 overflow-x-auto">
              {STATUS_TABS.map((tab) => (
                <button
                  key={tab.value}
                  onClick={() => setStatus(tab.value)}
                  className={`
                    px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors
                    ${
                      status === tab.value
                        ? "bg-foreground text-background"
                        : "bg-foreground/5 text-muted-foreground hover:bg-foreground/10"
                    }
                  `}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showFavoritesOnly}
                onChange={(e) => setShowFavoritesOnly(e.target.checked)}
                className="w-4 h-4 rounded border-border text-foreground focus:ring-2 focus:ring-foreground/20"
              />
              <span className="text-sm text-muted-foreground">
                Favorites only
              </span>
            </label>
          </div>

          {/* Content */}
          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Spinner className="size-8 text-muted-foreground" />
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <svg
                className="w-16 h-16 text-muted-foreground/30 mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                />
              </svg>
              <h2 className="text-xl font-medium text-foreground mb-2">
                No anime in your library
              </h2>
              <p className="text-muted-foreground mb-6">
                {showFavoritesOnly
                  ? "You haven't favorited any anime yet"
                  : status !== "all"
                    ? `No anime with status "${status}"`
                    : "Start adding anime to your library"}
              </p>
              <Link
                href="/browse"
                className="px-6 py-3 rounded-lg bg-foreground text-background text-sm font-medium hover:bg-foreground/90 transition-colors"
              >
                Browse Anime
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
              {filteredItems.map((item) => (
                <div key={item.id} className="group relative">
                  <Link
                    href={`/anime/${item.title_id}`}
                    className="block"
                  >
                    <div className="relative aspect-3/4 rounded-lg overflow-hidden bg-foreground/5">
                      {/* Placeholder for poster - would need to fetch from RPC */}
                      <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                        <svg
                          className="w-12 h-12 opacity-30"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
                        </svg>
                      </div>

                      {/* Status badge */}
                      <div className="absolute top-2 left-2 px-2 py-1 rounded text-xs font-medium bg-black/70 text-white capitalize">
                        {item.status}
                      </div>

                      {/* Favorite indicator */}
                      {item.is_favorite && (
                        <div className="absolute top-2 right-2 p-1.5 rounded bg-black/70">
                          <svg
                            className="w-4 h-4 fill-red-500 text-red-500"
                            viewBox="0 0 24 24"
                          >
                            <path d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                          </svg>
                        </div>
                      )}
                    </div>
                    <h3 className="mt-2 text-sm text-muted-foreground line-clamp-2 group-hover:text-foreground transition-colors">
                      {item.title_id}
                    </h3>
                  </Link>
                  {/* Quick Actions - appears on hover */}
                  <div className="mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <QuickActions titleId={item.title_id} provider={item.provider} variant="compact" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <Footer />
    </div>
  );
}

export default function LibraryPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="flex items-center justify-center min-h-[60vh]">
          <Spinner className="size-8 text-muted-foreground" />
        </div>
        <Footer />
      </div>
    }>
      <LibraryContent />
    </Suspense>
  );
}
