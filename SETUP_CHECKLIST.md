# 🚀 Quick Setup Checklist

After cloning this repository, follow these steps:

## Local Development Setup ✅

- [ ] **Install uv** (if not already installed)
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- [ ] **Install dependencies**
  ```bash
  uv sync
  ```

- [ ] **Install pre-commit hooks**
  ```bash
  uv run pre-commit install
  ```

- [ ] **Configure environment**
  ```bash
  cp .env.example .env
  # Edit .env with your paths and Azure credentials
  ```

- [ ] **Test everything works**
  ```bash
  uv run pytest tests/ -v
  uv run pre-commit run --all-files
  ```

## Enable pre-commit.ci (One-Time) ✅

- [ ] **Visit https://pre-commit.ci**
- [ ] **Sign in with GitHub**
- [ ] **Enable for `madebygps/second-brain`**
- [ ] **Done!** 🎉

Pre-commit.ci will now:
- Auto-fix PRs (formatting, linting, imports)
- Send weekly dependency update PRs
- Run faster than GitHub Actions

## Verify Everything Works ✅

- [ ] **Create a test branch**
  ```bash
  git checkout -b test-setup
  ```

- [ ] **Make a small change**
  ```bash
  echo "# Test" >> test.md
  git add test.md
  git commit -m "Test pre-commit hooks"
  ```

- [ ] **Pre-commit hooks should run automatically**
  - Ruff linting ✓
  - Ruff formatting ✓
  - File checks ✓
  - Pytest ✓

- [ ] **Push and create a PR**
  ```bash
  git push origin test-setup
  ```

- [ ] **Verify GitHub Actions runs** (check Actions tab)

- [ ] **Verify pre-commit.ci runs** (if enabled, check PR checks)

- [ ] **Clean up**
  ```bash
  git checkout main
  git branch -D test-setup
  rm test.md
  ```

## Success! 🎊

You're all set up! Your development environment includes:
- ✅ Fast Python package management (uv)
- ✅ Automated code quality (ruff)
- ✅ Pre-commit hooks (catches issues before commit)
- ✅ CI/CD pipeline (GitHub Actions)
- ✅ Auto-fixing PRs (pre-commit.ci)
- ✅ Weekly dependency updates (pre-commit.ci)

## Daily Workflow

```bash
# Create a branch
git checkout -b feature/my-feature

# Make changes
vim brain_core/something.py

# Commit (hooks run automatically)
git add .
git commit -m "Add new feature"

# Push
git push origin feature/my-feature

# Create PR on GitHub
# pre-commit.ci will auto-fix any issues!
```

## Need Help?

- **Documentation**: See `README.md` and `CONTRIBUTING.md`
- **pre-commit.ci Guide**: See `docs/PRE_COMMIT_CI_GUIDE.md`
- **CI/CD Details**: See `docs/CI_CD_SETUP.md`
- **Issues**: Open an issue on GitHub
