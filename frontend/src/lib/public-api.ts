import type { AnimeDetail, AnimeListItem, Episode } from "@/lib/types";

const API_BASE = "/api/v1/anime";

async function fetchJson<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(path, {
      next: { revalidate: 60 },
    });

    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      console.error(`Public API error for ${path}: ${response.status}`);
      return null;
    }

    return (await response.json()) as T;
  } catch (error) {
    console.error(`Failed to fetch ${path}`, error);
    return null;
  }
}

export async function getAnimeList(): Promise<AnimeListItem[]> {
  const data = await fetchJson<AnimeListItem[]>(`${API_BASE}`);
  return Array.isArray(data) ? data : [];
}

export async function getAnimeBySlug(slug: string): Promise<AnimeDetail | null> {
  if (!slug) return null;
  return fetchJson<AnimeDetail>(`${API_BASE}/${encodeURIComponent(slug)}`);
}

export async function getEpisodesBySlug(slug: string): Promise<Episode[]> {
  if (!slug) return [];
  const data = await fetchJson<Episode[]>(`${API_BASE}/${encodeURIComponent(slug)}/episodes`);
  return Array.isArray(data) ? data : [];
}
