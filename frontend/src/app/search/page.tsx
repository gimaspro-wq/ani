"use client";

import { Suspense } from "react";
import { SearchContent } from "./search-content";

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="min-h-screen" />}>
      <SearchContent />
    </Suspense>
  );
}
