"use client";

import { useState } from "react";
import { useQueryState, parseAsString, parseAsArrayOf } from "nuqs";
import Image from "next/image";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Search, X, Filter } from "lucide-react";
import { Navbar } from "@/components/blocks/navbar";
import { Footer } from "@/components/blocks/footer";
import { Spinner } from "@/components/ui/spinner";
import { useDebounce } from "@/lib/hooks/use-debounce";
import { useSearchIndex } from "@/hooks/use-search-index";
import { orpc } from "@/lib/query/orpc";

const GENRES = [
  "Action",
  "Adventure",
  "Comedy",
  "Drama",
  "Fantasy",
  "Horror",
  "Mecha",
  "Music",
  "Mystery",
  "Psychological",
  "Romance",
  "Sci-Fi",
  "Slice of Life",
  "Sports",
  "Supernatural",
  "Thriller",
];

const SEASONS = ["winter", "spring", "summer", "fall"];
const TYPES = ["tv", "movie", "ova", "ona", "special"];
const YEARS = Array.from({ length: 30 }, (_, i) => (2025 - i).toString());

export function SearchContent() {
  const [query, setQuery] = useQueryState("q", parseAsString.withDefault(""));
  const [genres, setGenres] = useQueryState(
    "genres",
    parseAsArrayOf(parseAsString).withDefault([]),
  );
  const [year, setYear] = useQueryState("year", parseAsString);
  const [season, setSeason] = useQueryState("season", parseAsString);
  const [type, setType] = useQueryState("type", parseAsString);
  const [showFilters, setShowFilters] = useState(false);

  const debouncedQuery = useDebounce(query, 200);
  const { search, isReady, isBuilding } = useSearchIndex();

  // Use index search if ready, otherwise fall back to API
  const indexResults =
    isReady && debouncedQuery.length >= 2
      ? search(debouncedQuery, 50)
      : null;

  // Fallback to API search if index not ready
  const { data: apiSearchData, isLoading: isApiLoading } = useQuery({
    ...orpc.anime.search.queryOptions({
      input: {
        query: debouncedQuery,
        page: 1,
        filters: {
          type: type || undefined,
          season: season || undefined,
          genres: genres.length > 0 ? genres.join(",") : undefined,
        },
      },
    }),
    enabled: !isReady && debouncedQuery.length >= 2,
  });

  // Filter index results by client-side filters
  const filteredResults = indexResults
    ?.filter((anime) => {
      if (type && anime.type?.toLowerCase() !== type.toLowerCase())
        return false;
      if (genres.length > 0 && anime.genres) {
        const hasGenre = genres.some((g) =>
          anime.genres?.some(
            (ag) => ag.toLowerCase() === g.toLowerCase(),
          ),
        );
        if (!hasGenre) return false;
      }
      return true;
    })
    .slice(0, 50);

  const apiResults = apiSearchData?.animes?.filter(
    (
      item,
    ): item is typeof item & { id: string; name: string; poster: string } =>
      item.id !== null && item.name !== null && item.poster !== null,
  );

  const displayResults = indexResults ? filteredResults : apiResults;
  const isSearching = isApiLoading || isBuilding;

  const toggleGenre = (genre: string) => {
    if (genres.includes(genre)) {
      setGenres(genres.filter((g) => g !== genre));
    } else {
      setGenres([...genres, genre]);
    }
  };

  const clearFilters = () => {
    setGenres([]);
    setYear(null);
    setSeason(null);
    setType(null);
  };

  const hasActiveFilters =
    genres.length > 0 || year || season || type;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Search Anime</h1>
          <p className="text-muted-foreground">
            {isBuilding
              ? "Building search index..."
              : isReady
                ? `${search("").length || "Ready to"} search across indexed anime`
                : "Search for your favorite anime"}
          </p>
        </div>

        {/* Search Input */}
        <div className="relative mb-6">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 size-5 text-muted-foreground" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by title..."
            className="w-full pl-12 pr-12 py-4 rounded-xl border border-border bg-card text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-cyan/50"
          />
          {query && (
            <button
              onClick={() => setQuery("")}
              aria-label="Clear search"
              className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            >
              <X className="size-5" />
            </button>
          )}
        </div>

        {/* Filter Toggle */}
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border bg-card hover:bg-card/80 transition-colors"
          >
            <Filter className="size-4" />
            <span className="text-sm font-medium">
              Filters {hasActiveFilters && `(${genres.length + (year ? 1 : 0) + (season ? 1 : 0) + (type ? 1 : 0)})`}
            </span>
          </button>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Clear all
            </button>
          )}
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="mb-8 p-6 rounded-xl border border-border bg-card">
            {/* Type Filter */}
            <div className="mb-6">
              <label className="block text-sm font-medium mb-3">Type</label>
              <div className="flex flex-wrap gap-2">
                {TYPES.map((t) => (
                  <button
                    key={t}
                    onClick={() => setType(type === t ? null : t)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      type === t
                        ? "bg-cyan text-background"
                        : "bg-foreground/5 text-muted-foreground hover:text-foreground hover:bg-foreground/10"
                    }`}
                  >
                    {t.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            {/* Genres Filter */}
            <div className="mb-6">
              <label className="block text-sm font-medium mb-3">
                Genres {genres.length > 0 && `(${genres.length})`}
              </label>
              <div className="flex flex-wrap gap-2">
                {GENRES.map((g) => (
                  <button
                    key={g}
                    onClick={() => toggleGenre(g)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      genres.includes(g)
                        ? "bg-cyan text-background"
                        : "bg-foreground/5 text-muted-foreground hover:text-foreground hover:bg-foreground/10"
                    }`}
                  >
                    {g}
                  </button>
                ))}
              </div>
            </div>

            {/* Year Filter */}
            <div className="mb-6">
              <label className="block text-sm font-medium mb-3">Year</label>
              <select
                value={year || ""}
                onChange={(e) => setYear(e.target.value || null)}
                className="w-full max-w-xs px-4 py-2 rounded-lg border border-border bg-card text-foreground focus:outline-none focus:ring-2 focus:ring-cyan/50"
              >
                <option value="">Any year</option>
                {YEARS.map((y) => (
                  <option key={y} value={y}>
                    {y}
                  </option>
                ))}
              </select>
            </div>

            {/* Season Filter */}
            <div>
              <label className="block text-sm font-medium mb-3">Season</label>
              <div className="flex flex-wrap gap-2">
                {SEASONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => setSeason(season === s ? null : s)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-all ${
                      season === s
                        ? "bg-cyan text-background"
                        : "bg-foreground/5 text-muted-foreground hover:text-foreground hover:bg-foreground/10"
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        <div>
          {debouncedQuery.length < 2 ? (
            <div className="text-center py-20">
              <Search className="size-12 text-muted-foreground mx-auto mb-4 opacity-50" />
              <p className="text-muted-foreground">
                Enter at least 2 characters to search
              </p>
            </div>
          ) : isSearching ? (
            <div className="flex items-center justify-center py-20">
              <Spinner className="size-8 text-muted-foreground" />
            </div>
          ) : !displayResults || displayResults.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-muted-foreground mb-2">No results found</p>
              <p className="text-sm text-muted-foreground/60">
                Try adjusting your filters or search terms
              </p>
            </div>
          ) : (
            <>
              <div className="mb-6">
                <p className="text-sm text-muted-foreground">
                  {displayResults.length} result
                  {displayResults.length !== 1 ? "s" : ""} for &quot;
                  {debouncedQuery}&quot;
                </p>
              </div>
              <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-4">
                {displayResults.map((anime) => (
                  <Link
                    key={anime.id}
                    href={`/anime/${anime.id}`}
                    className="group block"
                  >
                    <div className="relative aspect-3/4 rounded-lg overflow-hidden bg-foreground/5">
                      {anime.poster && (
                        <Image
                          src={anime.poster}
                          alt={anime.name}
                          fill
                          className="object-cover transition-transform duration-300 group-hover:scale-105"
                        />
                      )}
                      <div className="absolute inset-0 bg-gradient-to-t from-background/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                    <h3 className="mt-2 text-sm text-muted-foreground line-clamp-1 group-hover:text-foreground transition-colors">
                      {anime.name}
                    </h3>
                    <p className="text-xs text-muted-foreground/60">
                      {anime.type} ·{" "}
                      {anime.episodes?.sub ?? anime.episodes?.dub ?? "?"} ep
                    </p>
                  </Link>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      <Footer />
    </div>
  );
}
