import type { Metadata } from "next";

interface LayoutProps {
  children: React.ReactNode;
}

export const metadata: Metadata = {
  title: "Search Anime - Anirohi",
  description:
    "Search and discover anime series and movies. Find your favorite shows by title, genre, or season.",
  robots: {
    index: false,
    follow: true,
  },
  openGraph: {
    title: "Search Anime - Anirohi",
    description:
      "Search and discover anime series and movies. Find your favorite shows by title, genre, or season.",
  },
  twitter: {
    card: "summary",
    title: "Search Anime - Anirohi",
    description:
      "Search and discover anime series and movies. Find your favorite shows by title, genre, or season.",
  },
};

export default function SearchLayout({ children }: LayoutProps) {
  return <>{children}</>;
}
