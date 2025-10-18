#!/bin/bash
# Setup script for CV and Cover Letter tailoring tools

echo "=========================================="
echo "CV Tools Setup"
echo "=========================================="
echo ""

# Check Python version
echo "[1/3] Checking Python version..."
python3 --version || { echo "Error: Python 3 not found"; exit 1; }

# Install requirements
echo ""
echo "[2/3] Installing Python dependencies..."
pip install -r requirements_cv_tools.txt || { echo "Error: Failed to install dependencies"; exit 1; }

# Verify installation
echo ""
echo "[3/3] Verifying installation..."
python3 -c "import docx; print('✓ python-docx installed successfully')" || { echo "✗ python-docx installation failed"; exit 1; }
python3 -c "import bs4; print('✓ beautifulsoup4 installed successfully')" || { echo "✗ beautifulsoup4 installation failed"; exit 1; }
python3 -c "import requests; print('✓ requests installed successfully')" || { echo "✗ requests installation failed"; exit 1; }

echo ""
echo "=========================================="
echo "✓ Setup complete!"
echo "=========================================="
echo ""
echo "You can now use the CV tailoring tools:"
echo "  - Command: /create_cv_&_cover <job_url>"
echo "  - Script: python3 create_tailored_application.py --job-text <file>"
echo ""
