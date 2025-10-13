# Contributing

This is a personal project, but if you'd like to contribute, here's how to set up the development environment.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/madebygps/second-brain.git
cd second-brain

# Install dependencies with uv
uv sync

# Install pre-commit hooks
uv run pre-commit install

# Configure your environment
cp .env.example .env
# Edit .env with your paths and Azure credentials
```

## Making Changes

1. **Create a branch** for your changes
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** - The pre-commit hooks will automatically:
   - Lint code with ruff (auto-fixes issues)
   - Format code with ruff-format
   - Run the 7 essential tests
   - Check file endings and whitespace

3. **Run tests manually** if needed:
   ```bash
   uv run pytest tests/ -v
   uv run pytest tests/ --cov  # with coverage
   ```

4. **Commit your changes** - Pre-commit hooks will run automatically:
   ```bash
   git add .
   git commit -m "Your descriptive commit message"
   ```

5. **Push and create a PR**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **pre-commit.ci will automatically**:
   - Run checks on your PR
   - Auto-fix any formatting/linting issues
   - Push fixes to your PR branch

## Testing Philosophy

This is a **personal project** with minimal tests focused on preventing data loss:

- ✅ Configuration validation (missing paths)
- ✅ File naming (reflection vs. plan entries)
- ✅ Write/read cycles (data persistence)
- ✅ Path separation (diary vs. planner)

We don't test:
- ❌ LLM responses (too variable)
- ❌ CLI output formatting (not critical)
- ❌ Template generation (easily tested manually)
- ❌ Search functionality (depends on external Azure service)

## Code Style

- **Formatting**: Handled automatically by `ruff-format` (100 char line length)
- **Type hints**: Use Python 3.13+ type hints on all functions
- **Naming**: Clear, descriptive names (no abbreviations unless obvious)
- **Comments**: Docstrings on all public functions

## CI/CD

**GitHub Actions** runs on push/PR:
- Runs all 7 tests with coverage
- Validates test count (ensures tests aren't accidentally deleted)
- Checks Python 3.13 compatibility

**[pre-commit.ci](https://pre-commit.ci)** (free for open source):
- Auto-fixes PRs (formatting, imports, whitespace)
- Weekly dependency updates via automated PRs
- Faster than GitHub Actions for simple checks
- Comment `pre-commit.ci run` to re-trigger
- Skip with `[skip pre-commit.ci]` in commit message

## Package Management

**ALWAYS use `uv`, never `pip`**:

```bash
# Add a dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Update dependencies
uv sync

# Remove a dependency
uv remove package-name
```

## Questions?

Open an issue or reach out to [@madebygps](https://github.com/madebygps).
