"use client";

import { useEffect, useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { getSearchIndex, type AnimeIndexItem } from "@/lib/search/index";
import { orpc } from "@/lib/query/orpc";
import { useAuth } from "@/lib/auth/auth-context";

export function useSearchIndex() {
  const [isIndexReady, setIsIndexReady] = useState(false);
  const [isBuilding, setIsBuilding] = useState(false);
  const searchIndex = getSearchIndex();
  const { isAuthenticated } = useAuth();
  const queryEnabled = isAuthenticated;

  // Fetch popular anime to build index
  const { data: popularData } = useQuery({
    ...orpc.anime.getCategoryAnime.queryOptions({
      input: { category: "most-popular", page: 1 },
    }),
    staleTime: 15 * 60 * 1000, // 15 minutes
    enabled: queryEnabled,
  });

  const { data: recentData } = useQuery({
    ...orpc.anime.getCategoryAnime.queryOptions({
      input: { category: "recently-updated", page: 1 },
    }),
    staleTime: 15 * 60 * 1000,
    enabled: queryEnabled,
  });

  const { data: airingData } = useQuery({
    ...orpc.anime.getCategoryAnime.queryOptions({
      input: { category: "top-airing", page: 1 },
    }),
    staleTime: 15 * 60 * 1000,
    enabled: queryEnabled,
  });

  // Load or build index
  useEffect(() => {
    let mounted = true;

    async function initializeIndex() {
      if (!queryEnabled) {
        setIsIndexReady(false);
        setIsBuilding(false);
        return;
      }

      try {
        // Try to load existing index
        const loaded = await searchIndex.load();
        if (loaded && mounted) {
          setIsIndexReady(true);
          return;
        }

        // Build new index if we have data
        if (popularData?.animes || recentData?.animes || airingData?.animes) {
          setIsBuilding(true);

          // Combine all anime data
          const allAnime: AnimeIndexItem[] = [];
          const seenIds = new Set<string>();

          type AnimeArray = NonNullable<typeof popularData>["animes"];

          const addAnime = (animes?: AnimeArray) => {
            animes?.forEach((anime) => {
              if (
                anime.id &&
                anime.name &&
                !seenIds.has(anime.id) &&
                anime.poster
              ) {
                seenIds.add(anime.id);
                allAnime.push({
                  id: anime.id,
                  name: anime.name,
                  jname: anime.jname ?? null,
                  type: anime.type ?? null,
                  poster: anime.poster,
                  episodes: anime.episodes ?? { sub: null, dub: null },
                  rating: anime.rating ?? null,
                  duration: anime.duration ?? null,
                });
              }
            });
          };

          addAnime(popularData?.animes);
          addAnime(recentData?.animes);
          addAnime(airingData?.animes);

          if (allAnime.length > 0 && mounted) {
            await searchIndex.build(allAnime);
            if (mounted) {
              setIsIndexReady(true);
              setIsBuilding(false);
            }
          }
        }
      } catch (error) {
        console.error("Failed to initialize search index:", error);
        if (mounted) {
          setIsBuilding(false);
        }
      }
    }

    initializeIndex();

    return () => {
      mounted = false;
    };
  }, [popularData, recentData, airingData, searchIndex, queryEnabled]);

  const search = useCallback(
    (query: string, limit?: number) => {
      if (!isIndexReady) return [];
      return searchIndex.search(query, limit);
    },
    [isIndexReady, searchIndex],
  );

  const clearIndex = useCallback(async () => {
    await searchIndex.clear();
    setIsIndexReady(false);
  }, [searchIndex]);

  return {
    search,
    isReady: isIndexReady,
    isBuilding,
    documentCount: searchIndex.getDocumentCount(),
    clearIndex,
  };
}
