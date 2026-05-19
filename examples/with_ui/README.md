# with_ui

Plugin that ships a React UI bundle plus a backend route the UI fetches.

## What this example shows

- **`has_ui: true` + `ui_bundle_hash`** — the manifest declares the plugin
  has a UI half. The host verifies the on-disk JS bundle's SHA-256 matches
  `ui_bundle_hash` before mounting it. Fail-closed: a tampered bundle is
  silently skipped.
- **`@route` decorator** — the backend exposes one HTTP route mounted at
  `/api/plugins/with_ui/api/widget`.
- **UI source layout** — `ui/index.tsx` is the entry point. Real plugins
  compile this with vite / esbuild / rollup into a single bundle whose
  SHA-256 goes into the manifest.

## Files

| File | Purpose |
|------|---------|
| `dryade.json` | Manifest with `has_ui: true` + 64-char `ui_bundle_hash` |
| `plugin.py` | Backend half — `@route` handler |
| `ui/index.tsx` | UI entry point — React component the workbench mounts |
| `tests/test_plugin.py` | Route + manifest + UI-file-on-disk tests |

## Run the backend tests

```bash
cd examples/with_ui
pytest tests/
```

## Build the UI bundle (production)

Use your own toolchain — Dryade has no opinion on which bundler you use,
as long as the output is a single JS file whose SHA-256 matches
`ui_bundle_hash` in the manifest.

A typical vite config (`vite.config.ts`):

```ts
import { defineConfig } from "vite";
export default defineConfig({
  build: {
    lib: { entry: "ui/index.tsx", formats: ["es"], fileName: "bundle" },
    rollupOptions: {
      external: ["react", "react-dom"],  // host injects React
    },
  },
});
```

Then regenerate the hash:

```bash
sha256sum dist/bundle.js | awk '{print $1}'
```

…and paste it into `ui_bundle_hash` in `dryade.json`. The CLI's
`dryade plugin package` will validate the match.
