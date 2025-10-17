#!/usr/bin/env python3
"""
Fetch LinkedIn job listings using the LinkedIn MCP server.
This script will search for data engineer contract jobs and extract URLs.
"""

import json
import subprocess
import sys
from pathlib import Path

# Add the project directory to path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir / "linkedin-mcp-server"))

def search_linkedin_jobs(keywords: str, location: str = "Australia"):
    """
    Search for jobs on LinkedIn using the MCP server.

    Args:
        keywords: Job search keywords (e.g., "Data Engineer contract")
        location: Location to search in

    Returns:
        List of job dictionaries with URLs and details
    """
    # Load environment
    env_file = project_dir / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith("LINKEDIN_COOKIE="):
                    cookie = line.split("=", 1)[1].strip()
                    break

    # Import the LinkedIn scraper
    try:
        from linkedin_scraper import JobSearch, actions
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")

        # Create driver
        driver = webdriver.Chrome(options=chrome_options)

        # Login with cookie
        driver.get("https://www.linkedin.com")
        driver.add_cookie({
            "name": "li_at",
            "value": cookie,
            "domain": ".linkedin.com"
        })

        # Search for jobs
        print(f"Searching for: {keywords} in {location}")

        # Navigate to jobs page
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
        driver.get(search_url)

        # Wait for page to load
        import time
        time.sleep(5)

        # Extract job listings
        jobs = []
        job_cards = driver.find_elements("css selector", ".job-card-container")

        for card in job_cards[:20]:  # Limit to first 20
            try:
                title_elem = card.find_element("css selector", ".job-card-list__title")
                company_elem = card.find_element("css selector", ".job-card-container__company-name")
                location_elem = card.find_element("css selector", ".job-card-container__metadata-item")
                link_elem = card.find_element("css selector", "a")

                job = {
                    "title": title_elem.text,
                    "company": company_elem.text,
                    "location": location_elem.text,
                    "url": link_elem.get_attribute("href")
                }
                jobs.append(job)
                print(f"Found: {job['title']} at {job['company']}")
            except Exception as e:
                print(f"Error parsing job card: {e}")
                continue

        driver.quit()
        return jobs

    except ImportError as e:
        print(f"Error importing LinkedIn scraper: {e}")
        print("The LinkedIn MCP server tools are not directly importable.")
        return []
    except Exception as e:
        print(f"Error during job search: {e}")
        return []

def main():
    """Main function to search for jobs."""
    searches = [
        ("Data Engineer contract", "Australia"),
        ("Data Engineer remote contract", "Australia"),
        ("Data Engineer", "Hobart Tasmania"),
    ]

    all_jobs = []

    for keywords, location in searches:
        print(f"\n{'='*60}")
        print(f"Searching: {keywords} in {location}")
        print(f"{'='*60}\n")

        jobs = search_linkedin_jobs(keywords, location)
        all_jobs.extend(jobs)

    # Save results
    output_file = project_dir / "linkedin_jobs_results.json"
    with open(output_file, "w") as f:
        json.dump(all_jobs, f, indent=2)

    print(f"\n\nTotal jobs found: {len(all_jobs)}")
    print(f"Results saved to: {output_file}")

    return all_jobs

if __name__ == "__main__":
    jobs = main()
