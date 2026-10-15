---
name: tdd
description: "Write unit tests first using strict Test-Driven Development (TDD) following Robert C. Martin's Clean Code rules (Three Laws of TDD, F.I.R.S.T., Given-When-Then). Use when: writing unit tests before an implementation, preparing a feature via tests-first workflow, working from an issue or task description where the later implementation consists solely of making the tests pass, or when the user mentions TDD, test-driven, tests first, red-green-refactor, or Uncle Bob testing."
---

# Test-Driven Development (Robert C. Martin)

Write the unit tests for an upcoming implementation — nothing else. The subsequent implementation step will consist **solely** of making these tests pass. There will be no requirements discussion, no extra hardening, no second test pass. Therefore:

> **Making the tests green must be equivalent to the feature being complete.** Write tests that cover the full behavior described in the issue/task — happy paths, edge cases, boundary values, error cases, and every acceptance criterion. Anything not covered by a test will not be implemented.

## When to Use

- The user asks for unit tests before an implementation exists (tests-first / TDD workflow)
- Working from an issue or task description whose implementation will follow in a separate step
- The user mentions TDD, test-driven development, red-green-refactor, or Robert C. Martin / Uncle Bob testing

## Procedure

### 1. Before writing any code

1. **Read and understand the issue/task described in the prompt.** Identify every observable behavior and acceptance criterion. If requirements are ambiguous, ask before writing tests.
2. **Make sure you are on the correct feature branch.** Check with `git branch --show-current` / `git status` and switch if necessary. Never write tests on the wrong branch.
3. **Locate the project's unit test folder** and read the production code, configs, and documentation needed to understand the design.

### 2. Scope restrictions — strictly enforced

- **Only operate in the project's unit test folder.** Every file you create or modify lives there.
- **Treat everything outside the project's unit test folder as READ-ONLY.** You may read production code, configs, and documentation to understand the design, but you must never modify, move, or delete anything outside the test folder.
- **Write no production code.** No implementation, no stubs in production files, no "quick fixes" to make a test compile — if a test fails because production code is missing or wrong, that failing test is the deliverable.

### 3. The Three Laws of TDD

1. Write no production code until you have a failing unit test for it. (In this workflow: production code is out of scope entirely — the output is the failing tests.)
2. Write no more of a unit test than is sufficient to fail — a compilation error counts as a failure.
3. Write no more production code than is sufficient to pass. (For the later implementation step: it exists only to turn the red tests green.)

### 4. Test quality rules (Clean Code, ch. 9)

- **F.I.R.S.T.**: tests are **F**ast (milliseconds), **I**ndependent (no order dependence, no shared mutable state), **R**epeatable (pass in any environment; no unmocked network, filesystem, or clock), **S**elf-validating (boolean pass/fail, no manual inspection), **T**imely (written before the production code — that is this step).
- **One concept per test**; aim for **one assert per test**. Each test name describes a single, specific behavior.
- Structure every test as **Given–When–Then** (build–operate–check): set up state, execute the behavior under test, assert the outcome.
- Test code is as important as production code — keep it **clean and readable**: intention-revealing test names, no magic values, minimal setup noise (extract fixtures/builders where useful, inside the test folder).
- **Coverage for completeness**: since green tests = done feature, enumerate the behaviors from the issue first and map each to at least one test. Include failure modes and boundary conditions, not just the happy path.

### 5. Done means

- All tests live in the project's unit test folder; nothing outside it was changed.
- The new tests fail (or fail to compile) against the current code — that failure is the specification for the implementation step.
- Existing tests are untouched and still pass.
- Report: which branch you are on, the list of behaviors covered, and which tests fail and why.
