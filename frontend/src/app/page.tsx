import { Suspense } from "react";
import { Footer } from "@/components/blocks/footer";
import { Navbar } from "@/components/blocks/navbar";
import { AnimeGrid, AnimeGridSkeleton } from "@/components/AnimeGrid";
import type { AnimeListItem } from "@/lib/types";
import { getAnimeList } from "@/lib/public-api";

export const revalidate = 60;

async function AnimeCatalog({ promise }: { promise: Promise<AnimeListItem[]> }) {
  const anime = await promise;
  return <AnimeGrid anime={anime} />;
}

export default function HomePage() {
  const animePromise = getAnimeList();

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 pb-12 pt-20 space-y-8">
        <header className="space-y-2">
          <p className="text-xs uppercase tracking-wide text-muted-foreground/70">
            Каталог
          </p>
          <h1 className="text-3xl font-semibold text-foreground lg:text-4xl">
            Аниме
          </h1>
          <p className="text-sm text-muted-foreground">
            Обновляется каждые 60 секунд. Используется публичный API.
          </p>
        </header>

        <Suspense fallback={<AnimeGridSkeleton />}>
          <AnimeCatalog promise={animePromise} />
        </Suspense>
      </main>
      <Footer />
    </div>
  );
}
