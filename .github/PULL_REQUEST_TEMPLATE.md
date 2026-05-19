## Summary

<!-- What does this PR change and why? Keep it under 5 sentences. -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Security fix
- [ ] Chore / refactor / tooling

## Checklist

- [ ] Tests added or updated (`pytest -x` green)
- [ ] Examples still build (`pytest tests/test_examples_build.py -v` green)
- [ ] Brand-leak guard passes (`pytest tests/test_no_internal_leaks_in_marketing.py` green)
- [ ] Docs updated if user-facing change (`mkdocs build --strict` green)
- [ ] No `core.*` imports introduced into the SDK (`pytest tests/test_zero_core_imports.py` green)
- [ ] Conventional-Commits PR title (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, etc.)
- [ ] Linked to issue or Discussion if applicable

## Test plan

<!-- How did you verify this change? Paste relevant pytest / curl / screenshot output. -->

## Reviewer notes

<!-- Anything specific you want the reviewer to look at? Edge cases you're worried about? -->
