"use client";

import type { Metadata } from "next";
import { useEffect, useMemo, useRef, useState } from "react";
import Hls, { Level } from "hls.js";
import { useSearchParams } from "next/navigation";

type EpisodeSource = {
  id: string;
  url: string;
  priority: number;
  is_active?: boolean;
};

type EpisodeItem = {
  id: string;
  number: number;
  title: string | null;
  video_sources: EpisodeSource[];
};

const SAMPLE_EPISODE = {
  title: "Sample Episode 1",
  streamUrl: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
};

export const metadata: Metadata = {
  title: "HLS плеер",
  description: "Воспроизведение серий с существующих READ эндпоинтов в формате HLS.",
  alternates: { canonical: "/player" },
};

export default function PlayerPage() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const hlsRef = useRef<Hls | null>(null);
  const [levels, setLevels] = useState<Level[]>([]);
  const [currentLevel, setCurrentLevel] = useState<number>(-1);
  const searchParams = useSearchParams();
  const slug = useMemo(() => searchParams.get("slug")?.trim(), [searchParams]);
  const [episodes, setEpisodes] = useState<EpisodeItem[]>([]);
  const [selectedEpisode, setSelectedEpisode] = useState<EpisodeItem | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [isSwitching, setIsSwitching] = useState(false);

  const destroyHls = () => {
    hlsRef.current?.destroy();
    hlsRef.current = null;
  };

  const loadStream = (url: string) => {
    const video = videoRef.current;
    if (!video) return;

    destroyHls();

    if (Hls.isSupported()) {
      const hls = new Hls();
      hlsRef.current = hls;

      hls.on(Hls.Events.MANIFEST_PARSED, (_, data) => {
        setLevels(data.levels);
        setCurrentLevel(hls.currentLevel);
      });

      hls.on(Hls.Events.LEVEL_SWITCHED, (_, data) => {
        setCurrentLevel(data.level);
      });

      hls.loadSource(url);
      hls.attachMedia(video);
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = url;
    }
  };

  useEffect(() => {
    if (!slug) {
      setStatusMessage("Add ?slug={anime-slug} to load episodes.");
      loadStream(SAMPLE_EPISODE.streamUrl);
      return;
    }

    const fetchEpisodes = async () => {
      setStatusMessage("Loading episodes…");
      try {
        const res = await fetch(`/api/v1/anime/${encodeURIComponent(slug)}/episodes`);
        if (!res.ok) {
          setStatusMessage("Failed to load episodes.");
          return;
        }
        const data = (await res.json()) as EpisodeItem[];
        setEpisodes(data);
        if (data.length === 0) {
          setStatusMessage("No episodes available.");
          return;
        }
        selectEpisode(data[0]);
      } catch (err) {
        console.error(err);
        setStatusMessage("Failed to load episodes.");
      }
    };

    fetchEpisodes();

    return () => {
      destroyHls();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug]);

  const selectEpisode = (episode: EpisodeItem) => {
    setIsSwitching(true);
    setSelectedEpisode(episode);
    setLevels([]);
    setCurrentLevel(-1);

    const activeSources = episode.video_sources
      .filter((vs) => vs.is_active !== false)
      .sort((a, b) => a.priority - b.priority);

    const source = activeSources[0];

    if (!source) {
      setStatusMessage("No active video sources for this episode.");
      destroyHls();
      setIsSwitching(false);
      return;
    }

    setStatusMessage(null);
    loadStream(source.url);
    setIsSwitching(false);
  };

  const handleQualityChange = (levelIndex: number) => {
    if (hlsRef.current) {
      hlsRef.current.currentLevel = levelIndex;
    }
  };

  const handleSkipOpening = () => {
    const video = videoRef.current;
    if (video) {
      video.currentTime = Math.max(0, video.currentTime + 90);
    }
  };

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleEnded = () => {
      if (isSwitching) return;
      const currentIndex = episodes.findIndex((ep) => ep.id === selectedEpisode?.id);
      if (currentIndex === -1) return;
      const next = episodes[currentIndex + 1];
      if (next) {
        selectEpisode(next);
      }
    };

    video.addEventListener("ended", handleEnded);

    return () => {
      video.removeEventListener("ended", handleEnded);
    };
  }, [episodes, selectedEpisode, isSwitching]);

  return (
    <main className="min-h-screen bg-black text-white flex flex-col items-center gap-4 py-8 px-4">
      <div className="w-full max-w-5xl flex flex-col gap-3">
        <div>
          <p className="text-sm text-gray-400 uppercase tracking-wide">Episode</p>
          <h1 className="text-2xl font-semibold">
            {selectedEpisode ? `Episode ${selectedEpisode.number}` : SAMPLE_EPISODE.title}
          </h1>
        </div>

        <div className="relative w-full aspect-video bg-neutral-900 rounded-lg overflow-hidden">
          <video
            ref={videoRef}
            className="w-full h-full"
            controls
            playsInline
            preload="auto"
            data-testid="hls-player"
          />
        </div>

        {statusMessage && (
          <div
            className="text-sm text-amber-300 bg-amber-900/30 border border-amber-700 rounded px-3 py-2"
            role="status"
            aria-live="polite"
          >
            {statusMessage}
          </div>
        )}

          {levels.length > 0 && (
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-300">Quality</span>
            <select
              value={currentLevel}
              onChange={(e) => handleQualityChange(Number(e.target.value))}
              className="bg-neutral-800 border border-neutral-700 rounded px-3 py-2 text-sm"
            >
              <option value={-1}>Auto</option>
              {levels.map((level, index) => (
                <option key={index} value={index}>
                  {level.height ? `${level.height}p` : `Level ${index + 1}`}
                </option>
              ))}
            </select>
            </div>
          )}

          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleSkipOpening}
              className="px-3 py-2 bg-neutral-800 border border-neutral-700 rounded text-sm hover:border-blue-400"
            >
              Skip opening (+90s)
            </button>
          </div>

          {episodes.length > 0 && (
            <div className="flex flex-col gap-2">
              <p className="text-sm text-gray-300">Episodes</p>
              <div className="flex flex-wrap gap-2">
                {episodes.map((episode) => {
                const hasSources = episode.video_sources.some((vs) => vs.is_active !== false);
                return (
                  <button
                    key={episode.id}
                    type="button"
                    onClick={() => selectEpisode(episode)}
                    className={`px-3 py-2 rounded border text-sm ${
                      episode.id === selectedEpisode?.id
                        ? "bg-blue-600 border-blue-500 text-white"
                        : hasSources
                        ? "bg-neutral-800 border-neutral-700 text-white hover:border-blue-400"
                        : "bg-neutral-900 border-neutral-800 text-gray-500 cursor-not-allowed"
                    }`}
                    disabled={!hasSources}
                  >
                    {episode.number}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
