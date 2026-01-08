import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Footer } from "@/components/blocks/footer";
import { Navbar } from "@/components/blocks/navbar";
import { AnimeHeader } from "@/components/AnimeHeader";
import { EpisodeList } from "@/components/EpisodeList";
import { getAnimeBySlug, getEpisodesBySlug } from "@/lib/public-api";

export const revalidate = 60;

function truncate(text: string, limit = 160) {
  if (text.length <= limit) return text;
  return `${text.slice(0, limit - 1)}…`;
}

export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}): Promise<Metadata> {
  const anime = await getAnimeBySlug(params.slug);

  if (!anime) {
    return { title: "Аниме не найдено" };
  }

  const description = anime.description
    ? truncate(anime.description)
    : "Описание недоступно.";

  return {
    title: anime.title,
    description,
    openGraph: {
      title: anime.title,
      description,
      images: anime.poster ? [anime.poster] : undefined,
    },
  };
}

export default async function AnimePage({
  params,
}: {
  params: { slug: string };
}) {
  const { slug } = params;
  const [anime, episodes] = await Promise.all([
    getAnimeBySlug(slug),
    getEpisodesBySlug(slug),
  ]);

  if (!anime) {
    notFound();
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 pb-12 pt-20">
        <AnimeHeader anime={anime} />
        <section className="mt-8">
          <EpisodeList episodes={episodes} slug={slug} />
        </section>
      </main>
      <Footer />
    </div>
  );
}
