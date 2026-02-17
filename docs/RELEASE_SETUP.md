# Release Setup

This project publishes to PyPI using trusted publishing from GitHub Actions.

## 1) Create the PyPI project

1. Log in to PyPI.
2. Create project `videocontext` (or your chosen package name).
3. Ensure maintainers/owners are set correctly.

## 2) Configure trusted publishing on PyPI

In PyPI project settings, add a trusted publisher with:

- Owner: `YOUR_GITHUB_USERNAME_OR_ORG`
- Repository name: `claude_journey`
- Workflow name: `videocontext-release.yml`
- Environment name: leave empty (unless you add one in workflow)

Notes:
- Workflow file path in this repo is `.github/workflows/videocontext-release.yml`.
- Release workflow triggers on tags: `videocontext-v*`.

## 3) Validate GitHub workflow permissions

The workflow already requests `id-token: write` in the `publish` job.
No PyPI API token secret is needed with trusted publishing.

## 4) First release run

From `projects/videocontext`:

```bash
python scripts/bump_version.py 0.2.0
python -m unittest discover -s tests -v
git add .
git commit -m "release: 0.2.0"
git tag videocontext-v0.2.0
git push origin main
git push origin videocontext-v0.2.0
```

After push, watch GitHub Actions run `VideoContext Release`.
