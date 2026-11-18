# Project development rules

- This project uses Odoo 20.0 Community; custom modules belong in `addons/`.
- Follow [Odoo 20.0 Git guidelines](https://www.odoo.com/documentation/20.0/contributing/development/git_guidelines.html) for every new module and subsequent changes.
- Use `[TAG] technical_module: concise reason for change` commit subjects. Use `[ADD]` for new modules, `[FIX]` for fixes, `[IMP]` for improvements, and `[REF]` for refactors. Explain why in the commit body and include relevant ticket references. Keep unrelated module changes in separate commits.
- Target `20.0-DEV` with feature pull requests (GitHub's equivalent of merge requests).
- Every installable custom module must include meaningful Python unit tests in `tests/test_*.py`, imported by `tests/__init__.py`. Cover behavior, access rules where relevant, and regression cases for fixes. Do not add empty tests merely to satisfy CI.
- All pull requests targeting `20.0-DEV` must run the Odoo unit-test CI workflow. Do not disable tests or bypass failing checks.
- Use ECC unified-memory to recall context before work and save verified changes, decisions, validation, and remaining limitations after meaningful work. Never save credentials. Keep durable project rules here and setup instructions in README.md; memory is supporting context, not policy.
