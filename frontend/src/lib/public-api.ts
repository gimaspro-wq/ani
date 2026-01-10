import type { AnimeDetail, AnimeListItem, Episode } from "@/lib/types";
const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL;
const READ_API_BASE = "/api/read/anime";
const LEGACY_EPISODES_BASE = "/api/v1/anime";

function buildUrl(path: string): string {
  if (path.startsWith("http")) {
    return path;
  }

  if (typeof window !== "undefined") {
    return path;
  }

  if (!API_BASE) {
    return path;
  }

  return `${API_BASE}${path}`;
}

async function fetchJson<T>(path: string): Promise<T | null> {
  const isServer = typeof window === "undefined";

  if (isServer && !API_BASE) {
    return null;
  }

  const url = buildUrl(path);

  try {
    const response = await fetch(url, {
      next: { revalidate: 60 },
    });

    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      if (!isServer) {
        console.error(`Public API error for ${path}: ${response.status}`);
      }
      return null;
    }

    return (await response.json()) as T;
  } catch (error) {
    if (!isServer) {
      console.error(`Failed to fetch ${path}`, error);
    }
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
