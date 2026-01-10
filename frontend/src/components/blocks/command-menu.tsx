"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { useQuery } from "@tanstack/react-query";
import { Clock } from "lucide-react";
import { useDebounce } from "@/lib/hooks/use-debounce";
import { useSearchIndex } from "@/hooks/use-search-index";
import { orpc } from "@/lib/query/orpc";
import { useAuth } from "@/lib/auth/auth-context";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Spinner } from "@/components/ui/spinner";

const RECENT_SEARCHES_KEY = "recent-searches";
const MAX_RECENT_SEARCHES = 10;

type RecentSearch = {
  id: string;
  name: string;
  poster: string;
};

function loadRecentSearches(): RecentSearch[] {
  if (typeof window === "undefined") return [];
  try {
    const stored = localStorage.getItem(RECENT_SEARCHES_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (error) {
    console.error("Failed to load recent searches:", error);
  }
  return [];
}

export function CommandMenu() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [recentSearches, setRecentSearches] = useState<RecentSearch[]>(
    loadRecentSearches,
  );
  const debouncedQuery = useDebounce(query, 200);
  const router = useRouter();

  const { search, isReady, isBuilding } = useSearchIndex();
  const { isAuthenticated } = useAuth();
  const queryEnabled = isAuthenticated;

  // Use index search if ready, otherwise fall back to API
  const indexResults =
    isReady && debouncedQuery.length >= 2
      ? search(debouncedQuery, 10)
          .filter((anime): anime is typeof anime & { poster: string } => 
            anime.poster !== null
          )
      : null;

  // Fallback to API search if index not ready
  const { data: apiSearchData, isLoading: isApiLoading } = useQuery({
    ...orpc.anime.search.queryOptions({
      input: { query: debouncedQuery, page: 1 },
    }),
    enabled: queryEnabled && !isReady && debouncedQuery.length >= 2,
  });

  const apiResults = (apiSearchData?.animes ?? []).filter(
    (
      item,
    ): item is typeof item & { id: string; name: string; poster: string } =>
      item.id !== null && item.name !== null && item.poster !== null,
  );

  const searchResults = indexResults || apiResults;
  const isSearching = (queryEnabled && !isReady && isApiLoading) || isBuilding;

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const saveRecentSearch = useCallback((anime: RecentSearch) => {
    if (typeof window === "undefined") return;

    try {
      const stored = localStorage.getItem(RECENT_SEARCHES_KEY);
      const recent: RecentSearch[] = stored ? JSON.parse(stored) : [];

      // Remove if already exists
      const filtered = recent.filter((item) => item.id !== anime.id);

      // Add to front and limit to max
      const updated = [anime, ...filtered].slice(0, MAX_RECENT_SEARCHES);

      localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(updated));
      setRecentSearches(updated);
    } catch (error) {
      console.error("Failed to save recent search:", error);
    }
  }, []);

  const clearRecentSearches = useCallback(() => {
    if (typeof window === "undefined") return;
    localStorage.removeItem(RECENT_SEARCHES_KEY);
    setRecentSearches([]);
  }, []);

  const handleSelect = useCallback(
    (anime: { id: string; name: string; poster: string }) => {
      saveRecentSearch(anime);
      setOpen(false);
      setQuery("");
      router.push(`/anime/${anime.id}`);
    },
    [router, saveRecentSearch],
  );

  return (
    <CommandDialog
      open={open}
      onOpenChange={setOpen}
      title="Search Anime"
      description="Search for your favorite anime"
      showCloseButton={false}
    >
      <CommandInput
        placeholder="Search anime..."
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        {debouncedQuery.length < 2 ? (
          <>
            {recentSearches.length > 0 && (
              <CommandGroup
                heading={
                  <div className="flex items-center justify-between">
                    <span>Recent Searches</span>
                    <button
                      onClick={clearRecentSearches}
                      className="text-xs text-muted-foreground hover:text-foreground"
                    >
                      Clear
                    </button>
                  </div>
                }
              >
                {recentSearches.map((anime) => (
                  <CommandItem
                    key={anime.id}
                    value={anime.name}
                    onSelect={() => handleSelect(anime)}
                    className="gap-3 py-3 border border-transparent transition-colors data-[selected=true]:bg-card data-[selected=true]:border-input data-[selected=true]:text-card-foreground"
                  >
                    <Clock className="size-4 text-muted-foreground shrink-0" />
                    <div className="relative h-12 w-9 overflow-hidden rounded bg-muted shrink-0">
                      <Image
                        src={anime.poster}
                        alt={anime.name}
                        fill
                        className="object-cover"
                      />
                    </div>
                    <div className="flex flex-col gap-0.5 min-w-0">
                      <span className="font-medium truncate">{anime.name}</span>
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}
            {recentSearches.length === 0 && (
              <div className="py-6 text-center text-sm text-muted-foreground">
                Type to search...
              </div>
            )}
          </>
        ) : isSearching ? (
          <div className="flex items-center justify-center py-6">
            <Spinner className="size-5 text-muted-foreground" />
          </div>
        ) : searchResults.length === 0 ? (
          <CommandEmpty>No results found.</CommandEmpty>
        ) : (
          <CommandGroup heading="Results">
            {searchResults.map((anime) => (
              <CommandItem
                key={anime.id}
                value={anime.name}
                onSelect={() => handleSelect(anime)}
                className="gap-3 py-3 border border-transparent transition-colors data-[selected=true]:bg-card data-[selected=true]:border-input data-[selected=true]:text-card-foreground"
              >
                <div className="relative h-12 w-9 overflow-hidden rounded bg-muted shrink-0">
                  <Image
                    src={anime.poster}
                    alt={anime.name}
                    fill
                    className="object-cover"
                  />
                </div>
                <div className="flex flex-col gap-0.5 min-w-0">
                  <span className="font-medium truncate">{anime.name}</span>
                  <span className="text-xs text-muted-foreground">
                    {anime.type} ·{" "}
                    {anime.episodes?.sub ?? anime.episodes?.dub ?? "?"} ep
                  </span>
                </div>
              </CommandItem>
            ))}
          </CommandGroup>
        )}
      </CommandList>
    </CommandDialog>
  );
}
