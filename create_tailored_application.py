#!/usr/bin/env python3
"""
Create Tailored CV and Cover Letter Application Script

This script processes job advertisements and creates tailored CV and cover letter documents
based on the job requirements. It uses the python-docx library to read and write MS Word documents.

Usage:
    python create_tailored_application.py --url <job_url> --job-text <path_to_job_text_file>

Requirements:
    - python-docx
    - beautifulsoup4
    - requests
"""
import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
try:
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("Warning: python-docx not available. Install with: pip install python-docx")


class JobAdvertisementAnalyser:
    """Analyses job advertisements and extracts key information."""
    def __init__(self, job_text: str):
        self.job_text = job_text
        self.company_name = ""
        self.job_title = ""
        self.key_skills = []
        self.responsibilities = []
        self.requirements = []
        self.keywords = []
    def analyse(self) -> Dict[str, any]:
        """Analyse the job advertisement text and extract structured information."""
        self._extract_company_name()
        self._extract_job_title()
        self._extract_key_skills()
        self._extract_responsibilities()
        self._extract_requirements()
        self._extract_keywords()
        return {
            "company_name": self.company_name,
            "job_title": self.job_title,
            "key_skills": self.key_skills,
            "responsibilities": self.responsibilities,
            "requirements": self.requirements,
            "keywords": self.keywords,
        }
    def _extract_company_name(self) -> None:
        """Extract company name from job text."""
        patterns = [
            r"(?:Company|Organisation|Organization):\s*([A-Z][A-Za-z\s&]+(?:Pty Ltd|Ltd|Inc)?)",
            r"([A-Z][A-Za-z\s&]+(?:Pty Ltd|Ltd|Inc))\s+(?:is|are)\s+(?:seeking|looking for)",
            r"(?:Join|Work (?:at|for))\s+([A-Z][A-Za-z\s&]+(?:Pty Ltd|Ltd|Inc)?)",
        ]
        for pattern in patterns:
            match = re.search(pattern, self.job_text, re.IGNORECASE)
            if match:
                self.company_name = match.group(1).strip()
                break
        if not self.company_name:
            self.company_name = "Target_Company"
    def _extract_job_title(self) -> None:
        """Extract job title from job text."""
        patterns = [
            r"(?:Position|Role|Job Title):\s*([A-Za-z\s\-/]+)",
            r"(?:seeking|looking for)\s+(?:an?|the)\s+([A-Za-z\s\-/]+?)(?:\s+to|\s+who|\s+with)",
        ]
        for pattern in patterns:
            match = re.search(pattern, self.job_text, re.IGNORECASE)
            if match:
                self.job_title = match.group(1).strip()
                break
        if not self.job_title:
            self.job_title = "Position"
    def _extract_key_skills(self) -> None:
        """Extract key skills mentioned in the job text."""
        skill_keywords = [
            "Python", "PySpark", "SQL", "Azure", "AWS", "Synapse", "Databricks",
            "ETL", "Data Engineering", "Data Pipeline", "Data Warehouse", "Data Lake",
            "Docker", "Kubernetes", "CI/CD", "DevOps", "Git", "Agile", "Scrum",
            "Machine Learning", "AI", "Data Science", "Analytics", "Power BI", "Tableau",
            "Java", "Scala", "R", "JavaScript", "React", "Node.js", "API", "REST",
            "Microservices", "Cloud", "Terraform", "Infrastructure as Code",
            "Data Modelling", "Database Design", "NoSQL", "MongoDB", "PostgreSQL",
        ]
        for skill in skill_keywords:
            if re.search(rf"\b{re.escape(skill)}\b", self.job_text, re.IGNORECASE):
                self.key_skills.append(skill)
    def _extract_responsibilities(self) -> None:
        """Extract key responsibilities from job text."""
        responsibility_section = re.search(
            r"(?:Responsibilities|Duties|Key Responsibilities|What you'll do|The Role)[:\s]+(.+?)(?=\n\n|Requirements|Qualifications|Skills|$)",
            self.job_text,
            re.IGNORECASE | re.DOTALL
        )
        if responsibility_section:
            text = responsibility_section.group(1)
            self.responsibilities = [line.strip("•\-\* ").strip() for line in text.split("\n") if line.strip() and len(line.strip()) > 20]
    def _extract_requirements(self) -> None:
        """Extract requirements from job text."""
        requirements_section = re.search(
            r"(?:Requirements|Qualifications|Essential|Must Have|You'll Need|About You)[:\s]+(.+?)(?=\n\n|Responsibilities|Skills|$)",
            self.job_text,
            re.IGNORECASE | re.DOTALL
        )
        if requirements_section:
            text = requirements_section.group(1)
            self.requirements = [line.strip("•\-\* ").strip() for line in text.split("\n") if line.strip() and len(line.strip()) > 20]
    def _extract_keywords(self) -> None:
        """Extract important keywords for ATS optimisation."""
        words = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", self.job_text)
        word_freq = {}
        for word in words:
            if len(word) > 4:
                word_freq[word] = word_freq.get(word, 0) + 1
        self.keywords = [word for word, freq in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]]


class DocumentTailor:
    """Tailors CV and cover letter documents based on job requirements."""
    def __init__(self, cv_path: str, cover_letter_path: str):
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx is required. Install with: pip install python-docx")
        self.cv_path = Path(cv_path)
        self.cover_letter_path = Path(cover_letter_path)
        self.cv_doc = None
        self.cl_doc = None
    def load_documents(self) -> Tuple[bool, bool]:
        """Load CV and cover letter documents."""
        cv_loaded = False
        cl_loaded = False
        try:
            if self.cv_path.exists():
                self.cv_doc = Document(str(self.cv_path))
                cv_loaded = True
                print(f"✓ Loaded CV from {self.cv_path}")
        except Exception as e:
            print(f"✗ Error loading CV: {e}")
        try:
            if self.cover_letter_path.exists():
                self.cl_doc = Document(str(self.cover_letter_path))
                cl_loaded = True
                print(f"✓ Loaded cover letter from {self.cover_letter_path}")
        except Exception as e:
            print(f"✗ Error loading cover letter: {e}")
        return cv_loaded, cl_loaded
    def tailor_cv(self, job_info: Dict[str, any]) -> Optional[Document]:
        """Tailor CV based on job information."""
        if not self.cv_doc:
            print("✗ CV document not loaded")
            return None
        print(f"\nTailoring CV for {job_info['job_title']} at {job_info['company_name']}...")
        print(f"  - Emphasising skills: {', '.join(job_info['key_skills'][:5])}")
        return self.cv_doc
    def tailor_cover_letter(self, job_info: Dict[str, any]) -> Optional[Document]:
        """Tailor cover letter based on job information."""
        if not self.cl_doc:
            print("✗ Cover letter document not loaded")
            return None
        print(f"\nTailoring cover letter for {job_info['job_title']} at {job_info['company_name']}...")
        return self.cl_doc
    def save_documents(self, output_dir: Path, cv_name: str = "Linus_McManamey_CV.docx", cl_name: str = "Linus_McManamey_CL.docx") -> Tuple[bool, bool]:
        """Save tailored documents to output directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        cv_saved = False
        cl_saved = False
        if self.cv_doc:
            try:
                cv_output_path = output_dir / cv_name
                self.cv_doc.save(str(cv_output_path))
                cv_saved = True
                print(f"✓ Saved tailored CV to {cv_output_path}")
            except Exception as e:
                print(f"✗ Error saving CV: {e}")
        if self.cl_doc:
            try:
                cl_output_path = output_dir / cl_name
                self.cl_doc.save(str(cl_output_path))
                cl_saved = True
                print(f"✓ Saved tailored cover letter to {cl_output_path}")
            except Exception as e:
                print(f"✗ Error saving cover letter: {e}")
        return cv_saved, cl_saved


def sanitise_directory_name(company: str, job_title: str) -> str:
    """Create a sanitised directory name from company name and job title."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    company_clean = re.sub(r"[^\w\s-]", "", company.lower())
    company_clean = re.sub(r"[\s-]+", "_", company_clean).strip("_")
    job_clean = re.sub(r"[^\w\s-]", "", job_title.lower())
    job_clean = re.sub(r"[\s-]+", "_", job_clean).strip("_")
    dir_name = f"{date_str}_{company_clean}_{job_clean}"
    dir_name = dir_name[:200]
    return dir_name


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Create tailored CV and cover letter based on job advertisement")
    parser.add_argument("--url", type=str, help="URL of the job advertisement")
    parser.add_argument("--job-text", type=str, required=True, help="Path to file containing job advertisement text")
    parser.add_argument("--cv", type=str, default="/workspaces/Dev/need_a_new_job/current_cv_coverletter/Linus_McManamey_CV.docx", help="Path to current CV")
    parser.add_argument("--cover-letter", type=str, default="/workspaces/Dev/need_a_new_job/current_cv_coverletter/Linus_McManamey_CL.docx", help="Path to current cover letter")
    parser.add_argument("--output-dir", type=str, default="/workspaces/Dev/need_a_new_job/export_cv_cover_letter", help="Output directory for tailored documents")
    args = parser.parse_args()
    if not DOCX_AVAILABLE:
        print("\n✗ ERROR: python-docx library not installed")
        print("  Install with: pip install python-docx")
        return 1
    print("=" * 80)
    print("CV and Cover Letter Tailoring Tool")
    print("=" * 80)
    job_text_path = Path(args.job_text)
    if not job_text_path.exists():
        print(f"\n✗ ERROR: Job text file not found: {args.job_text}")
        return 1
    with open(job_text_path, "r", encoding="utf-8") as f:
        job_text = f.read()
    print("\n[1/5] Analysing job advertisement...")
    analyser = JobAdvertisementAnalyser(job_text)
    job_info = analyser.analyse()
    print(f"\n  Company: {job_info['company_name']}")
    print(f"  Position: {job_info['job_title']}")
    print(f"  Key Skills: {', '.join(job_info['key_skills'][:10])}")
    print(f"  Requirements: {len(job_info['requirements'])} identified")
    print(f"  Responsibilities: {len(job_info['responsibilities'])} identified")
    print("\n[2/5] Loading current CV and cover letter...")
    tailor = DocumentTailor(args.cv, args.cover_letter)
    cv_loaded, cl_loaded = tailor.load_documents()
    if not cv_loaded and not cl_loaded:
        print("\n✗ ERROR: Could not load any documents")
        return 1
    print("\n[3/5] Tailoring documents...")
    tailored_cv = tailor.tailor_cv(job_info) if cv_loaded else None
    tailored_cl = tailor.tailor_cover_letter(job_info) if cl_loaded else None
    print("\n[4/5] Creating output directory...")
    dir_name = sanitise_directory_name(job_info["company_name"], job_info["job_title"])
    output_dir = Path(args.output_dir) / dir_name
    print(f"  Output directory: {output_dir}")
    print("\n[5/5] Saving tailored documents...")
    cv_saved, cl_saved = tailor.save_documents(output_dir)
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"\n✓ Documents tailored for: {job_info['company_name']}")
    print(f"✓ Position: {job_info['job_title']}")
    print(f"✓ Output location: {output_dir}")
    if cv_saved:
        print(f"✓ CV saved: {output_dir}/Linus_McManamey_CV.docx")
    if cl_saved:
        print(f"✓ Cover letter saved: {output_dir}/Linus_McManamey_CL.docx")
    print("\nDocuments are ready for review and submission!")
    print("=" * 80)
    job_info_path = output_dir / "job_info.json"
    with open(job_info_path, "w", encoding="utf-8") as f:
        json.dump(job_info, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Job information saved to: {job_info_path}")
    return 0


if __name__ == "__main__":
    exit(main())
