# Quick Reference: CV and Cover Letter Tools

## Quick Start

```bash
# 1. Install dependencies (first time only)
./setup_cv_tools.sh

# 2. Use the Claude command
/create_cv_&_cover <job_url>
```

## Command Syntax

### Claude Command
```bash
/create_cv_&_cover https://www.seek.com.au/job/12345678
```

### Python Script (Direct)
```bash
# Basic usage
python3 create_tailored_application.py --job-text job_ad.txt

# Full options
python3 create_tailored_application.py \
  --job-text job_ad.txt \
  --cv current_cv_coverletter/Linus_McManamey_CV.docx \
  --cover-letter current_cv_coverletter/Linus_McManamey_CL.docx \
  --output-dir export_cv_cover_letter
```

## File Locations

| Description | Path |
|-------------|------|
| **Master CV** | `current_cv_coverletter/Linus_McManamey_CV.docx` |
| **Master Cover Letter** | `current_cv_coverletter/Linus_McManamey_CL.docx` |
| **Tailored Outputs** | `export_cv_cover_letter/YYYY-MM-DD_company_position/` |
| **Python Script** | `create_tailored_application.py` |
| **Claude Command** | `.claude/commands/create_cv_&_cover.md` |
| **Dependencies** | `requirements_cv_tools.txt` |
| **Setup Script** | `setup_cv_tools.sh` |

## Common Tasks

### Update Master Documents
```bash
# Edit your current CV and cover letter
code current_cv_coverletter/Linus_McManamey_CV.docx
code current_cv_coverletter/Linus_McManamey_CL.docx
```

### List All Applications
```bash
ls -lh export_cv_cover_letter/
```

### View Job Information
```bash
cat export_cv_cover_letter/2025-01-15_company_position/job_info.json | jq
```

### Batch Process Multiple Jobs
```bash
for job_file in job_ads/*.txt; do
    python3 create_tailored_application.py --job-text "$job_file"
done
```

### Clean Up Old Applications
```bash
# Remove applications older than 90 days
find export_cv_cover_letter/ -type d -mtime +90 -exec rm -rf {} +
```

## Required Python Packages

| Package | Version | Purpose |
|---------|---------|---------|
| `python-docx` | >=1.1.0 | MS Word document handling |
| `beautifulsoup4` | >=4.12.0 | HTML parsing |
| `requests` | >=2.31.0 | HTTP requests |
| `lxml` | >=5.1.0 | XML/HTML processing |

Install all at once:
```bash
pip install -r requirements_cv_tools.txt
```

## Troubleshooting

### Issue: python-docx not installed
```bash
pip install python-docx
```

### Issue: Documents not found
```bash
# Check file paths
ls -lh current_cv_coverletter/
```

### Issue: Permission denied
```bash
# Make scripts executable
chmod +x setup_cv_tools.sh
chmod +x create_tailored_application.py
```

### Issue: Web scraping fails
```bash
# Manual fallback: Copy job text to file
cat > job_ad.txt << 'EOF'
[Paste job advertisement here]
EOF

python3 create_tailored_application.py --job-text job_ad.txt
```

## Output Structure

After running the tool, you'll get:

```
export_cv_cover_letter/
└── 2025-01-15_acme_corporation_data_engineer/
    ├── Linus_McManamey_CV.docx          # Tailored CV
    ├── Linus_McManamey_CL.docx          # Tailored cover letter
    └── job_info.json                     # Job analysis data
```

## Key Features

- ✅ Extracts job requirements automatically
- ✅ Analyses key skills and keywords
- ✅ Tailors CV and cover letter to match
- ✅ Uses Australian English
- ✅ Professional, friendly tone
- ✅ Organises by date and company
- ✅ Preserves factual accuracy
- ✅ ATS-friendly formatting

## Best Practices

1. **Keep master documents updated** - Your current CV should reflect latest achievements
2. **Review before submitting** - Always check tailored documents for accuracy
3. **Customise further** - Add personal touches specific to each role
4. **Track applications** - Use directory structure to organise submissions
5. **Update regularly** - Refresh skills and experience quarterly

## Help and Documentation

| Resource | Location |
|----------|----------|
| **Full Documentation** | [CV_TOOLS_README.md](CV_TOOLS_README.md) |
| **Example Usage** | [example_usage.sh](example_usage.sh) |
| **Command Definition** | [.claude/commands/create_cv_&_cover.md](.claude/commands/create_cv_&_cover.md) |
| **Python Script** | [create_tailored_application.py](create_tailored_application.py) |

## Related Tools

- **LinkedIn MCP Server** - Job search and profile scraping
- **fetch_linkedin_jobs.py** - Automated LinkedIn job search
- **Job tracking markdown** - Application status tracking

---

**Need help?** Run `./example_usage.sh` for interactive examples
