"use client";

import { useEffect, useRef, useState } from "react";
import Hls from "hls.js";

const SAMPLE_EPISODE = {
  title: "Sample Episode 1",
  streamUrl: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
};

export default function PlayerPage() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const hlsRef = useRef<Hls | null>(null);
  const [levels, setLevels] = useState<Hls.Level[]>([]);
  const [currentLevel, setCurrentLevel] = useState<number>(-1);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

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

      hls.loadSource(SAMPLE_EPISODE.streamUrl);
      hls.attachMedia(video);
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = SAMPLE_EPISODE.streamUrl;
    }

    return () => {
      hlsRef.current?.destroy();
      hlsRef.current = null;
    };
  }, []);

  const handleQualityChange = (levelIndex: number) => {
    if (hlsRef.current) {
      hlsRef.current.currentLevel = levelIndex;
    }
  };

  return (
    <main className="min-h-screen bg-black text-white flex flex-col items-center gap-4 py-8 px-4">
      <div className="w-full max-w-5xl flex flex-col gap-3">
        <div>
          <p className="text-sm text-gray-400 uppercase tracking-wide">Episode</p>
          <h1 className="text-2xl font-semibold">{SAMPLE_EPISODE.title}</h1>
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
      </div>
    </main>
  );
}
