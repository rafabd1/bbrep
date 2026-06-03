import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

export default defineConfig({
  site: "https://bbrep.vercel.app",
  integrations: [sitemap()],
});
