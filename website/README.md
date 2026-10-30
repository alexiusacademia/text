# text's website

The page for the text library, live at https://text-package.syncster.dev.

Author: Alexius Academia · Started 2026-10-31

A static page: no build step, no dependencies. Netlify (project
`text-package`, team syncster.dev) deploys this folder by itself whenever
`main` is pushed to GitHub.

```
index.html          # the page; its example outputs were printed by running them
styles.css          # csv's website's design, in violet
assets/share.png    # the picture shown when a link to the site is shared (1200 × 630)
assets/favicon.svg
netlify.toml        # no build; HTML isn't cached
```

To look at it locally: `python3 -m http.server 8080 -d website`, then
http://localhost:8080/.

If an example changes, run it with the library and copy its output in.
