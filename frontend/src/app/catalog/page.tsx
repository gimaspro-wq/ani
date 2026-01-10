import { Suspense } from "react";
import { Footer } from "@/components/blocks/footer";
import { Navbar } from "@/components/blocks/navbar";
import { AnimeGridSkeleton } from "@/components/AnimeGrid";
import { CatalogExplorer } from "@/components/CatalogExplorer";
import { getAnimeList } from "@/lib/public-api";

export const revalidate = 60;

async function CatalogContent() {
  const anime = await getAnimeList();
  return <CatalogExplorer anime={anime} />;
}

export default function CatalogPage() {
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
            Используются публичные READ эндпоинты. Обновление каждые 60 секунд.
          </p>
        </header>

        <Suspense fallback={<AnimeGridSkeleton />}>
          {/* Server component fetch; Suspense for initial load */}
          <CatalogContent />
        </Suspense>
      </main>
      <Footer />
    </div>
  );
}
