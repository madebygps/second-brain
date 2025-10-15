# Setup Checklist for second-brain

Complete guide for first-time setup after installation.

## Installation


```bash
uv tool install git+https://github.com/madebygps/second-brain.git
```

Verify installation:
```bash
brain --version
# Output: Brain CLI v0.1.0
```

## Configuration

### Step 1: Create Directories

Create directories for your diary and planner:

```bash
# Create diary directory (for reflection entries)
mkdir -p ~/Documents/second-brain/diary

# Create planner directory (for daily plans)
mkdir -p ~/Documents/second-brain/planner
```

> **Tip:** Best if used with Obsidian. Point `DIARY_PATH` to your vault directory.

### Step 2: Create .env File

The `brain` CLI automatically searches for `.env` in these locations (in order):

1. **Current directory** (`./.env`)
2. **User config directory** (`~/.config/brain/.env`) ⭐ **Recommended**
3. **Home directory** (`~/.brain/.env`)

**Recommended Setup (works from anywhere):**

```bash
# Create config directory
mkdir -p ~/.config/brain

# Download the example .env template
curl -o ~/.config/brain/.env https://raw.githubusercontent.com/madebygps/second-brain/main/.env.example

# Set secure permissions (readable by you only)
chmod 600 ~/.config/brain/.env

# Edit with your settings
nano ~/.config/brain/.env  # or use your preferred editor
```

That's it! No need for shell aliases or cd-ing around. The `brain` command will automatically find your config.

> **Security Note:** Your `.env` file contains API keys. The `chmod 600` command ensures only you can read it.


The current directory's `.env` takes priority over the global config.

### Step 3: Configure .env

Edit your `.env` file with the following **required** variables:

```bash
# Required: Paths (created in Step 1)
DIARY_PATH=/Users/yourname/Documents/second-brain/diary
PLANNER_PATH=/Users/yourname/Documents/second-brain/planner

# Required: LLM Provider (choose one)
LLM_PROVIDER=azure  # or "ollama" for local

# Option 1: Azure OpenAI (cloud-based)
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Option 2: Ollama (local, free)
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=llama3.1
```

**Optional variables** (with defaults):

```bash
# Cost tracking database location
BRAIN_COST_DB_PATH=~/.brain/costs.db

# Logging
BRAIN_LOG_LEVEL=INFO
BRAIN_LOG_FILE=~/.brain/logs/brain.log
```

### Step 4: Setup LLM Provider

Choose **one** of the following:

#### Option 1: Azure OpenAI (Cloud)

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Azure OpenAI resource
3. Go to **Keys and Endpoint**
4. Copy:
   - **KEY 1** → `AZURE_OPENAI_API_KEY`
   - **Endpoint** → `AZURE_OPENAI_ENDPOINT`
5. Go to **Model deployments**
6. Copy your deployment name (e.g., "gpt-4o") → `AZURE_OPENAI_DEPLOYMENT`
7. Set `LLM_PROVIDER=azure` in `.env`

#### Option 2: Ollama (Local)

1. Install Ollama from https://ollama.com
2. Start Ollama (it runs in the background)
3. Pull a model:
   ```bash
   ollama pull llama3.1        # Fast, balanced (4.7GB)
   # OR
   ollama pull llama3.2        # Smaller, faster (2GB)
   # OR
   ollama pull qwen2.5:7b      # Great for structured output
   ```
4. Set in `.env`:
   ```bash
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=llama3.1  # or whichever model you pulled
   ```

### Step 5: Test Configuration

Test that everything is configured correctly:

```bash
# Test diary commands (uses DIARY_PATH)
brain diary list

# Test plan commands (uses PLANNER_PATH)
brain plan create today

# Test cost tracking (uses BRAIN_COST_DB_PATH)
brain cost summary
```

## Troubleshooting

### "DIARY_PATH must be set in .env"

The `brain` command cannot find your `.env` file. The error message will show where it's looking.

Create `.env` in the recommended location:
```bash
mkdir -p ~/.config/brain
nano ~/.config/brain/.env
```

### "DIARY_PATH does not exist: /path/to/dir"

The directory doesn't exist. Create it:
```bash
mkdir -p /path/to/dir
```

### "Azure OpenAI credentials required" or "LLM_PROVIDER must be set"

**If using Azure OpenAI:**
1. Set `LLM_PROVIDER=azure` in `.env`
2. Ensure `AZURE_OPENAI_API_KEY` is set correctly
3. Ensure `AZURE_OPENAI_ENDPOINT` ends with a `/`
4. Ensure `AZURE_OPENAI_DEPLOYMENT` matches your deployment name in Azure Portal

**If using Ollama:**
1. Set `LLM_PROVIDER=ollama` in `.env`
2. Make sure Ollama is running (check with `ollama list`)
3. Pull a model if you haven't: `ollama pull llama3.1`
4. Set `OLLAMA_MODEL` to match the model you pulled

### .env File Not Loading

The `brain` CLI searches for `.env` in multiple locations automatically. If it's not loading:

1. **Check file exists in a searched location:**
   ```bash
   ls -la ~/.config/brain/.env  # Recommended location
   ls -la ~/.brain/.env         # Alternative location
   ls -la .env                  # Current directory
   ```

2. **Check file permissions (should be 600):**
   ```bash
   ls -l ~/.config/brain/.env
   # Should show: -rw------- (readable/writable by you only)

   # Fix if needed:
   chmod 600 ~/.config/brain/.env
   ```

3. **Verify file has correct format:**
   ```bash
   cat ~/.config/brain/.env | grep DIARY_PATH
   # Should show: DIARY_PATH=/your/path
   ```

## Security Best Practices

### Protect Your API Keys

Your `.env` file contains sensitive Azure API keys. Follow these practices:

1. **File Permissions:**
   ```bash
   chmod 600 ~/.config/brain/.env  # Only you can read/write
   ```

2. **Never Commit to Git:**
   ```bash
   # If you accidentally staged it:
   git rm --cached .env
   echo ".env" >> .gitignore
   ```

3. **Regular Key Rotation:**
   - Rotate Azure API keys periodically (every 90 days)
   - Update `.env` with new keys
   - Revoke old keys in Azure Portal

4. **Config Location Safety:**
   - `~/.config/brain/.env` is in your home directory (safe)
   - Current directory `.env` takes priority (be aware in shared directories)
   - Only load from trusted locations (the tool only searches these 3 paths)

### What the Tool Does

The `brain` CLI is designed with security in mind:

✅ Only searches 3 specific paths (no arbitrary file loading)
✅ Validates files are regular files (not directories or special files)
✅ Resolves symlinks to prevent path traversal
✅ Only reads text configuration (no code execution)
✅ Uses `python-dotenv` (standard, audited library)

### Data Privacy

All your data stays local:

- **Diary/Plan entries:** Stored in paths you specify (`DIARY_PATH`, `PLANNER_PATH`)
- **Cost tracking:** SQLite database in `~/.brain/costs.db` (your machine only)
- **No telemetry:** Nothing is sent except Azure OpenAI API calls (for LLM features)
- **No cloud sync:** You control where files are stored (use Obsidian Sync, etc. if desired)

## Next Steps

Once configured:

1. **Morning routine:**
   ```bash
   brain plan create today
   ```

2. **Evening routine:**
   ```bash
   brain diary create today
   # Write your reflection
   brain diary link today  # Generate backlinks
   ```

3. **Weekly review:**
   ```bash
   brain diary report 7
   brain diary patterns 7
   ```

4. **Track costs:**
   ```bash
   brain cost summary
   brain cost trends 30
   ```

## Updating

To update to the latest version:

```bash
uv tool install --force git+https://github.com/madebygps/second-brain.git
```

Your `.env` configuration file is not affected by updates.
