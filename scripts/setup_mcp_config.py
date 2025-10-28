#!/usr/bin/env python3
"""
Setup script to generate .mcp.json from .mcp.json.template and .env file.

This script reads environment variables from .env and substitutes them
into .mcp.json.template to create .mcp.json with actual credentials.

Usage:
    python scripts/setup_mcp_config.py

Environment Variables Required:
    - LINKEDIN_COOKIE: Your LinkedIn li_at cookie value
    - GITHUB_TOKEN: Your GitHub personal access token (optional)
"""

import json
import os
import sys
from pathlib import Path
from string import Template


def load_env_file(env_path: Path) -> dict[str, str]:
    """
    Load environment variables from .env file.

    Args:
        env_path: Path to .env file

    Returns:
        Dictionary of environment variable key-value pairs
    """
    env_vars = {}

    if not env_path.exists():
        print(f"⚠️  Warning: {env_path} not found. Using system environment variables only.")
        return env_vars

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Parse KEY=VALUE
            if "=" in line:
                key, value = line.split("=", 1)
                # Remove quotes if present
                value = value.strip().strip('"').strip("'")
                env_vars[key.strip()] = value

    return env_vars


def generate_mcp_config(template_path: Path, output_path: Path, env_vars: dict[str, str]) -> None:
    """
    Generate .mcp.json from template and environment variables.

    Args:
        template_path: Path to .mcp.json.template
        output_path: Path to output .mcp.json
        env_vars: Dictionary of environment variables
    """
    # Read template
    with open(template_path) as f:
        template_content = f.read()

    # Substitute environment variables
    template = Template(template_content)

    # Merge with system environment variables and provide defaults for optional vars
    all_vars = {
        **os.environ,
        **env_vars,
        # Default values for optional variables
        "GITHUB_TOKEN": "",  # Optional - can be empty
    }

    try:
        result = template.substitute(all_vars)
    except KeyError as e:
        print(f"❌ Error: Missing required environment variable: {e}")
        print("\nRequired variables:")
        print("  - LINKEDIN_COOKIE (required)")
        print("\nOptional variables:")
        print("  - GITHUB_TOKEN (optional - leave empty if not using GitHub MCP)")
        print("\nPlease add them to your .env file or set as environment variables.")
        sys.exit(1)

    # Validate JSON
    try:
        json.loads(result)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Generated JSON is invalid: {e}")
        sys.exit(1)

    # Write output
    with open(output_path, "w") as f:
        f.write(result)

    # Set restrictive permissions (owner read/write only)
    output_path.chmod(0o600)

    print(f"✅ Generated {output_path}")
    print("   Permissions set to 600 (owner read/write only)")


def main():
    """Main entry point."""
    # Get project root (parent of scripts/)
    project_root = Path(__file__).parent.parent

    template_path = project_root / ".mcp.json.template"
    output_path = project_root / ".mcp.json"
    env_path = project_root / ".env"

    print("🔧 MCP Configuration Setup")
    print("=" * 50)

    # Check if template exists
    if not template_path.exists():
        print(f"❌ Error: Template not found: {template_path}")
        sys.exit(1)

    # Load environment variables
    print(f"📖 Loading environment from: {env_path}")
    env_vars = load_env_file(env_path)

    # Check for required variables
    linkedin_cookie = env_vars.get("LINKEDIN_COOKIE") or os.getenv("LINKEDIN_COOKIE")
    github_token = env_vars.get("GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")

    if not linkedin_cookie:
        print("⚠️  Warning: LINKEDIN_COOKIE not found")
    else:
        print(f"✅ Found LINKEDIN_COOKIE: {linkedin_cookie[:20]}...")

    if not github_token:
        print("⚠️  Warning: GITHUB_TOKEN not found (optional)")
    else:
        print(f"✅ Found GITHUB_TOKEN: {github_token[:20]}...")

    # Generate config
    print(f"\n🔨 Generating: {output_path}")
    generate_mcp_config(template_path, output_path, env_vars)

    print("\n✅ MCP configuration setup complete!")
    print("\n💡 Next steps:")
    print("   1. Verify .mcp.json was created")
    print("   2. Test MCP server connections")
    print("   3. Never commit .mcp.json to git (it's in .gitignore)")


if __name__ == "__main__":
    main()
