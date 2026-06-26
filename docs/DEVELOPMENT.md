# Development Guide

## Setup

```bash
cd projects/videocontext
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,test]"
```

For frames support:

```bash
pip install -e ".[vision]"
```

## Core Commands

```bash
make test
make lint
make lint-fix
make precommit-install
make precommit-run
```

## Live Checks

```bash
./scripts/smoke_e2e.sh
vc frames "https://www.youtube.com/watch?v=<id>" --interval 15 --max-frames 3 --output-dir ./frames_test
```

## Release Flow

```bash
make bump V=0.2.0
make release-check
git tag videocontext-v0.2.0
git push origin videocontext-v0.2.0
```

Also see `docs/RELEASE_SETUP.md`.
