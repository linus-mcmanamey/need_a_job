# CV and Cover Letter Tailoring Tools

Automated tools for creating tailored CVs and cover letters based on job advertisements.

## Overview

This toolset helps you create customised application documents by:
1. Extracting job requirements from advertisements
2. Analysing your current CV and cover letter
3. Tailoring documents to match specific job requirements
4. Organising outputs in company-specific directories

## Quick Start

### 1. Install Dependencies

```bash
./setup_cv_tools.sh
```

Or manually:
```bash
pip install -r requirements_cv_tools.txt
```

### 2. Prepare Your Current Documents

Place your current CV and cover letter in:
- `/workspaces/Dev/need_a_new_job/current_cv_coverletter/Linus_McManamey_CV.docx`
- `/workspaces/Dev/need_a_new_job/current_cv_coverletter/Linus_McManamey_CL.docx`

### 3. Use the Claude Command

```bash
/create_cv_&_cover https://www.seek.com.au/job/12345678
```

Or use the Python script directly:

```bash
python3 create_tailored_application.py --job-text job_ad.txt
```

## Features

### Job Advertisement Analysis
- Extracts company name and job title
- Identifies key skills and technologies
- Parses responsibilities and requirements
- Extracts ATS-friendly keywords

### Document Tailoring
- **CV Customisation**:
  - Emphasises relevant experience
  - Incorporates job-specific keywords
  - Reorders sections for maximum impact
  - Maintains factual accuracy

- **Cover Letter Customisation**:
  - Personalised opening addressing specific role
  - Highlights matching achievements
  - Demonstrates company research
  - Professional Australian English tone

### Organisation
- Creates dated, company-specific directories
- Maintains consistent naming conventions
- Saves job information for reference
- Tracks application history

## Directory Structure

```
need_a_new_job/
├── current_cv_coverletter/          # Your master documents
│   ├── Linus_McManamey_CV.docx
│   └── Linus_McManamey_CL.docx
├── export_cv_cover_letter/          # Tailored outputs
│   ├── 2025-01-15_acme_corp_data_engineer/
│   │   ├── Linus_McManamey_CV.docx
│   │   ├── Linus_McManamey_CL.docx
│   │   └── job_info.json
│   └── 2025-01-16_tech_solutions_senior_developer/
│       ├── Linus_McManamey_CV.docx
│       ├── Linus_McManamey_CL.docx
│       └── job_info.json
├── create_tailored_application.py   # Main script
├── setup_cv_tools.sh                # Setup script
├── requirements_cv_tools.txt        # Python dependencies
└── .claude/commands/
    └── create_cv_&_cover.md         # Claude command definition
```

## Usage Examples

### Using Claude Command (Recommended)

```bash
# With job URL
/create_cv_&_cover https://www.seek.com.au/job/12345678

# Claude will:
# 1. Fetch the job advertisement
# 2. Analyse requirements
# 3. Read your current documents
# 4. Create tailored versions
# 5. Save to appropriate directory
```

### Using Python Script Directly

```bash
# Save job advertisement text to a file first
# Then run:
python3 create_tailored_application.py \
  --job-text job_advertisement.txt \
  --cv current_cv_coverletter/Linus_McManamey_CV.docx \
  --cover-letter current_cv_coverletter/Linus_McManamey_CL.docx
```

### Custom Output Directory

```bash
python3 create_tailored_application.py \
  --job-text job_ad.txt \
  --output-dir /path/to/custom/directory
```

## Australian English Writing Standards

The tools ensure all output follows Australian English conventions:

- **Spelling**: organisation, analyse, colour, centre
- **Date Format**: DD/MM/YYYY
- **Terminology**: CV (not resume), organisation (not company)
- **Tone**: Professional yet warm and approachable

## Writing Style Guidelines

### Professional Tone
- Formal business writing standards
- Clear, concise language
- Active voice preferred
- Strong action verbs

### Friendly Approach
- Warm, personable language
- Enthusiasm for opportunities
- Genuine interest in company
- Collaborative mindset

### Polite Expression
- Respectful phrasing
- Gratitude for consideration
- Positive framing
- Confident without arrogance

## Technical Requirements

### Python Dependencies
- `python-docx>=1.1.0` - MS Word document handling
- `beautifulsoup4>=4.12.0` - HTML parsing (for web scraping)
- `requests>=2.31.0` - HTTP requests
- `lxml>=5.1.0` - XML/HTML processing

### System Requirements
- Python 3.8 or higher
- MS Word documents (.docx format)
- Internet access (for fetching job advertisements)

## File Formats

### Input Documents
- **Format**: Microsoft Word 2007+ (.docx)
- **Location**: `current_cv_coverletter/`
- **Names**:
  - `Linus_McManamey_CV.docx`
  - `Linus_McManamey_CL.docx`

### Output Documents
- **Format**: Microsoft Word 2007+ (.docx)
- **Location**: `export_cv_cover_letter/YYYY-MM-DD_company_jobtitle/`
- **Names**: Same as input (maintains consistency)

### Job Information
- **Format**: JSON
- **Name**: `job_info.json`
- **Contents**:
  - Company name
  - Job title
  - Key skills identified
  - Requirements extracted
  - Keywords for ATS

## Troubleshooting

### Dependencies Not Installing

```bash
# Update pip first
pip install --upgrade pip

# Install dependencies with verbose output
pip install -v -r requirements_cv_tools.txt
```

### Documents Not Loading

Check:
1. File paths are correct
2. Files are .docx format (not .doc)
3. Documents are not password protected
4. You have read permissions

### Web Scraping Issues

If job advertisements cannot be fetched:
1. Copy the job text manually
2. Save to a text file
3. Use `--job-text` argument with file path

### Permission Errors

```bash
# Ensure scripts are executable
chmod +x setup_cv_tools.sh
chmod +x create_tailored_application.py

# Ensure output directory is writable
chmod -R 755 export_cv_cover_letter/
```

## Best Practices

### Before Applying
1. **Review Tailored Documents**: Always review before submission
2. **Verify Facts**: Ensure all information remains accurate
3. **Customise Further**: Add personal touches specific to the role
4. **Proofread**: Check for typos and formatting

### Maintaining Your Master Documents
1. **Update Regularly**: Keep current CV and cover letter up to date
2. **Add Achievements**: Include new accomplishments
3. **Refresh Skills**: Update technical skills list
4. **Review Language**: Ensure professional tone

### Application Tracking
1. **Use job_info.json**: Reference extracted job information
2. **Note Application Date**: Directory names include dates
3. **Track Responses**: Note interview requests
4. **Follow Up**: Use saved information for follow-up communications

## Security and Privacy

### Sensitive Information
- Never commit `.env` files with credentials
- Keep current CV/cover letter out of version control if contains personal data
- Review exported documents before sharing

### Git Configuration
The following are gitignored by default:
- `current_cv_coverletter/` - Your master documents
- `export_cv_cover_letter/` - Tailored outputs
- `.env` - Environment variables
- `*.docx` - MS Word documents

## Advanced Usage

### Customising the Script

Edit [create_tailored_application.py](create_tailored_application.py) to:
- Add additional skill keywords
- Modify extraction patterns
- Customise output formatting
- Add additional analysis features

### Modifying the Claude Command

Edit [.claude/commands/create_cv_&_cover.md](.claude/commands/create_cv_&_cover.md) to:
- Change writing style guidelines
- Adjust tone and formality
- Add additional instructions
- Customise workflow steps

### Batch Processing

Create multiple applications at once:

```bash
# Create a list of job text files
for job_file in jobs/*.txt; do
    python3 create_tailored_application.py --job-text "$job_file"
done
```

## Support and Feedback

### Getting Help
- Check this README first
- Review error messages carefully
- Verify all dependencies are installed
- Ensure file paths are correct

### Reporting Issues
Include:
- Error messages (full text)
- Python version (`python3 --version`)
- Installed package versions (`pip list`)
- Steps to reproduce

## Future Enhancements

Planned features:
- [ ] PDF export option
- [ ] LinkedIn profile integration
- [ ] Email draft generation
- [ ] Application tracking database
- [ ] Skills gap analysis
- [ ] Interview preparation notes
- [ ] Cover letter A/B testing
- [ ] ATS score prediction

## Related Tools

- **LinkedIn MCP Server**: Job search and profile management
- **fetch_linkedin_jobs.py**: Automated job searching
- **Job Tracking Markdown**: Application status tracking

## License

This toolset is for personal use in job applications. Ensure compliance with website terms of service when scraping job advertisements.

---

**Last Updated**: January 2025
**Maintained By**: Job Search Automation Project
**Status**: Active Development
