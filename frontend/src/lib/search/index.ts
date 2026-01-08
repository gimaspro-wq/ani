import MiniSearch from "minisearch";
import { get, set, del } from "idb-keyval";

export type AnimeIndexItem = {
  id: string;
  name: string;
  jname: string | null;
  type: string | null;
  poster: string | null;
  episodes: { sub: number | null; dub: number | null };
  genres?: string[];
  year?: string | null;
  season?: string | null;
  status?: string | null;
  rating?: string | null;
  duration?: string | null;
};

type IndexMetadata = {
  version: string;
  timestamp: number;
  count: number;
};

const INDEX_VERSION = "1.0";
const INDEX_TTL = 24 * 60 * 60 * 1000; // 24 hours
const INDEX_KEY = "anime-search-index";
const METADATA_KEY = "anime-search-metadata";

export class AnimeSearchIndex {
  private miniSearch: MiniSearch<AnimeIndexItem> | null = null;
  private isBuilding = false;
  private buildPromise: Promise<void> | null = null;

  constructor() {
    this.miniSearch = new MiniSearch<AnimeIndexItem>({
      fields: ["name", "jname", "type"], // fields to index
      storeFields: [
        "id",
        "name",
        "jname",
        "type",
        "poster",
        "episodes",
        "genres",
        "year",
        "season",
        "status",
        "rating",
        "duration",
      ], // fields to return
      searchOptions: {
        boost: { name: 2, jname: 1.5 },
        fuzzy: 0.2,
        prefix: true,
      },
    });
  }

  async isValid(): Promise<boolean> {
    try {
      const metadata = await get<IndexMetadata>(METADATA_KEY);
      if (!metadata) return false;

      const isExpired = Date.now() - metadata.timestamp > INDEX_TTL;
      const isVersionMismatch = metadata.version !== INDEX_VERSION;

      return !isExpired && !isVersionMismatch;
    } catch {
      return false;
    }
  }

  async load(): Promise<boolean> {
    try {
      const isValid = await this.isValid();
      if (!isValid) return false;

      const serialized = await get<string>(INDEX_KEY);
      if (!serialized || !this.miniSearch) return false;

      this.miniSearch = MiniSearch.loadJSON(serialized, {
        fields: ["name", "jname", "type"],
        storeFields: [
          "id",
          "name",
          "jname",
          "type",
          "poster",
          "episodes",
          "genres",
          "year",
          "season",
          "status",
          "rating",
          "duration",
        ],
        searchOptions: {
          boost: { name: 2, jname: 1.5 },
          fuzzy: 0.2,
          prefix: true,
        },
      });

      return true;
    } catch (error) {
      console.error("Failed to load search index:", error);
      return false;
    }
  }

  async save(): Promise<void> {
    try {
      if (!this.miniSearch) return;

      const serialized = JSON.stringify(this.miniSearch);
      const metadata: IndexMetadata = {
        version: INDEX_VERSION,
        timestamp: Date.now(),
        count: this.miniSearch.documentCount,
      };

      await Promise.all([
        set(INDEX_KEY, serialized),
        set(METADATA_KEY, metadata),
      ]);
    } catch (error) {
      console.error("Failed to save search index:", error);
    }
  }

  async clear(): Promise<void> {
    try {
      await Promise.all([del(INDEX_KEY), del(METADATA_KEY)]);
      if (this.miniSearch) {
        this.miniSearch.removeAll();
      }
    } catch (error) {
      console.error("Failed to clear search index:", error);
    }
  }

  async build(items: AnimeIndexItem[]): Promise<void> {
    // If already building, return the existing promise
    if (this.isBuilding && this.buildPromise) {
      return this.buildPromise;
    }

    this.isBuilding = true;
    this.buildPromise = this._doBuild(items);

    try {
      await this.buildPromise;
    } finally {
      this.isBuilding = false;
      this.buildPromise = null;
    }
  }

  private async _doBuild(items: AnimeIndexItem[]): Promise<void> {
    try {
      if (!this.miniSearch) {
        throw new Error("MiniSearch not initialized");
      }

      // Clear existing documents
      this.miniSearch.removeAll();

      // Filter out items without required fields and add to index
      const validItems = items.filter((item) => item.id && item.name);
      this.miniSearch.addAll(validItems);

      // Persist to IndexedDB
      await this.save();
    } catch (error) {
      console.error("Failed to build search index:", error);
      throw error;
    }
  }

  search(query: string, limit = 50): AnimeIndexItem[] {
    if (!this.miniSearch || !query.trim()) {
      return [];
    }

    try {
      const results = this.miniSearch.search(query, {
        boost: { name: 2, jname: 1.5 },
        fuzzy: 0.2,
        prefix: true,
      });

      // MiniSearch returns SearchResult objects that include the stored fields
      return results.slice(0, limit) as unknown as AnimeIndexItem[];
    } catch (error) {
      console.error("Search error:", error);
      return [];
    }
  }

  getDocumentCount(): number {
    return this.miniSearch?.documentCount ?? 0;
  }

  isReady(): boolean {
    return this.miniSearch !== null && this.miniSearch.documentCount > 0;
  }

  isIndexing(): boolean {
    return this.isBuilding;
  }
}

// Singleton instance
let searchIndexInstance: AnimeSearchIndex | null = null;

export function getSearchIndex(): AnimeSearchIndex {
  if (!searchIndexInstance) {
    searchIndexInstance = new AnimeSearchIndex();
  }
  return searchIndexInstance;
}
