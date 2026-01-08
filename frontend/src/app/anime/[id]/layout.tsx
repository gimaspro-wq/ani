import type { Metadata } from "next";

interface LayoutProps {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;

  // Since we can't easily fetch data at build time with the current architecture,
  // we'll provide generic but useful metadata
  // The actual title will be updated client-side via the page component
  
  const title = `Watch Anime - Anirohi`;
  const description = `Watch anime episodes online in HD quality. Stream with subtitles and dub options on Anirohi.`;

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      type: "video.tv_show",
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
    },
  };
}

export default async function AnimeLayout({ children }: LayoutProps) {
  return <>{children}</>;
}
