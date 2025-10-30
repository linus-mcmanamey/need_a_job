# 🚀 Setup Guide

Complete guide to setting up the Job Application Automation System.

---

## Quick Start

The fastest way to get started:

```bash
git clone <repository-url>
cd need_a_job
make first-time-setup
```

The interactive wizard will guide you through the entire setup process.

---

## Setup Modes

### 1. First Time Setup (Recommended)
```bash
make first-time-setup
```

**What it does:**
- Runs an interactive wizard to collect all configuration
- Validates inputs in real-time
- Tests API connections
- Creates the `.env` file
- Sets up required directories
- Starts all Docker services
- Verifies everything is working

**When to use:**
- First time setting up the project
- Want a guided experience
- Want to configure all features

### 2. Quick Setup
```bash
make quick-setup
```

**What it does:**
- Collects only essential variables (Claude API key)
- Skips optional features
- Creates minimal `.env` file
- Starts services

**When to use:**
- Want to get started quickly
- Will configure optional features later
- Already familiar with the system

### 3. Validate Setup
```bash
make validate-setup
```

**What it does:**
- Checks existing `.env` file
- Validates required variables are present
- Reports missing or incomplete configuration

**When to use:**
- Troubleshooting setup issues
- Verifying configuration after manual edits
- Before starting services

---

## Configuration Variables

### Essential (Required)

#### `ANTHROPIC_API_KEY`
- **Required:** Yes
- **Description:** Claude API key for all AI agents
- **Where to get:** https://console.anthropic.com/
- **Format:** `sk-ant-api03-xxxxx...`
- **Validation:** Must start with `sk-ant-api`

**Why it's needed:** Powers all the AI agents that match jobs, tailor CVs, write cover letters, and make decisions.

---

### Core Features (Recommended)

#### `LINKEDIN_LI_AT_COOKIE`
- **Required:** No (but recommended for job discovery)
- **Description:** LinkedIn authentication cookie (`li_at`)
- **Where to get:**
  1. Log into LinkedIn in your browser
  2. Open DevTools (F12)
  3. Go to Application > Cookies > linkedin.com
  4. Copy the `li_at` cookie value
- **Format:** `AQEDATxxxxx...`
- **Note:** Expires approximately every 30 days

**Why it's needed:** Enables automated job discovery from LinkedIn. Without this, you'll need to manually add jobs.

#### `SENDER_EMAIL`
- **Required:** No (but needed for submissions)
- **Description:** Your Gmail address
- **Format:** `your.email@gmail.com`
- **Validation:** Must be valid email format

**Why it's needed:** Used to send job applications via email.

#### `SENDER_PASSWORD`
- **Required:** No (but needed for submissions)
- **Description:** Gmail App Password (NOT your regular Gmail password)
- **Where to get:**
  1. Enable 2FA on your Gmail account
  2. Go to Google Account → Security → App Passwords - https://myaccount.google.com/apppasswords?
  3. Generate App Password for "Mail"
  4. Copy the 16-character password (remove spaces)
- **Format:** `xxxxxxxxxxxx` (16 characters, no spaces)
- **Note:** More info at https://support.google.com/accounts/answer/185833

**Why it's needed:** Allows the system to send emails on your behalf. Must use App Password, not your regular password.

---

### Optional Settings

#### `GITHUB_TOKEN`
- **Required:** No
- **Description:** GitHub Personal Access Token
- **Where to get:** https://github.com/settings/tokens
- **Format:** `ghp_xxxxx...` or `github_pat_xxxxx...`
- **Scopes needed:** `repo`, `read:org`

**Why it's optional:** Only needed if you want GitHub integration via MCP server.

#### `MIN_SALARY_AUD_PER_DAY`
- **Required:** No
- **Default:** `800`
- **Description:** Minimum acceptable daily rate (AUD)
- **Format:** Integer (e.g., `800`)

**Why it's optional:** Has a sensible default. Change if your requirements differ.

#### `MAX_SALARY_AUD_PER_DAY`
- **Required:** No
- **Default:** `1500`
- **Description:** Maximum salary expectation (AUD per day)
- **Format:** Integer (e.g., `1500`)

**Why it's optional:** Has a default. Used for filtering and validation.

#### `JOB_MATCH_THRESHOLD`
- **Required:** No
- **Default:** `0.70`
- **Description:** Minimum matching score (0.0 - 1.0) for a job to proceed
- **Format:** Float between 0.0 and 1.0
- **Lower = more permissive, Higher = more selective**

**Why it's optional:** Default of 0.70 (70%) works well for most cases.

#### `APPROVAL_MODE`
- **Required:** No
- **Default:** `true`
- **Description:** Require manual approval before submitting applications
- **Format:** `true` or `false`

**Why it's optional:** Defaults to `true` for safety. Set to `false` for fully automated submissions (not recommended initially).

#### `DRY_RUN`
- **Required:** No
- **Default:** `false`
- **Description:** Test mode - generates CVs/CLs but doesn't send applications
- **Format:** `true` or `false`

**Why it's optional:** Use `true` for testing the system safely.

---

### Auto-Generated (No Input Required)

These are set automatically with sensible defaults:

- **Application Settings:** `APP_ENV=development`, `LOG_LEVEL=INFO`
- **Database:** `DUCKDB_PATH=data/job_applications.duckdb`
- **Redis:** `REDIS_URL=redis://redis:6379` (container networking)
- **Email:** `SMTP_SERVER=smtp.gmail.com`, `SMTP_PORT=587`
- **Directories:** `CV_TEMPLATE_DIR`, `OUTPUT_DIR`, `LOG_DIR`
- **Thresholds:** Duplicate detection, rate limits, etc.
- **Workers:** Queue names, worker count

You can override any of these by editing `.env` directly after setup.

---

## Setup Flow

### Interactive Wizard Flow

1. **Welcome Screen**
   - Shows what the wizard will do
   - Checks for existing `.env` file

2. **Essential Configuration**
   - Collects Claude API key
   - Validates format
   - Cannot skip (required for system to work)

3. **Core Features** (unless quick mode)
   - Asks about LinkedIn cookie
   - Asks about email credentials
   - Each can be skipped if not ready

4. **Optional Settings** (if requested)
   - GitHub token
   - Salary ranges
   - Thresholds and modes
   - All can be skipped

5. **Review & Confirm**
   - Shows summary of all settings
   - Sensitive values are masked
   - Final chance to cancel

6. **Write Configuration**
   - Creates `.env` file
   - Organized by category
   - Includes comments

7. **Test Connections** (optional)
   - Tests Claude API connectivity
   - Reports success/failure

8. **Success & Next Steps**
   - Shows access URLs
   - Explains how to start using

---

## After Setup

### Start the Application

Services are started automatically, but you can control them:

```bash
# View status
make docker-ps

# View logs
make docker-logs

# Restart services
make docker-restart

# Stop services
make docker-down
```

### Access the Interfaces

- **Gradio UI:** http://localhost:7860
- **API Docs:** http://localhost:8000/api/docs
- **RQ Dashboard:** http://localhost:9181

### Modify Configuration

```bash
# Edit .env directly
nano .env

# Or re-run wizard
make first-time-setup

# Validate changes
make validate-setup

# Apply changes
make docker-restart
```

---

## Troubleshooting

### Setup Issues

**"Docker not found"**
- Install Docker Desktop from https://www.docker.com/products/docker-desktop
- Verify with `docker --version`

**"Invalid API key"**
- Verify key starts with `sk-ant-api`
- Get new key from https://console.anthropic.com/
- Re-run setup

**"Setup wizard exits immediately"**
- Check Docker is running: `docker ps`
- Try pulling image manually: `docker pull python:3.11-slim`

### Configuration Issues

**Want to skip a configuration step?**
- Just press Enter when prompted
- You can add it later by:
  - Re-running `make first-time-setup`, or
  - Editing `.env` manually

**Made a mistake during setup?**
- Just re-run `make first-time-setup`
- Choose "Yes" when asked to overwrite

**Need to change settings later?**
- Edit `.env` file directly
- Or re-run setup wizard
- Then restart: `make docker-restart`

---

## Security Best Practices

1. **Never commit `.env` file**
   - Already in `.gitignore`
   - Contains sensitive credentials

2. **Use App Passwords**
   - Never use your actual Gmail password
   - Always generate App Passwords

3. **Rotate credentials regularly**
   - LinkedIn cookies expire ~30 days
   - Consider rotating API keys periodically

4. **Start with Approval Mode**
   - Keep `APPROVAL_MODE=true` initially
   - Only disable after you trust the system

5. **Test with Dry Run**
   - Use `DRY_RUN=true` first
   - Verify CVs/CLs look good
   - Then enable real submissions

---

## Advanced Configuration

### Custom Docker Configuration

Edit `docker-compose.yml` to customize:
- Port mappings
- Resource limits
- Volume mounts
- Network settings

### Custom YAML Configs

Edit files in `config/` directory:
- `search.yaml` - Job search criteria
- `agents.yaml` - Agent behavior
- `platforms.yaml` - Platform settings
- `similarity.yaml` - Duplicate detection

### Scaling Workers

```bash
# Scale to 5 workers
make docker-scale-workers N=5
```

---

## Getting Help

- **Documentation:** See `README.md` and `docs/` directory
- **Common Issues:** See Troubleshooting section in `README.md`
- **Logs:** `make docker-logs` or `logs/` directory
- **Health Check:** `make docker-health`

---

## Next Steps After Setup

1. **Add your CV and cover letter templates**
   - Place in `current_cv_coverletter/` directory
   - Use `.docx` format

2. **Configure job search criteria**
   - Edit `config/search.yaml`
   - Set your keywords, technologies, preferences

3. **Test the system**
   - Start with `DRY_RUN=true`
   - Review generated documents
   - Enable real submissions when ready

4. **Monitor the pipeline**
   - Use Gradio UI at http://localhost:7860
   - Watch jobs flow through agents
   - Review and approve applications

---

**Ready to start?** Run `make first-time-setup` and let the wizard guide you!
