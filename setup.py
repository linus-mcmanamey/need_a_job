#!/usr/bin/env python3
"""
Job Application Automation - First Time Setup
Interactive setup script for configuring environment variables.
No external dependencies required - uses only Python stdlib.
"""

import sys
import re
import argparse
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse


# ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"


# Configuration categories
ESSENTIAL_VARS = {"ANTHROPIC_API_KEY": {"description": "Claude API Key (required for all AI agents)", "help_url": "https://console.anthropic.com/", "example": "sk-ant-api03-xxxxx", "validator": "api_key", "required": True}}

CORE_VARS = {
    "LINKEDIN_LI_AT_COOKIE": {
        "description": "LinkedIn li_at cookie (for job discovery)",
        "help_url": "Instructions: Open LinkedIn > DevTools (F12) > Application > Cookies > li_at",
        "example": "AQEDATxxxxx...",
        "validator": "non_empty",
        "required": False,
        "skip_message": "You can add this later to enable LinkedIn job discovery",
    },
    "SENDER_EMAIL": {
        "description": "Gmail address (for sending applications)",
        "help_url": "Use your Gmail address",
        "example": "your.email@gmail.com",
        "validator": "email",
        "required": False,
        "skip_message": "You can add this later to enable email submissions",
    },
    "SENDER_PASSWORD": {
        "description": "Gmail App Password (NOT your Gmail password)",
        "help_url": "https://support.google.com/accounts/answer/185833",
        "example": "xxxx-xxxx-xxxx-xxxx (remove spaces)",
        "validator": "non_empty",
        "required": False,
        "skip_message": "You can add this later to enable email submissions",
    },
}

OPTIONAL_VARS = {
    "GITHUB_TOKEN": {
        "description": "GitHub Personal Access Token (for GitHub MCP server)",
        "help_url": "https://github.com/settings/tokens",
        "example": "ghp_xxxxx",
        "validator": "github_token",
        "required": False,
        "skip_message": "Optional - only needed for GitHub integration",
    },
    "MIN_SALARY_AUD_PER_DAY": {"description": "Minimum daily rate (AUD)", "example": "800", "validator": "number", "default": "800", "required": False},
    "MAX_SALARY_AUD_PER_DAY": {"description": "Maximum daily rate (AUD)", "example": "1500", "validator": "number", "default": "1500", "required": False},
    "JOB_MATCH_THRESHOLD": {"description": "Job matching threshold (0.0 - 1.0)", "example": "0.70", "validator": "float_range", "default": "0.70", "required": False},
    "APPROVAL_MODE": {"description": "Require manual approval before submission (true/false)", "example": "true", "validator": "boolean", "default": "true", "required": False},
    "DRY_RUN": {"description": "Dry run mode - no actual applications sent (true/false)", "example": "false", "validator": "boolean", "default": "false", "required": False},
}

# Auto-generated variables with defaults
AUTO_VARS = {
    "APP_ENV": "development",
    "LOG_LEVEL": "INFO",
    "REDIS_URL": "redis://redis:6379",
    "REDIS_HOST": "redis",
    "REDIS_PORT": "6379",
    "DUCKDB_PATH": "data/job_applications.duckdb",
    "SMTP_SERVER": "smtp.gmail.com",
    "SMTP_PORT": "587",
    "SMTP_USE_TLS": "true",
    "MCP_CONFIG_PATH": ".mcp.json",
    "ENABLE_AUTO_DISCOVERY": "false",
    "DISCOVERY_INTERVAL_HOURS": "1",
    "LINKEDIN_MAX_RESULTS": "50",
    "SEEK_MAX_RESULTS": "50",
    "INDEED_MAX_RESULTS": "50",
    "RQ_QUEUE_NAMES": "discovery_queue,pipeline_queue,submission_queue",
    "WORKER_COUNT": "3",
    "DUPLICATE_TIER1_THRESHOLD": "0.90",
    "DUPLICATE_TIER2_THRESHOLD": "0.90",
    "DUPLICATE_LOOKBACK_DAYS": "30",
    "CV_TEMPLATE_DIR": "current_cv_coverletter",
    "OUTPUT_DIR": "export_cv_cover_letter",
    "ALT_OUTPUT_DIR": "second_folder",
    "LOG_DIR": "logs",
    "LOG_ROTATION": "1 day",
    "LOG_RETENTION": "30 days",
    "LOG_FORMAT": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    "LINKEDIN_RATE_LIMIT": "100",
    "SEEK_RATE_LIMIT": "50",
    "INDEED_RATE_LIMIT": "50",
    "CLAUDE_RATE_LIMIT": "50",
    "DEBUG": "false",
}


class SetupWizard:
    """Interactive setup wizard for first-time configuration."""

    def __init__(self, quick_mode: bool = False, validate_only: bool = False):
        self.quick_mode = quick_mode
        self.validate_only = validate_only
        self.env_values: Dict[str, str] = {}
        self.env_file_path = Path.cwd() / ".env"

    def run(self):
        """Main execution flow."""
        self.print_header()

        if self.validate_only:
            return self.validate_existing_env()

        if self.env_file_path.exists():
            if not self.confirm_overwrite():
                print(f"\n{Colors.YELLOW}Setup cancelled. Your existing .env file was not modified.{Colors.RESET}")
                return False

        # Collect configuration
        if not self.collect_essential_vars():
            print(f"\n{Colors.RED}❌ Setup cancelled. Essential variables are required.{Colors.RESET}")
            return False

        if not self.quick_mode:
            self.collect_core_vars()
            if self.ask_yes_no("Configure optional settings?", default=False):
                self.collect_optional_vars()

        # Add auto-generated vars
        self.env_values.update(AUTO_VARS)

        # Review and confirm
        if not self.review_configuration():
            print(f"\n{Colors.YELLOW}Setup cancelled.{Colors.RESET}")
            return False

        # Write .env file
        self.write_env_file()

        # Test connections
        if self.ask_yes_no("Test connections now?", default=True):
            self.test_connections()

        self.print_success()
        return True

    def print_header(self):
        """Print welcome header."""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 70}")
        print("🤖  Job Application Automation - First Time Setup")
        print(f"{'=' * 70}{Colors.RESET}\n")

        if self.quick_mode:
            print(f"{Colors.YELLOW}Quick mode: Configuring essential variables only{Colors.RESET}\n")
        elif self.validate_only:
            print(f"{Colors.BLUE}Validation mode: Checking existing .env file{Colors.RESET}\n")
        else:
            print("This wizard will help you configure your environment.\n")

    def confirm_overwrite(self) -> bool:
        """Ask user if they want to overwrite existing .env file."""
        print(f"{Colors.YELLOW}⚠️  An .env file already exists!{Colors.RESET}")
        return self.ask_yes_no("Do you want to overwrite it?", default=False)

    def collect_essential_vars(self) -> bool:
        """Collect essential variables - cannot skip."""
        print(f"\n{Colors.BOLD}{Colors.GREEN}📋 ESSENTIAL CONFIGURATION{Colors.RESET}")
        print(f"{Colors.GRAY}These settings are required to run the application.{Colors.RESET}\n")

        for var_name, config in ESSENTIAL_VARS.items():
            value = self.prompt_for_variable(var_name, config)
            if not value:
                return False
            self.env_values[var_name] = value

        return True

    def collect_core_vars(self):
        """Collect core variables - can skip but recommended."""
        print(f"\n{Colors.BOLD}{Colors.GREEN}🔑 CORE FEATURES{Colors.RESET}")
        print(f"{Colors.GRAY}These settings enable job discovery and application submission.{Colors.RESET}\n")

        for var_name, config in CORE_VARS.items():
            if self.ask_yes_no(f"Configure {var_name}?", default=True):
                value = self.prompt_for_variable(var_name, config)
                if value:
                    self.env_values[var_name] = value
            else:
                print(f"{Colors.GRAY}  ℹ️  {config.get('skip_message', 'Skipped')}{Colors.RESET}")

    def collect_optional_vars(self):
        """Collect optional variables."""
        print(f"\n{Colors.BOLD}{Colors.GREEN}⚙️  OPTIONAL SETTINGS{Colors.RESET}")
        print(f"{Colors.GRAY}Advanced configuration options.{Colors.RESET}\n")

        for var_name, config in OPTIONAL_VARS.items():
            if self.ask_yes_no(f"Configure {var_name}?", default=False):
                value = self.prompt_for_variable(var_name, config)
                if value:
                    self.env_values[var_name] = value
                elif config.get("default"):
                    self.env_values[var_name] = config["default"]
            elif config.get("default"):
                self.env_values[var_name] = config["default"]

    def prompt_for_variable(self, var_name: str, config: Dict) -> Optional[str]:
        """Prompt user for a single variable with validation."""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{var_name}{Colors.RESET}")
        print(f"{Colors.GRAY}  {config['description']}{Colors.RESET}")

        if "help_url" in config:
            print(f"{Colors.GRAY}  📖 {config['help_url']}{Colors.RESET}")

        if "example" in config:
            print(f"{Colors.GRAY}  Example: {config['example']}{Colors.RESET}")

        if config.get("default"):
            print(f"{Colors.GRAY}  Default: {config['default']}{Colors.RESET}")

        max_attempts = 3
        for attempt in range(max_attempts):
            value = input(f"{Colors.BOLD}→ {Colors.RESET}").strip()

            # Use default if empty and default exists
            if not value and config.get("default"):
                value = config["default"]
                print(f"{Colors.GRAY}  Using default: {value}{Colors.RESET}")

            # Allow empty for optional fields
            if not value and not config.get("required"):
                if config.get("skip_message"):
                    print(f"{Colors.GRAY}  ℹ️  {config['skip_message']}{Colors.RESET}")
                return None

            # Validate
            validator = config.get("validator")
            if validator:
                is_valid, error_message = self.validate_input(value, validator)
                if is_valid:
                    print(f"{Colors.GREEN}  ✓ Valid{Colors.RESET}")
                    return value
                else:
                    print(f"{Colors.RED}  ✗ {error_message}{Colors.RESET}")
                    if attempt < max_attempts - 1:
                        print(f"{Colors.GRAY}  Please try again ({max_attempts - attempt - 1} attempts remaining){Colors.RESET}")
            else:
                return value

        if config.get("required"):
            print(f"{Colors.RED}  ✗ Max attempts reached. This field is required.{Colors.RESET}")
            return None

        print(f"{Colors.YELLOW}  ⚠️  Skipping this field.{Colors.RESET}")
        return None

    def validate_input(self, value: str, validator_type: str) -> Tuple[bool, str]:
        """Validate input based on type."""
        validators = {
            "api_key": self.validate_api_key,
            "email": self.validate_email,
            "non_empty": self.validate_non_empty,
            "github_token": self.validate_github_token,
            "number": self.validate_number,
            "float_range": self.validate_float_range,
            "boolean": self.validate_boolean,
            "url": self.validate_url,
        }

        validator_func = validators.get(validator_type)
        if validator_func:
            return validator_func(value)

        return True, ""

    def validate_api_key(self, value: str) -> Tuple[bool, str]:
        """Validate Anthropic API key format."""
        if not value.startswith("sk-ant-api"):
            return False, "API key should start with 'sk-ant-api'"
        if len(value) < 20:
            return False, "API key seems too short"
        return True, ""

    def validate_email(self, value: str) -> Tuple[bool, str]:
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, value):
            return False, "Invalid email format"
        return True, ""

    def validate_non_empty(self, value: str) -> Tuple[bool, str]:
        """Validate non-empty string."""
        if not value or not value.strip():
            return False, "Value cannot be empty"
        return True, ""

    def validate_github_token(self, value: str) -> Tuple[bool, str]:
        """Validate GitHub token format."""
        if not value.startswith("ghp_") and not value.startswith("github_pat_"):
            return False, "GitHub token should start with 'ghp_' or 'github_pat_'"
        if len(value) < 20:
            return False, "Token seems too short"
        return True, ""

    def validate_number(self, value: str) -> Tuple[bool, str]:
        """Validate number."""
        try:
            int(value)
            return True, ""
        except ValueError:
            return False, "Must be a valid number"

    def validate_float_range(self, value: str) -> Tuple[bool, str]:
        """Validate float in range 0.0 - 1.0."""
        try:
            num = float(value)
            if 0.0 <= num <= 1.0:
                return True, ""
            return False, "Must be between 0.0 and 1.0"
        except ValueError:
            return False, "Must be a valid number"

    def validate_boolean(self, value: str) -> Tuple[bool, str]:
        """Validate boolean."""
        if value.lower() in ["true", "false"]:
            return True, ""
        return False, "Must be 'true' or 'false'"

    def validate_url(self, value: str) -> Tuple[bool, str]:
        """Validate URL format."""
        try:
            result = urlparse(value)
            if all([result.scheme, result.netloc]):
                return True, ""
            return False, "Invalid URL format"
        except Exception:
            return False, "Invalid URL format"

    def review_configuration(self) -> bool:
        """Show configuration summary and ask for confirmation."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}📝 CONFIGURATION SUMMARY{Colors.RESET}\n")

        # Essential
        if any(k in self.env_values for k in ESSENTIAL_VARS.keys()):
            print(f"{Colors.BOLD}Essential:{Colors.RESET}")
            for key in ESSENTIAL_VARS.keys():
                if key in self.env_values:
                    value = self.mask_sensitive_value(key, self.env_values[key])
                    print(f"  {Colors.GREEN}✓{Colors.RESET} {key} = {value}")

        # Core
        core_configured = [k for k in CORE_VARS.keys() if k in self.env_values]
        if core_configured:
            print(f"\n{Colors.BOLD}Core Features:{Colors.RESET}")
            for key in core_configured:
                value = self.mask_sensitive_value(key, self.env_values[key])
                print(f"  {Colors.GREEN}✓{Colors.RESET} {key} = {value}")

        # Optional
        optional_configured = [k for k in OPTIONAL_VARS.keys() if k in self.env_values]
        if optional_configured:
            print(f"\n{Colors.BOLD}Optional:{Colors.RESET}")
            for key in optional_configured:
                value = self.mask_sensitive_value(key, self.env_values[key])
                print(f"  {Colors.GREEN}✓{Colors.RESET} {key} = {value}")

        # Auto-generated
        print(f"\n{Colors.GRAY}+ {len(AUTO_VARS)} auto-generated variables with defaults{Colors.RESET}")

        return self.ask_yes_no("\nSave this configuration?", default=True)

    def mask_sensitive_value(self, key: str, value: str) -> str:
        """Mask sensitive values for display."""
        sensitive_keys = ["KEY", "PASSWORD", "TOKEN", "COOKIE", "SECRET"]
        if any(s in key.upper() for s in sensitive_keys):
            if len(value) <= 8:
                return "***"
            return f"{value[:4]}...{value[-4:]}"
        return value

    def write_env_file(self):
        """Write configuration to .env file."""
        print(f"\n{Colors.BLUE}Writing .env file...{Colors.RESET}")

        lines = [
            "# Job Application Automation System - Environment Configuration",
            "# Generated by setup wizard",
            f"# Date: {self._get_timestamp()}",
            "",
            "# =============================================================================",
            "# Essential Configuration",
            "# =============================================================================",
        ]

        # Essential vars
        for key in ESSENTIAL_VARS.keys():
            if key in self.env_values:
                lines.append(f"{key}={self.env_values[key]}")

        # Core vars
        core_configured = [k for k in CORE_VARS.keys() if k in self.env_values]
        if core_configured:
            lines.extend(["", "# =============================================================================", "# Core Features", "# ============================================================================="])
            for key in core_configured:
                lines.append(f"{key}={self.env_values[key]}")

        # Optional vars
        optional_configured = [k for k in OPTIONAL_VARS.keys() if k in self.env_values]
        if optional_configured:
            lines.extend(["", "# =============================================================================", "# Optional Settings", "# ============================================================================="])
            for key in optional_configured:
                lines.append(f"{key}={self.env_values[key]}")

        # Auto-generated vars
        lines.extend(["", "# =============================================================================", "# Auto-Generated Configuration (Defaults)", "# ============================================================================="])
        for key, value in AUTO_VARS.items():
            lines.append(f"{key}={value}")

        # Write file
        with open(self.env_file_path, "w") as f:
            f.write("\n".join(lines))

        print(f"{Colors.GREEN}✓ .env file created successfully{Colors.RESET}")

    def test_connections(self):
        """Test configured connections."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}🔍 TESTING CONNECTIONS{Colors.RESET}\n")

        # Test Claude API
        if "ANTHROPIC_API_KEY" in self.env_values:
            self._test_claude_api()

        print(f"\n{Colors.GRAY}Note: Redis and other services will be tested when Docker starts{Colors.RESET}")

    def _test_claude_api(self):
        """Test Claude API connection."""
        print("Testing Claude API...", end=" ")
        try:
            import urllib.request
            import json

            api_key = self.env_values["ANTHROPIC_API_KEY"]

            # Simple API check - just verify key format and make a minimal request
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json.dumps({"model": "claude-3-haiku-20240307", "max_tokens": 10, "messages": [{"role": "user", "content": "hi"}]}).encode("utf-8"),
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    print(f"{Colors.GREEN}✓ Connected{Colors.RESET}")
                else:
                    print(f"{Colors.YELLOW}⚠️  Status {response.status}{Colors.RESET}")
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                print(f"{Colors.RED}✗ Invalid API key{Colors.RESET}")
            elif "429" in error_msg:
                print(f"{Colors.YELLOW}⚠️  Rate limited (key is valid){Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}⚠️  Could not test: {error_msg[:50]}{Colors.RESET}")

    def validate_existing_env(self) -> bool:
        """Validate existing .env file."""
        if not self.env_file_path.exists():
            print(f"{Colors.RED}✗ No .env file found{Colors.RESET}")
            print("\nRun 'make first-time-setup' to create one.")
            return False

        print(f"Validating {self.env_file_path}...\n")

        # Read existing .env
        env_vars = {}
        with open(self.env_file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()

        # Check essential vars
        print(f"{Colors.BOLD}Essential Variables:{Colors.RESET}")
        all_essential_present = True
        for key in ESSENTIAL_VARS.keys():
            if key in env_vars and env_vars[key]:
                print(f"  {Colors.GREEN}✓{Colors.RESET} {key}")
            else:
                print(f"  {Colors.RED}✗{Colors.RESET} {key} - Missing or empty")
                all_essential_present = False

        # Check core vars
        print(f"\n{Colors.BOLD}Core Variables:{Colors.RESET}")
        for key in CORE_VARS.keys():
            if key in env_vars and env_vars[key]:
                print(f"  {Colors.GREEN}✓{Colors.RESET} {key}")
            else:
                print(f"  {Colors.YELLOW}○{Colors.RESET} {key} - Not configured")

        if all_essential_present:
            print(f"\n{Colors.GREEN}✓ Configuration is valid{Colors.RESET}")
            return True
        else:
            print(f"\n{Colors.RED}✗ Configuration is incomplete{Colors.RESET}")
            print("\nRun 'make first-time-setup' to reconfigure.")
            return False

    def print_success(self):
        """Print success message with next steps."""
        print(f"\n{Colors.GREEN}{Colors.BOLD}{'=' * 70}")
        print("✅  Setup Complete!")
        print(f"{'=' * 70}{Colors.RESET}\n")

        print(f"{Colors.BOLD}Next Steps:{Colors.RESET}")
        print(f"  1. {Colors.CYAN}Start the application:{Colors.RESET}")
        print("     make docker-up")
        print(f"\n  2. {Colors.CYAN}Access the interfaces:{Colors.RESET}")
        print("     • Gradio UI:    http://localhost:7860")
        print("     • API Docs:     http://localhost:8000/api/docs")
        print("     • RQ Dashboard: http://localhost:9181")
        print(f"\n  3. {Colors.CYAN}View logs:{Colors.RESET}")
        print("     make docker-logs")

        print(f"\n{Colors.GRAY}Need help? Check the README.md or run 'make help'{Colors.RESET}\n")

    def ask_yes_no(self, question: str, default: bool = True) -> bool:
        """Ask a yes/no question."""
        suffix = "[Y/n]" if default else "[y/N]"
        while True:
            response = input(f"{question} {suffix}: ").strip().lower()
            if not response:
                return default
            if response in ["y", "yes"]:
                return True
            if response in ["n", "no"]:
                return False
            print(f"{Colors.YELLOW}Please answer 'yes' or 'no'{Colors.RESET}")

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Job Application Automation - First Time Setup")
    parser.add_argument("--quick", action="store_true", help="Quick setup - essential variables only")
    parser.add_argument("--validate", action="store_true", help="Validate existing .env file")

    args = parser.parse_args()

    try:
        wizard = SetupWizard(quick_mode=args.quick, validate_only=args.validate)
        success = wizard.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Setup cancelled by user.{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
