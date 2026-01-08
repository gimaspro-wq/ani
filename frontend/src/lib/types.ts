export type AnimeStatus = "ongoing" | "completed" | "upcoming" | string;

export interface AnimeListItem {
  id: string;
  title: string;
  slug: string;
  description?: string | null;
  year?: number | null;
  status?: AnimeStatus | null;
  poster?: string | null;
  genres?: string[];
  created_at?: string;
}

export interface AnimeDetail extends AnimeListItem {
  alternative_titles?: string[];
  updated_at?: string | null;
}

export type VideoSourceType = "iframe" | "embed" | "m3u8" | "mp4";

export interface VideoSource {
  id: string;
  type: VideoSourceType;
  url: string;
  source_name: string;
  priority: number;
}

export interface Episode {
  id: string;
  number: number;
  title: string | null;
  video_sources: VideoSource[];
}
