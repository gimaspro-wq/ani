import type { Metadata } from "next";

interface LayoutProps {
  children: React.ReactNode;
  params: Promise<{ id: string; episode: string }>;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string; episode: string }>;
}): Promise<Metadata> {
  const { id, episode } = await params;

  // Generic but useful metadata for watch pages
  const title = `Watch Episode ${episode} - Anirohi`;
  const description = `Watch anime Episode ${episode} online in HD quality with subtitles and dub options on Anirohi.`;

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      type: "video.episode",
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
    },
  };
}

export default async function WatchLayout({ children }: LayoutProps) {
  return <>{children}</>;
}
