import { Footer } from "@/components/blocks/footer";
import { Navbar } from "@/components/blocks/navbar";
import { AnimeGridSkeleton } from "@/components/AnimeGrid";

export default function CatalogLoading() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 pb-12 pt-20 space-y-8">
        <header className="space-y-2">
          <div className="h-3 w-16 rounded bg-foreground/10 animate-pulse" />
          <div className="h-8 w-48 rounded bg-foreground/10 animate-pulse" />
          <div className="h-4 w-80 max-w-full rounded bg-foreground/10 animate-pulse" />
        </header>
        <AnimeGridSkeleton />
      </main>
      <Footer />
    </div>
  );
}
