export function getServerBaseUrl(): string {
  if (typeof window !== "undefined") {
    return window.location.origin || "";
  }

  try {
    // next/headers is only available in server contexts
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { headers } = require("next/headers") as typeof import("next/headers");
    const incomingHeaders = headers() as unknown as Headers;
    const host =
      incomingHeaders.get("x-forwarded-host") ?? incomingHeaders.get("host");
    const protocol = incomingHeaders.get("x-forwarded-proto") ?? "https";

    if (host) {
      return `${protocol}://${host}`;
    }
  } catch {
    // headers() is not available in some non-request contexts
  }

  if (process.env.VERCEL_URL) {
    return `https://${process.env.VERCEL_URL}`;
  }

  if (process.env.NEXT_PUBLIC_SITE_URL) {
    return process.env.NEXT_PUBLIC_SITE_URL;
  }

  if (process.env.NEXT_PUBLIC_APP_URL) {
    return process.env.NEXT_PUBLIC_APP_URL;
  }

  return "";
}
