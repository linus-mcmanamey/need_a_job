# Approve Pull Request Task

## Task Overview
Approve a reviewed pull request and optionally merge it.

## Prerequisites
- PR has been reviewed
- All tests passing
- No critical issues found
- Quality standards met

## Inputs
- `pr_number`: Pull request number to approve
- `merge`: Optional boolean to merge after approval (default: false)
- `merge_method`: Optional merge method (merge|squash|rebase, default: squash)

## Outputs
- PR approval submitted
- Optional: PR merged
- Confirmation message

## Execution Steps

### Step 1: Verify PR Status

```bash
# Check PR current status
gh pr view {pr_number} --json state,isDraft,mergeable,reviewDecision

# Check CI status
gh pr checks {pr_number}
```

Verify:
- [ ] PR is open (not already merged/closed)
- [ ] PR is not a draft
- [ ] All CI checks passing
- [ ] No blocking reviews
- [ ] Branch is up to date

### Step 2: Final Security Check

Quick scan for critical issues:
```bash
# Check for secrets one more time
gh pr diff {pr_number} | grep -i "api[_-]key\|password\|secret\|token" | grep -v "\.env\.example"
```

If any secrets found:
- ❌ **STOP** - Do not approve
- Alert about security issue
- Request immediate fix

### Step 3: Verify Tests

```bash
# Ensure all checks green
gh pr checks {pr_number} --watch
```

Required:
- [ ] All required checks passing
- [ ] No failing tests
- [ ] Build successful

### Step 4: Submit Approval

```bash
# Approve the PR
gh pr review {pr_number} --approve --body "✅ **Code Review: APPROVED**

**Reviewed by**: Code Reviewer (Alex)
**Date**: $(date +%Y-%m-%d)

**Summary:**
- All quality standards met
- Tests passing ({test_count} tests)
- No security concerns
- Code is maintainable and well-documented

**Review Checklist:**
✅ Security scan passed
✅ Code quality verified
✅ Tests comprehensive
✅ Documentation adequate
✅ Performance acceptable

{additional_notes}

**Status**: Ready for merge
"
```

### Step 5: Optional Merge

If `merge=true`:

```bash
# Merge the PR
gh pr merge {pr_number} --{merge_method} --delete-branch

# Typical merge methods:
# --squash  : Squash commits into one (recommended for features)
# --merge   : Standard merge commit (preserves history)
# --rebase  : Rebase and merge (linear history)
```

### Step 6: Post-Approval Actions

After approval:
1. Add success label: `gh pr edit {pr_number} --add-label "approved"`
2. Notify in PR: "✅ Approved and ready for merge"
3. Log approval decision
4. Update tracking (if using project boards)

If merged:
1. Verify merge successful
2. Confirm branch deleted (if configured)
3. Update story/issue status (if linked)
4. Notify team/stakeholders

## Approval Criteria

### Must Have (Required)
- ✅ All tests passing
- ✅ No critical security issues
- ✅ No breaking changes without migration
- ✅ Code review completed
- ✅ Acceptance criteria met

### Should Have (Warnings Acceptable)
- ⚠️ Code coverage adequate (90%+ preferred)
- ⚠️ Documentation present
- ⚠️ No code duplication
- ⚠️ Performance acceptable

### Nice to Have (Not Blocking)
- 💡 Optimal code structure
- 💡 Advanced optimizations
- 💡 Future extensibility

## Edge Cases

### Draft PR
If PR is draft:
- Don't approve
- Message: "Convert to ready for review first"

### Failing Tests
If tests failing:
- Don't approve
- Message: "Fix failing tests before approval"
- Link to test results

### Merge Conflicts
If merge conflicts:
- Don't approve
- Message: "Resolve merge conflicts with base branch"
- Provide guidance

### Missing Review
If no review completed yet:
- Run review first: `*review-pr {pr_number}`
- Then approve if passing

## Output Format

```markdown
✅ **Pull Request #${pr_number} APPROVED**

**Title**: {pr_title}
**Author**: {author}
**Approved by**: Code Reviewer (Alex)
**Date**: {date}

**Review Status**:
- Security: ✅ PASS
- Quality: ✅ PASS
- Tests: ✅ PASS ({count} passing)
- Documentation: ✅ PASS

**Merge Status**: {merged/ready for merge}
{if merged:}
- Merge Method: {method}
- Merge Commit: {sha}
- Branch Deleted: {yes/no}

**Next Steps**: {what happens next}
```

## Example Usage

```bash
# Approve only
*approve-pr 42

# Approve and merge with squash
*approve-pr 42 --merge --method squash
```

## Safety Guards

**Never approve if**:
- Secrets/API keys exposed
- Tests failing
- Critical security vulnerability
- Breaking changes without migration
- Merge conflicts present

**Always verify**:
- Review completed first
- All checks green
- Author addressed previous feedback
- PR description complete
