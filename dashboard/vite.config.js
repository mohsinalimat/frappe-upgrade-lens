import path from "path";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
	plugins: [vue()],
	build: {
		outDir: path.resolve(__dirname, "../upgrade_lens/public/dist"),
		emptyOutDir: true,
		lib: {
			entry: path.resolve(__dirname, "src/main.js"),
			name: "UpgradeLensDashboard",
			formats: ["iife"],
			fileName: () => "upgrade_lens_dashboard.js",
		},
		rollupOptions: {
			output: {
				extend: true,
				inlineDynamicImports: true,
			},
		},
		target: "es2015",
	},
	define: {
		"process.env.NODE_ENV": JSON.stringify("production"),
	},
});
