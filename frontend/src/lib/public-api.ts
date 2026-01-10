import type { AnimeDetail, AnimeListItem, Episode } from "@/lib/types";
import { getServerBaseUrl } from "@/lib/server-base-url";

const READ_API_BASE = "/api/read/anime";
const LEGACY_EPISODES_BASE = "/api/v1/anime";

function buildUrl(path: string): string {
  // If URL is already absolute, use as-is
  if (path.startsWith("http")) {
    return path;
  }

  // Client-side: use relative URL
  if (typeof window !== "undefined") {
    return path;
  }

  // Server-side: prefix with backend base URL
  const baseUrl = getServerBaseUrl();
  return `${baseUrl}${path}`;
}

async function fetchJson<T>(path: string): Promise<T | null> {
  const url = buildUrl(path);

  try {
    const response = await fetch(url, {
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
  const data = await fetchJson<AnimeListItem[]>(`${READ_API_BASE}`);
  return Array.isArray(data) ? data : [];
}

export async function getAnimeBySlug(slug: string): Promise<AnimeDetail | null> {
  if (!slug) return null;
  return fetchJson<AnimeDetail>(`${READ_API_BASE}/${encodeURIComponent(slug)}`);
}

export async function getEpisodesBySlug(slug: string): Promise<Episode[]> {
  if (!slug) return [];
  const data = await fetchJson<Episode[]>(
    `${LEGACY_EPISODES_BASE}/${encodeURIComponent(slug)}/episodes`,
  );
  return Array.isArray(data) ? data : [];
}
