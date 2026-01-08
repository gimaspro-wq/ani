"use client";

import Image from "next/image";
import Link from "next/link";
import { Navbar } from "@/components/blocks/navbar";
import { Footer } from "@/components/blocks/footer";
import { useLibrary } from "@/hooks/use-library";
import { backendAPI } from "@/lib/api/backend";
import { Spinner } from "@/components/ui/spinner";
import { toast } from "sonner";

export default function SavedPage() {
  const isAuthenticated = backendAPI.isAuthenticated();
  const { items: favorites, isLoading, updateItem } = useLibrary({ favorites: true });

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
            Please login to access your favorites
          </p>
          <Link
            href={`/login?returnTo=${encodeURIComponent("/saved")}`}
            className="px-6 py-3 rounded-lg bg-foreground text-background text-sm font-medium hover:bg-foreground/90 transition-colors"
          >
            Login
          </Link>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <main className="pt-20 pb-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h1 className="font-heading text-3xl md:text-4xl text-foreground mb-2">
            Favorites
          </h1>
          <p className="text-muted-foreground mb-8">
            {isLoading ? "Loading..." : `${favorites.length} ${favorites.length === 1 ? "favorite" : "favorites"}`}
          </p>

          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Spinner className="size-8 text-muted-foreground" />
            </div>
          ) : favorites.length === 0 ? (
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
                  d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                />
              </svg>
              <h2 className="text-lg font-medium text-foreground mb-2">
                No favorites yet
              </h2>
              <p className="text-muted-foreground mb-6 max-w-sm">
                Browse anime and mark them as favorites to see them here
              </p>
              <Link
                href="/browse"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-foreground text-background text-sm font-medium hover:bg-foreground/90 transition-colors"
              >
                Browse Anime
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
              {favorites.map((item) => (
                <div key={item.id} className="group relative">
                  <Link href={`/anime/${item.title_id}`} className="block">
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
                      <div className="absolute top-2 right-2 p-1.5 rounded bg-black/70">
                        <svg
                          className="w-4 h-4 fill-red-500 text-red-500"
                          viewBox="0 0 24 24"
                        >
                          <path d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                        </svg>
                      </div>
                    </div>
                    <h3 className="mt-2 text-sm text-muted-foreground line-clamp-2 group-hover:text-foreground transition-colors">
                      {item.title_id}
                    </h3>
                  </Link>
                  <button
                    onClick={() => {
                      updateItem(
                        {
                          titleId: item.title_id,
                          isFavorite: false,
                          status: item.status,
                          provider: item.provider,
                        },
                        {
                          onSuccess: () => {
                            toast("Removed from favorites");
                          },
                        }
                      );
                    }}
                    className="absolute top-2 right-2 p-1.5 rounded-md bg-background/80 backdrop-blur-sm opacity-0 group-hover:opacity-100 hover:bg-background transition-all z-10"
                    aria-label="Remove from favorites"
                  >
                    <svg
                      className="w-4 h-4 text-foreground"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
