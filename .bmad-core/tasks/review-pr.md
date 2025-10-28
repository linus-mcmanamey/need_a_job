# Review Pull Request Task

## Task Overview
Comprehensive pull request review with authority to approve or request changes.

## Inputs
- `pr_number`: Pull request number to review
- `repository`: Repository name (e.g., "owner/repo")

## Outputs
- PR review comments
- Approval/Request Changes decision
- Summary report

## Execution Steps

### Step 1: Fetch PR Details
```bash
# Get PR information
gh pr view {pr_number} --json title,body,author,headRefName,baseRefName,files
```

Parse and understand:
- PR title and description
- Linked issues/stories
- Author and context
- Changed files

### Step 2: Analyze Changed Files
```bash
# Get file changes
gh pr diff {pr_number}
```

Review each changed file:
- Understand purpose of changes
- Check for unintended modifications
- Note scope and complexity

### Step 3: Security Scan

Load `.bmad-core/checklists/security-checklist.md` and check:

**🚨 Critical Security Issues:**
- [ ] Search for exposed secrets: `grep -r "api[_-]key\|password\|secret\|token" --include="*.py" --include="*.js" --include="*.env*"`
- [ ] Check for SQL injection risks
- [ ] Check for command injection with os.system/subprocess
- [ ] Check for hardcoded credentials
- [ ] Verify input validation present

**Document any security findings with severity.**

### Step 4: Code Quality Review

Load `.bmad-core/checklists/code-review-checklist.md` and assess:

**Critical Issues:**
- [ ] Tests passing?
- [ ] Breaking changes handled?
- [ ] Data integrity preserved?

**Warnings:**
- [ ] Clear naming conventions?
- [ ] Error handling present?
- [ ] Code duplication?
- [ ] Documentation adequate?

**Suggestions:**
- [ ] Simplification opportunities?
- [ ] Performance improvements?
- [ ] Maintainability enhancements?

### Step 5: Test Validation

Check test status:
```bash
# View PR checks status
gh pr checks {pr_number}
```

Verify:
- [ ] All CI checks passing
- [ ] Test coverage adequate
- [ ] New tests for new functionality
- [ ] Integration tests appropriate

### Step 6: Generate Review Comments

For each issue found, create a structured comment:

```yaml
file: path/to/file.py
line: 45
severity: critical|warning|suggestion
issue: Description of the issue
example: |
  # Current code problem
  def bad_example():
      ...

  # Suggested fix
  def good_example():
      ...
```

### Step 7: Make Decision

Based on findings:

**APPROVE** ✅ if:
- No critical issues
- All tests passing
- Warnings are minor/acceptable
- Quality standards met

**REQUEST CHANGES** 🔄 if:
- Critical security issues present
- Tests failing
- Multiple significant warnings
- Breaking changes without migration

**COMMENT** 💬 if:
- Only suggestions
- Minor improvements recommended
- No blocking issues

### Step 8: Submit Review

```bash
# Approve PR
gh pr review {pr_number} --approve --body "Review summary..."

# Or request changes
gh pr review {pr_number} --request-changes --body "Issues found..."

# Or just comment
gh pr review {pr_number} --comment --body "Suggestions..."
```

### Step 9: Document Review

Create review summary with:
- Total files changed
- Critical issues found (count)
- Warnings found (count)
- Suggestions made (count)
- Decision and rationale
- Time to fix estimate (if changes requested)

## Review Template

```markdown
## PR Review Summary

**PR**: #{pr_number} - {title}
**Author**: {author}
**Reviewe: {reviewer_name}
**Date**: {date}

### Changes Overview
- Files changed: {count}
- Lines added: {added}
- Lines removed: {removed}

### Security Assessment
- 🚨 Critical Issues: {count}
- ⚠️ Security Warnings: {count}
- ✅ Security Status: {PASS/FAIL}

### Code Quality Assessment
- 🚨 Critical Issues: {count}
- ⚠️ Warnings: {count}
- 💡 Suggestions: {count}
- ✅ Quality Status: {PASS/CONCERNS/FAIL}

### Testing Assessment
- Test Status: {PASSING/FAILING}
- Coverage: {percentage}%
- New Tests: {count}
- ✅ Testing Status: {PASS/FAIL}

### Issues Found

{List each issue with severity, location, and fix suggestion}

### Decision: {APPROVE/REQUEST CHANGES/COMMENT}

**Rationale**: {Explanation of decision}

**Next Steps**: {What needs to happen next}

{If requesting changes:}
**Time to Fix**: {Estimate}
**Priority**: {Order of fixes}
```

## Example Usage

```bash
# User invokes
*review-pr 42

# Agent executes
1. Fetches PR #42 details
2. Analyzes 15 changed files
3. Finds 0 critical, 3 warnings, 5 suggestions
4. All tests passing
5. Submits APPROVE review
6. Outputs summary
```

## Error Handling

If PR not found:
- Verify PR number correct
- Check repository access
- Provide helpful error message

If tests not run yet:
- Note in review
- Recommend running tests
- Don't approve until verified

If unable to access files:
- Note access issues
- Review what's available
- Document limitations
