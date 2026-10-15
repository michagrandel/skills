---
name: clean-code
description: "Apply Robert C. Martin's Clean Code principles when writing, reviewing, or refactoring code in any programming language (Python, C++, C#, Java, etc.). Use when: writing new code, doing code reviews, refactoring legacy code, reducing code smells, improving naming, functions, error handling, tests, or class design, or when the user mentions clean code, Uncle Bob, readability, or maintainability."
---

# Clean Code Principles (Robert C. Martin)

Language-agnostic summary of the principles from *Clean Code: A Handbook of Agile Software Craftsmanship*. Apply them when writing, reviewing, or refactoring code — regardless of the programming language.

## When to Use

- Writing new code (apply from the start, not as an afterthought)
- Reviewing pull requests / code (use the [review checklist](./references/review-checklist.md))
- Refactoring legacy or smelly code
- Diagnosing why code is hard to read, test, or change

## Guiding Attitude

- **The Boy Scout Rule**: Leave the code cleaner than you found it. Small continuous improvements beat big rewrites.
- **Code is read far more often than it is written.** Optimize for the reader, not the writer.
- **Clean code does one thing well** and reads like well-written prose: focused, expressive, free of surprises.
- **Later equals never.** Clean up messes now; "we'll fix it later" means it stays.

## Procedure

1. **Identify the context**: new code, code review, or refactoring.
2. **Apply the relevant principle groups below** (naming, functions, comments, formatting, error handling, boundaries, tests, classes, SOLID, smells).
3. **For reviews**: walk through [review-checklist.md](./references/review-checklist.md) and report findings grouped by principle, with concrete suggestions.
4. **For refactoring**: change one thing at a time, keep tests green, prefer many small safe steps over one big edit.
5. **Respect the existing codebase style** where it deliberately deviates — consistency within a project also serves readability.

---

## 1. Meaningful Names

- **Use intention-revealing names.** A name should answer: why it exists, what it does, how it is used — without requiring a comment.
- **Avoid disinformation**: no names that hide meaning, reuse well-known terms incorrectly, or differ only subtly from another name.
- **Make meaningful distinctions**: don't add noise words (`Info`, `Data`, `a`, `the`) to force different names.
- **Use pronounceable and searchable names**; avoid single letters except for short loop counters.
- **No encodings**: no type/prefix notations (e.g., Hungarian notation), no member prefixes — modern tools make them obsolete.
- **Class names**: nouns or noun phrases. **Method names**: verbs or verb phrases.
- **Pick one word per concept** and use it consistently (`fetch`, `retrieve`, `get` — choose one).
- **Don't pun**: avoid using the same word for two different purposes.
- **Use solution-domain names** (patterns, algorithms) where readers are programmers; **use problem-domain names** otherwise.
- **Add context when needed**, but **don't add gratuitous context** (don't prefix every name with the app name).

## 2. Functions

- **Small.** The first rule of functions is that they should be small. The second rule is that they should be smaller than that. Aim for a handful of lines; hardly ever more than ~20.
- **Do one thing.** A function does one thing, does it well, and does it only. If you can meaningfully extract another function from it, it does more than one thing.
- **One level of abstraction per function.** Don't mix high-level orchestration with low-level detail.
- **The Stepdown Rule**: code should read like a top-down narrative — each function is followed by the functions at the next level down.
- **Few arguments**: ideal is 0, then 1, then 2. Avoid 3+; group related arguments into a concept (object/struct) instead.
- **No flag arguments**: a boolean parameter means the function does two things — split it.
- **No side effects**: a function should do what its name promises and nothing else (no hidden state changes).
- **Command–Query Separation**: a function either does something or answers something, not both.
- **Prefer exceptions over error return codes**; extract try/catch blocks into their own functions.
- **Don't Repeat Yourself (DRY)**: duplication is the root of much evil — extract it.

## 3. Comments

- **The proper use of comments is to compensate for our failure to express ourselves in code.** Every comment represents a small failure — minimize them.
- **Comments lie**: code changes, comments rot. Keeping them accurate costs energy better spent making the code clear.
- **Explain yourself in code instead**: rename, extract functions, introduce explanatory variables.
- **Good comments**: legal notices, explanation of *intent* (why, not what), clarification of opaque library calls, warnings of consequences, TODOs, amplification of seemingly-trivial-but-important decisions.
- **Bad comments** (delete or rewrite): mumbling/redundancy, misleading comments, mandated boilerplate comments, journal/change-log comments (version control does this), noise comments, position markers, closing-brace comments, commented-out code.
- **Never comment out code** — delete it. Version control remembers.

## 4. Formatting

- **Consistency is king.** Agree on one style per project and apply it everywhere, automatically (formatter/linter) if possible.
- **Think of the newspaper metaphor**: the name at the top, high-level concepts first, details increasing as you go down.
- **Vertical density**: lines that belong together should appear together. **Vertical distance**: concepts that are related should be kept close; callers above callees where the language allows.
- **Vertical openness**: blank lines separate concepts.
- **Horizontal formatting**: keep lines short; use whitespace to group related things and to make precedence visible.
- **Indentation** reflects scope — never collapse functions to one-liners.
- **Instance variables** at the top of the class; **dependent functions** close to their callers.

## 5. Objects and Data Structures

- **Hide implementation behind abstraction**: expose behavior, not internal structure.
- **Data/object anti-symmetry**: objects hide data and expose behavior; data structures expose data and have no significant behavior. Choose deliberately which one you need.
- **Law of Demeter** ("talk to friends, not strangers"): a method should only call methods of itself, its parameters, objects it creates, and its direct components — avoid `a.b().c().d()` train wrecks.
- **Tell, don't ask**: tell objects what to do rather than querying their state and acting on it.
- **Data Transfer Objects**: simple structures with no behavior are fine for crossing boundaries — but don't give them fake "business logic".

## 6. Error Handling

- **Use exceptions rather than return codes** — error codes clutter the caller and are easily ignored.
- **Write your try-catch-finally statement first** when writing code that could throw; it defines the scope of expected behavior.
- **Provide context with exceptions**: an error message should state the intent, the operation that failed, and the relevant values.
- **Define exception types by the caller's needs**, not by the thrower's internals; wrap third-party exceptions at boundaries.
- **Don't return null**: it forces every caller to check. Return an empty collection or a special-case object instead.
- **Don't pass null** as an argument; make it unrepresentable where the language allows.
- **Define the normal flow** using the Special Case pattern instead of scattering null/error checks.
- Error handling is **one thing** — a function that handles errors should do nothing else.

## 7. Boundaries

- **Wrap third-party code** behind your own interface so library changes don't ripple through your codebase, and so the API matches *your* needs.
- **Write learning tests** for third-party APIs: small tests that verify your understanding and detect breaking upgrades.
- **Use adapters** where an external interface doesn't fit your model.
- **Define boundaries for code that doesn't exist yet** with your own interface, keeping unknowns at the edge.

## 8. Unit Tests

- **The Three Laws of TDD**:
  1. Write no production code until you have a failing unit test.
  2. Write no more of a test than is sufficient to fail (compile errors count).
  3. Write no more production code than is sufficient to pass.
- **Test code is as important as production code.** Keep it clean — readability matters even more in tests.
- **F.I.R.S.T.**: tests are **F**ast, **I**ndependent (no order dependence), **R**epeatable (any environment), **S**elf-validating (pass/fail, no manual log reading), **T**imely (written just before/with the production code).
- **One assert per test** (as a goal) and **a single concept per test**.
- **Given–When–Then** (build–operate–check) structure keeps tests readable.
- **Dirty tests are worse than no tests** — they become unmaintainable and get deleted, taking your safety net with them.

## 9. Classes

- **Small.** Classes are measured by **responsibilities**, not lines of code. If you can't derive a precise name, it's too big.
- **Single Responsibility Principle**: a class should have one, and only one, reason to change.
- **High cohesion**: methods should use the class's fields; when cohesion drops, split the class.
- **Organize for change**: changes should extend behavior by adding code, not by modifying existing code (see Open/Closed).
- **Isolate from change**: depend on abstractions, not concretions (see Dependency Inversion).

## 10. SOLID Principles (Robert C. Martin)

- **S — Single Responsibility**: one reason to change per class/module.
- **O — Open/Closed**: open for extension, closed for modification.
- **L — Liskov Substitution**: subtypes must be usable wherever their base type is expected, without breaking behavior.
- **I — Interface Segregation**: many small, client-specific interfaces beat one fat general-purpose interface; don't force clients to depend on what they don't use.
- **D — Dependency Inversion**: high-level modules should not depend on low-level modules; both depend on abstractions. Inject dependencies rather than constructing them.

## 11. Emergence — Simple Design (Kent Beck's rules, cited in Clean Code)

A design is simple if, in order of importance, it:

1. **Runs all the tests**
2. **Contains no duplication**
3. **Expresses the intent of the programmer**
4. **Minimizes the number of classes and methods**

## 12. Concurrency

- **Keep concurrency separate**: concurrency is a decoupling strategy, not a feature — isolate it from other code (SRP applies).
- **Limit the scope of shared mutable data**; prefer copies of data or immutable values.
- **Threads should be as independent as possible**; avoid shared state, or guard it with well-understood synchronization.
- **Know your library's** thread-safe constructs; **know your execution models** (producer-consumer, readers-writers, dining philosophers).
- **Keep synchronized sections small**; test concurrent code with many threads, different loads, and forced failures.

## 13. Common Code Smells & Heuristics

- **Rigidity / Fragility / Immobility**: code that is hard to change, breaks unexpectedly, or can't be reused.
- **Needless complexity / needless repetition**: YAGNI ("You Aren't Gonna Need It") — don't build for speculative futures; DRY out duplication.
- **Dead code**: delete it — variables, parameters, functions, or branches that never execute.
- **Obsolete / misleading comments**, **magic numbers** (replace with named constants), **inconsistent style**.
- **Feature envy**: a method that uses another object's data more than its own belongs over there.
- **Inappropriate intimacy** and **long dependency chains**: reduce coupling.
- **Artificial coupling**: things that don't depend on each other should not share placement.
- **Functions should descend only one level of abstraction**; **base classes should know nothing about their derivatives**.
- **Prefer polymorphism over if/else or switch** statements that repeatedly switch on type.
- **Follow standard conventions** of the language and the project.

## Review Mode

When reviewing code with this skill, report findings using the categories above. For each finding:

1. Name the principle or smell violated.
2. Quote the offending code with its location.
3. Explain the concrete risk (readability, testability, change cost).
4. Propose the minimal clean-code fix.

Prioritize: correctness/test issues → design (SOLID, functions, classes) → naming/readability → formatting.
