export default function PlayerLoading() {
  return (
    <main className="min-h-screen bg-black text-white flex flex-col items-center gap-4 py-8 px-4">
      <div className="w-full max-w-5xl flex flex-col gap-4">
        <div className="space-y-2">
          <div className="h-3 w-20 rounded bg-neutral-800 animate-pulse" />
          <div className="h-8 w-56 rounded bg-neutral-800 animate-pulse" />
        </div>
        <div className="relative w-full aspect-video bg-neutral-900 rounded-lg overflow-hidden">
          <div className="absolute inset-0 bg-neutral-800 animate-pulse" />
        </div>
        <div className="flex gap-2">
          {Array.from({ length: 6 }).map((_, idx) => (
            <div
              key={idx}
              className="h-10 w-16 rounded border border-neutral-800 bg-neutral-900 animate-pulse"
            />
          ))}
        </div>
      </div>
    </main>
  );
}
