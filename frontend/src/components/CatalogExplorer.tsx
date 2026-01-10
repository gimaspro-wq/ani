"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { AnimeListItem } from "@/lib/types";
import { AnimeGrid } from "./AnimeGrid";

interface CatalogExplorerProps {
  anime: AnimeListItem[];
}

const DEBOUNCE = 400;

export function CatalogExplorer({ anime }: CatalogExplorerProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [search, setSearch] = useState(searchParams.get("q") ?? "");
  const [status, setStatus] = useState(searchParams.get("status") ?? "");
  const [year, setYear] = useState(searchParams.get("year") ?? "");
  const [debounced, setDebounced] = useState(search);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(search), DEBOUNCE);
    return () => clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (debounced) params.set("q", debounced);
    if (status) params.set("status", status);
    if (year) params.set("year", year);
    const query = params.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
  }, [debounced, status, year, pathname, router]);

  const years = useMemo(() => {
    const collected = new Set<number>();
    anime.forEach((item) => {
      if (item.year) collected.add(item.year);
    });
    return Array.from(collected).sort((a, b) => b - a);
  }, [anime]);

  const filtered = useMemo(() => {
    const term = debounced.trim().toLowerCase();
    return anime.filter((item) => {
      if (status && item.status !== status) return false;
      if (year && String(item.year ?? "") !== year) return false;
      if (!term) return true;
      const haystack = `${item.title} ${item.description ?? ""}`.toLowerCase();
      return haystack.includes(term);
    });
  }, [anime, debounced, status, year]);

  return (
    <div className="space-y-6">
      <div className="grid gap-3 md:grid-cols-[1fr_180px_180px]">
        <label className="flex items-center gap-3 rounded-lg border border-border bg-foreground/[0.02] px-4 py-2.5 text-sm text-muted-foreground focus-within:border-cyan/60 focus-within:text-foreground">
          <span className="text-xs uppercase tracking-wide text-muted-foreground/70">
            Search
          </span>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Название или описание"
            className="w-full bg-transparent text-foreground outline-none"
            aria-label="Search anime"
          />
        </label>

        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="rounded-lg border border-border bg-foreground/[0.02] px-3 py-2.5 text-sm text-foreground focus:border-cyan/60"
          aria-label="Фильтр по статусу"
        >
          <option value="">Все статусы</option>
          <option value="ongoing">Ongoing</option>
          <option value="completed">Completed</option>
          <option value="upcoming">Upcoming</option>
        </select>

        <select
          value={year}
          onChange={(e) => setYear(e.target.value)}
          className="rounded-lg border border-border bg-foreground/[0.02] px-3 py-2.5 text-sm text-foreground focus:border-cyan/60"
          aria-label="Фильтр по году"
        >
          <option value="">Все годы</option>
          {years.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
      </div>

      {filtered.length ? (
        <AnimeGrid anime={filtered} />
      ) : (
        <div className="rounded-lg border border-border bg-foreground/[0.02] p-8 text-center text-muted-foreground">
          Ничего не найдено
        </div>
      )}
    </div>
  );
}
