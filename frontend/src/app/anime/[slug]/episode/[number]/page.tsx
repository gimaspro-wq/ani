import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Footer } from "@/components/blocks/footer";
import { Navbar } from "@/components/blocks/navbar";
import { EpisodeList } from "@/components/EpisodeList";
import { EpisodePlayerWrapper } from "@/components/EpisodePlayerWrapper";
import { getAnimeBySlug, getEpisodesBySlug } from "@/lib/public-api";

export const revalidate = 60;

function truncate(text: string, limit = 160) {
  if (text.length <= limit) return text;
  return `${text.slice(0, limit - 1)}…`;
}

export async function generateMetadata({
  params,
}: {
  params: { slug: string; number: string };
}): Promise<Metadata> {
  const episodeNumber = Number(params.number);
  const anime = await getAnimeBySlug(params.slug);

  if (!anime || Number.isNaN(episodeNumber)) {
    return { title: "Эпизод не найден", robots: { index: false, follow: false } };
  }

  const title = `${anime.title} — Серия ${episodeNumber}`;
  const description = anime.description
    ? truncate(anime.description)
    : "Описание недоступно.";

  return {
    title,
    description,
    alternates: { canonical: `/anime/${params.slug}/episode/${params.number}` },
    openGraph: {
      title,
      description,
      images: anime.poster ? [anime.poster] : undefined,
    },
  };
}

export default async function EpisodePage({
  params,
}: {
  params: { slug: string; number: string };
}) {
  const { slug, number } = params;
  const episodeNumber = Number(number);

  if (Number.isNaN(episodeNumber)) {
    notFound();
  }

  const [anime, episodes] = await Promise.all([
    getAnimeBySlug(slug),
    getEpisodesBySlug(slug),
  ]);

  if (!anime || !episodes.length) {
    notFound();
  }

  const episode = episodes.find((item) => item.number === episodeNumber);

  if (!episode) {
    notFound();
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <EpisodeView
        animeTitle={anime.title}
        slug={slug}
        episode={episode}
        episodes={episodes}
      />
      <Footer />
    </div>
  );
}

function EpisodeView({
  animeTitle,
  slug,
  episode,
  episodes,
}: {
  animeTitle: string;
  slug: string;
  episode: (typeof episodes)[number];
  episodes: typeof episodes;
}) {
  return (
    <main className="mx-auto max-w-6xl px-4 pb-12 pt-20 space-y-8">
      <div className="space-y-3">
        <p className="text-xs uppercase tracking-wide text-muted-foreground/70">
          Серия {episode.number}
        </p>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold text-foreground lg:text-3xl">
              {animeTitle}
            </h1>
            <p className="text-sm text-muted-foreground">
              {episode.title || "Название серии недоступно"}
            </p>
          </div>
        </div>
      </div>

      <EpisodePlayerWrapper
        slug={slug}
        episodes={episodes}
        currentNumber={episode.number}
        sources={episode.video_sources}
        animeTitle={animeTitle}
      />

      <EpisodeList
        episodes={episodes}
        slug={slug}
        currentNumber={episode.number}
        className="pt-4"
      />
    </main>
  );
}
