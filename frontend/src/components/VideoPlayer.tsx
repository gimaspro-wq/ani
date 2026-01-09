"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { VideoSource } from "@/lib/types";
import { SourceSwitcher } from "./SourceSwitcher";
import { Spinner } from "@/components/ui/spinner";

interface VideoPlayerProps {
  sources: VideoSource[];
  title?: string;
  onEnded?: () => void;
}

export function VideoPlayer({ sources, title, onEnded }: VideoPlayerProps) {
  const [selectedId, setSelectedId] = useState<string | null>(sources[0]?.id ?? null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    setSelectedId(sources[0]?.id ?? null);
  }, [sources]);

  const selectedSource = useMemo(
    () => sources.find((source) => source.id === selectedId) ?? sources[0],
    [selectedId, sources],
  );

  useEffect(() => {
    if (!selectedSource) return;

    // Reset previous errors when switching sources
    setError(null);
    setIsLoading(true);

    if (selectedSource.type === "mp4" || selectedSource.type === "m3u8") {
      const video = videoRef.current;
      if (!video) return;

      let hlsInstance: { destroy: () => void } | null = null;

      const setupHls = async () => {
        if (selectedSource.type === "mp4") {
          video.src = selectedSource.url;
          video.load();
          return;
        }

        if (video.canPlayType("application/vnd.apple.mpegurl")) {
          video.src = selectedSource.url;
          video.load();
          return;
        }

        try {
          const Hls = (await import("hls.js")).default;
          if (Hls.isSupported()) {
            hlsInstance = new Hls();
            hlsInstance.loadSource(selectedSource.url);
            hlsInstance.attachMedia(video);
          } else {
            setError("Видео временно недоступно");
          }
        } catch (setupError) {
          console.error("HLS setup error", setupError);
          setError("Видео временно недоступно");
        }
      };

      setupHls();

      return () => {
        if (hlsInstance) {
          hlsInstance.destroy();
        }
      };
    }

    return undefined;
  }, [selectedSource]);

  if (!sources.length || !selectedSource) {
    return (
      <div className="rounded-xl border border-border bg-foreground/[0.02] p-6 text-center text-muted-foreground">
        Видео временно недоступно
      </div>
    );
  }

  const playerTitle = title || "Плеер";

  return (
    <div className="space-y-4">
      <div className="overflow-hidden rounded-xl border border-border bg-foreground/[0.02]">
        <div className="border-b border-border px-4 py-3 flex items-center justify-between">
          <div>
            <p className="text-xs text-muted-foreground/70">Источник</p>
            <p className="text-sm font-medium text-foreground">
              {selectedSource.source_name || "Видео"}
            </p>
          </div>
          <span className="text-xs uppercase text-muted-foreground/70">
            {selectedSource.type}
          </span>
        </div>

        <div className="relative aspect-video bg-foreground/5">
          {selectedSource.type === "iframe" || selectedSource.type === "embed" ? (
            <iframe
              key={selectedSource.id}
              src={selectedSource.url}
              title={playerTitle}
              className="absolute inset-0 h-full w-full rounded-b-xl"
              allowFullScreen
              onLoad={() => setIsLoading(false)}
              onError={() => {
                setIsLoading(false);
                setError("Видео временно недоступно");
              }}
            />
          ) : (
            <video
              key={selectedSource.id}
              ref={videoRef}
              className="absolute inset-0 h-full w-full rounded-b-xl bg-black"
              controls
              playsInline
              onLoadedData={() => setIsLoading(false)}
              onCanPlay={() => setIsLoading(false)}
              onError={() => {
                setIsLoading(false);
                setError("Видео временно недоступно");
              }}
              onEnded={onEnded}
            />
          )}

          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/30 backdrop-blur-sm">
              <Spinner className="h-8 w-8 text-white" />
            </div>
          )}
        </div>
      </div>

      <SourceSwitcher
        sources={sources}
        activeId={selectedSource.id}
        onSelect={(id) => {
          setSelectedId(id);
          setIsLoading(true);
        }}
      />

      {error ? (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      ) : null}
    </div>
  );
}
