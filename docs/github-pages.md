# GitHub Pages

This repository is ready to publish the MkDocs site with GitHub Pages.

## One-Time Repository Setting

In the GitHub repository settings, set Pages to use **GitHub Actions** as the build and deployment source. After that, the workflow in `.github/workflows/pages.yml` handles the rest.

## Deployment Workflow

The workflow runs on pushes to `main` and on manual dispatch. It:

1. Checks out the repository.
2. Sets up Python and `uv`.
3. Runs `uvx --from mkdocs --with 'mkdocs-material==9.5.*' --with pymdown-extensions mkdocs build --strict --site-dir site`.
4. Uploads the built `site/` directory as a Pages artifact.
5. Deploys the artifact to GitHub Pages.

The expected public URL is:

```text
https://fmschulz.github.io/omics-skills/
```

If the repository owner or name changes, update `site_url` in `mkdocs.yml`.

## Local Build

Run the same strict build locally:

```bash
uvx --from mkdocs --with 'mkdocs-material==9.5.*' --with pymdown-extensions mkdocs build --strict
```

Preview while editing:

```bash
uvx --from mkdocs --with 'mkdocs-material==9.5.*' --with pymdown-extensions mkdocs serve
```

MkDocs writes the local build to `site/`; that directory is generated output and should not be committed.
