import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/api/", "/rpc/"],
    },
    sitemap: "https://anirohi.com/sitemap.xml",
  };
}
