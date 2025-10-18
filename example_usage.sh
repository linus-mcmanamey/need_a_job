#!/bin/bash
# Example usage script for CV and Cover Letter tailoring tools

echo "=========================================="
echo "CV Tailoring Tools - Example Usage"
echo "=========================================="
echo ""

# Example 1: Using Claude Command
echo "Example 1: Using Claude Command (Recommended)"
echo "----------------------------------------------"
echo ""
echo "In Claude Code, type:"
echo ""
echo "  /create_cv_&_cover https://www.seek.com.au/job/12345678"
echo ""
echo "Claude will:"
echo "  1. Fetch the job advertisement from the URL"
echo "  2. Analyse the job requirements"
echo "  3. Read your current CV and cover letter"
echo "  4. Create tailored versions"
echo "  5. Save them to a company-specific directory"
echo ""
echo "Press Enter to see Example 2..."
read -r

# Example 2: Manual job text extraction
echo ""
echo "Example 2: Manual Job Text Extraction"
echo "----------------------------------------------"
echo ""
echo "1. Copy the job advertisement text from the website"
echo "2. Save it to a text file:"
echo ""
echo "  cat > job_ad.txt << 'EOF'"
echo "  [Paste job advertisement text here]"
echo "  EOF"
echo ""
echo "3. Run the Python script:"
echo ""
echo "  python3 create_tailored_application.py --job-text job_ad.txt"
echo ""
echo "Press Enter to see Example 3..."
read -r

# Example 3: Full command with all options
echo ""
echo "Example 3: Full Command with All Options"
echo "----------------------------------------------"
echo ""
echo "python3 create_tailored_application.py \\"
echo "  --job-text job_advertisement.txt \\"
echo "  --cv current_cv_coverletter/Linus_McManamey_CV.docx \\"
echo "  --cover-letter current_cv_coverletter/Linus_McManamey_CL.docx \\"
echo "  --output-dir export_cv_cover_letter"
echo ""
echo "Press Enter to see Example 4..."
read -r

# Example 4: Batch processing
echo ""
echo "Example 4: Batch Processing Multiple Jobs"
echo "----------------------------------------------"
echo ""
echo "# Create job text files in a directory"
echo "mkdir -p job_ads"
echo "# Save each job ad as: job_ads/company_position.txt"
echo ""
echo "# Process all jobs at once"
echo "for job_file in job_ads/*.txt; do"
echo '    echo "Processing: $job_file"'
echo '    python3 create_tailored_application.py --job-text "$job_file"'
echo "done"
echo ""
echo "Press Enter to see Example 5..."
read -r

# Example 5: Checking outputs
echo ""
echo "Example 5: Checking Your Tailored Documents"
echo "----------------------------------------------"
echo ""
echo "# List all created applications"
echo "ls -lh export_cv_cover_letter/"
echo ""
echo "# View job information for a specific application"
echo "cat export_cv_cover_letter/2025-01-15_company_position/job_info.json"
echo ""
echo "# Open documents in your default applications"
echo "open export_cv_cover_letter/2025-01-15_company_position/Linus_McManamey_CV.docx"
echo "open export_cv_cover_letter/2025-01-15_company_position/Linus_McManamey_CL.docx"
echo ""
echo ""

echo "=========================================="
echo "For more information, see:"
echo "  - CV_TOOLS_README.md"
echo "  - .claude/commands/create_cv_&_cover.md"
echo "=========================================="
echo ""
