export function getServerBaseUrl(): string {
  // Client-side: return empty string or origin
  if (typeof window !== "undefined") {
    return window.location.origin || "";
  }

  // Server-side: require NEXT_PUBLIC_BACKEND_URL
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
  
  if (!backendUrl) {
    throw new Error("NEXT_PUBLIC_BACKEND_URL is required for SSR");
  }

  return backendUrl;
}
