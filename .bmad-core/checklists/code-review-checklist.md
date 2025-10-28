# Code Review Checklist

## 🚨 Critical Issues (Must Fix - Blocks Merge)

### Security
- [ ] No API keys, passwords, or tokens in code
- [ ] No SQL injection vulnerabilities (parameterized queries used)
- [ ] No command injection risks
- [ ] No XSS vulnerabilities in web outputs
- [ ] No hardcoded credentials or secrets
- [ ] Input validation present for user inputs
- [ ] Authentication/authorization properly implemented
- [ ] Sensitive data encrypted at rest and in transit

### Data Integrity
- [ ] No data loss risks
- [ ] Transactions used where appropriate
- [ ] Database constraints enforced
- [ ] Rollback mechanisms present for failures

### Testing
- [ ] All tests passing (100% pass rate)
- [ ] New functionality has test coverage
- [ ] Critical paths have tests
- [ ] Edge cases tested

### Breaking Changes
- [ ] No breaking API changes without migration path
- [ ] Backward compatibility maintained or documented
- [ ] Database migrations present if schema changed

## ⚠️ Warning Issues (Should Fix - Advisory)

### Code Quality
- [ ] Functions have clear, descriptive names
- [ ] Variables have meaningful names (not x, temp, data)
- [ ] No duplicated code (DRY principle)
- [ ] Functions are focused (single responsibility)
- [ ] Complex logic is commented/explained
- [ ] Magic numbers replaced with named constants

### Error Handling
- [ ] External API calls have error handling
- [ ] Database operations have error handling
- [ ] User-friendly error messages provided
- [ ] Errors logged with sufficient context
- [ ] No bare except: clauses (Python)
- [ ] Resources properly cleaned up (files, connections)

### Testing
- [ ] Test coverage adequate (aim for 90%+)
- [ ] Integration tests for API endpoints
- [ ] Unit tests for business logic
- [ ] Mock external dependencies
- [ ] Tests are deterministic (not flaky)

### Documentation
- [ ] Public APIs have docstrings
- [ ] Complex algorithms explained
- [ ] README updated if public interface changed
- [ ] CHANGELOG updated for user-facing changes
- [ ] Type hints present (Python) or types declared

### Performance
- [ ] No N+1 query problems
- [ ] Appropriate data structures used
- [ ] Reasonable algorithmic complexity
- [ ] Large operations are async/background jobs
- [ ] Pagination implemented for lists
- [ ] Caching used where appropriate

## 💡 Suggestions (Consider Improving)

### Code Organization
- [ ] Could functions be smaller/simpler?
- [ ] Is the abstraction level appropriate?
- [ ] Could this be more maintainable?
- [ ] Are there cleaner patterns available?

### Future Considerations
- [ ] Is this extensible for future requirements?
- [ ] Are there potential scalability issues?
- [ ] Could this configuration be externalized?
- [ ] Are there reusable components?

### Style
- [ ] Code follows project conventions
- [ ] Consistent formatting (use linter)
- [ ] Imports organized and minimal
- [ ] No commented-out code
- [ ] No TODO comments without tickets

## Review Process

1. **Pre-Review**
   - Read PR description
   - Understand context and requirements
   - Review linked issues/stories

2. **Security Pass**
   - Search for secrets/keys
   - Check injection vulnerabilities
   - Review authentication/authorization

3. **Quality Pass**
   - Naming conventions
   - Code organization
   - Error handling
   - Documentation

4. **Testing Pass**
   - Verify tests run and pass
   - Check coverage
   - Review test quality

5. **Performance Pass**
   - Algorithm complexity
   - Database queries
   - Resource usage

6. **Decision**
   - ✅ APPROVE: No critical issues
   - 🔄 REQUEST CHANGES: Critical or multiple warnings
   - 💬 COMMENT: Suggestions only
