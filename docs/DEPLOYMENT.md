# Viewer deployment

The repository includes `.github/workflows/pages.yml` to publish the static `frontend/` viewer with GitHub Pages.

Before each deployment the workflow installs the BrickHouse Python package and runs the BH-016 reference pipeline:

```text
docs/examples/building-model-simple-house.json
    -> frontend/sample-export.json
```

The deployed sample therefore comes from the real deterministic engine rather than the hand-written viewer fixture.

## GitHub Pages

The workflow uses the official Pages Actions flow (`configure-pages`, `upload-pages-artifact`, `deploy-pages`) and requires no application secret.

If the repository has never had Pages enabled, GitHub may require the repository Pages build source to be set to **GitHub Actions** in repository settings before the first deployment can succeed. This connected-tool session can add the workflow but does not expose the repository Pages settings control, so that one-time setting cannot be changed here.

## Local viewer

The frontend remains a static site and can also be served locally:

```bash
python -m http.server 8000 --directory frontend
```

Then open `http://localhost:8000`.
