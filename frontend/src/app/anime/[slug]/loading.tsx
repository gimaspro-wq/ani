import { Footer } from "@/components/blocks/footer";
import { Navbar } from "@/components/blocks/navbar";
import { AnimeHeaderSkeleton } from "@/components/AnimeHeader";
import { EpisodeListSkeleton } from "@/components/EpisodeList";

export default function AnimeLoading() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 pb-12 pt-20 space-y-8">
        <AnimeHeaderSkeleton />
        <EpisodeListSkeleton />
      </main>
      <Footer />
    </div>
  );
}
