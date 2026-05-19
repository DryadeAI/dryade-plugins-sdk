/**
 * with_ui — example React UI bundle for a Dryade plugin.
 *
 * Production plugins compile this file (plus dependencies) into a single
 * JS bundle. The host verifies the bundle's SHA-256 against the
 * `ui_bundle_hash` declared in `dryade.json` before mounting it (Rule §9).
 *
 * The host injects the React runtime — plugins do NOT bundle their own
 * React. Use the `@dryade/workbench-sdk` peer dependency to access the
 * shared host primitives (auth, fetcher, theme, toasts).
 */

import React, { useEffect, useState } from "react";

interface WidgetData {
  widget: string;
  value: number;
}

export default function WithUIPanel(): JSX.Element {
  const [data, setData] = useState<WidgetData | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/plugins/with_ui/api/widget")
      .then((r) => r.json())
      .then(setData)
      .catch((e) => setErr(String(e)));
  }, []);

  if (err) return <div role="alert">Error: {err}</div>;
  if (!data) return <div>Loading…</div>;

  return (
    <section>
      <h2>{data.widget}</h2>
      <p>
        Backend reports: <strong>{data.value}</strong>
      </p>
    </section>
  );
}
