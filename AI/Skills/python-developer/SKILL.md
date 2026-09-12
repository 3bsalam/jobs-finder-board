---
name: python-developer
description:
  You are an Expert Python Software Engineer with deep knowledge of modern Python 3.12+ best practices.
  Use when creating new Python projects, reviewing Python code, refactoring existing code,
  or when the user asks about Python project structure, dependencies, type hints, testing, or modern Python features.
  Ensures code follows current best practices with proper tooling (uv, ruff, ty/mypy, pytest), type hints, dataclasses,
  async patterns, and project structure. Includes version-specific features for 3.12, 3.13, and 3.14.
disable-model-invocation: true
license: MIT
metadata:
  author: Giannis Vrentzos
  version: "1.3.0"
---

# Python Developer

Guide for writing production-quality Python 3.12+ projects following current best practices.

## Version Support

This guide covers:
- **Python 3.12+**: Base requirements and common features (all sections below)
- **Python 3.13**: Additional features and improvements → See [references/python-3.13-features.md](references/python-3.13-features.md)
- **Python 3.14**: Latest features and enhancements → See [references/python-3.14-features.md](references/python-3.14-features.md)

### Feature Version Matrix

| Feature | 3.12 | 3.13 | 3.14 |
|---------|------|------|------|
| Type parameter syntax (`def func[T]()`) | ✅ | ✅ | ✅ |
| Type statement (`type X = ...`) | ✅ | ✅ | ✅ |
| Pattern matching (`match/case`) | ✅ | ✅ | ✅ |
| Exception groups (`except*`) | ✅ | ✅ | ✅ |
| TaskGroup | ✅ | ✅ | ✅ |
| TypeIs for type narrowing | ❌ | ✅ | ✅ |
| ReadOnly type hint | ❌ | ✅ | ✅ |
| Improved REPL | ❌ | ✅ | ✅ |
| Bracketless `except` (PEP 758) | ❌ | ❌ | ✅ |
| Experimental JIT | ❌ | ❌ | ✅ |
| Free-threaded (no-GIL) | ❌ | ❌ | ✅ |

## Quick Reference

**Core Requirements (3.12+):**
- Python 3.12+ minimum
- Use pyproject.toml for all config
- Type hints everywhere
- Ruff for formatting/linting
- ty or mypy for type checking
- pytest for testing
- src/ layout structure

**Type Checker Comparison:**

| Feature | mypy | ty |
|---------|------|-----|
| Status | ✅ Stable, mature (1.0+) | ⚠️ Beta (0.0.22, Mar 2026) |
| Speed | Standard | 10-100x faster |
| Language | Python | Rust |
| Ecosystem | Extensive | Growing rapidly |
| IDE Support | Universal | VS Code, PyCharm, Neovim (built-in language server) |
| Production Ready | ✅ Yes | ⚠️ Maturing fast - viable for new projects |
| Best for | Production systems, existing codebases | New projects, fast iteration |
| Maintainer | Python community | Astral (Ruff/uv creators) |
| Configuration | `[tool.mypy]` | `[tool.ty]` |
| Recommendation | Existing codebases, risk-averse teams | **Default for new projects** |

## Project Overrides

How tool settings are resolved depends on the task:

- **Reviewing existing code / PRs:** Read `pyproject.toml` from the
  repository. The project's actual configuration is the source of truth
  for python-version, line-length, ruff rules, type checker, test
  framework, and project layout. Do not override what the project
  already defines.
- **Creating new projects:** Use the defaults below when no
  `pyproject.toml` exists yet.

Local overrides (see "What Can Be Overridden") apply in both modes and
take precedence over both the project config and the defaults below.

### Defaults for New Projects

| Setting          | Default                |
|------------------|------------------------|
| python-version   | 3.14                   |
| line-length      | 120                    |
| type-checker     | ty                     |
| test-framework   | pytest                 |
| test-directory   | tests/                 |
| project-layout   | src/                   |
| docstring-style  | Google                 |
| ruff-select      | E, F, W, I, B, C4, UP |

### What Can Be Overridden

Overrides are not limited to the tool defaults above. A repository can
provide **any** additional context that affects how this skill operates:

- **Domain / business context:** what the service does, which external
  systems it integrates with, critical business invariants the AI would
  not know from reading code alone.
- **Review behavior:** which priority levels to comment on, what to
  skip, confidence threshold, maximum number of comments.
- **Codebase state:** ongoing migrations, known tech debt that is
  intentional, legacy patterns being phased out (so the AI does not flag
  them).
- **Team conventions:** patterns specific to this codebase that differ
  from generic best practices.
- **External caveats:** downstream consumers, deployment constraints,
  known limitations in third-party dependencies.

### How to Override

Place overrides in whichever local rule file your agent platform uses:

- **Cursor:** `.cursor/rules/python-overrides.mdc` (with `globs: "**/*.py"`)
- **Claude Code:** `CLAUDE.md` at the repository root
- **Generic / agentskills.io:** `AGENTS.md` at the repository root

Only include what differs from the defaults or what adds context the
AI cannot infer from the code.

**Example override (works in any of the above files):**

> **Python skill overrides for this repository:**
>
> Domain context:
> This service is the payment gateway adapter. It integrates with Stripe
> and Adyen APIs. Error handling and idempotency are critical — always
> flag missing retry logic or non-idempotent mutations in payment flows.
>
> Review behavior:
> - Only flag Priority 1 (Critical) and Priority 2 (Important) issues
> - Do not comment on docstring style or naming preferences
> - Maximum 5 review comments per PR
>
> Codebase state:
> - Mid-migration from Flask to FastAPI; mixed patterns are intentional
> - The `legacy/` directory is scheduled for removal in Q3; do not
>   review files under it
>
> Tool overrides (only when pyproject.toml does not define them):
> - docstring-style: NumPy

## Project Structure

```
project-name/
├── src/
│   └── package_name/
│       ├── __init__.py
│       └── core.py
├── tests/
│   └── test_core.py
├── pyproject.toml
└── README.md
```

**Rules:**
- ALWAYS use src/ layout (never place code at project root)
- ALWAYS include __init__.py in packages
- Use underscores in module names: `my_module.py` not `my-module.py`

## Configuration (pyproject.toml)

### Base Configuration

```toml
[project]
name = "your-project"
version = "0.1.0"
description = "Your description"
requires-python = ">=3.14"
dependencies = [
    "httpx>=0.28.1",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.14.10",
    "ty>=0.0.5",
]
test = [
    "pytest>=9.0.2",
    "pytest-asyncio>=1.3.0",
    "pytest-cov>=7.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "C4", "UP"]

[tool.ty]
python-version = "3.14"
```

## Type Hints (Python 3.12+)

**Required everywhere:**
- All function parameters and return types
- Class attributes
- Module-level variables when not obvious

**Modern syntax (3.10+):**
```python
# Use | for unions (not Optional/Union)
def process(data: str | None) -> dict[str, int | float]:
    ...

# Use lowercase generics (not List/Dict)
def filter_items(items: list[str]) -> list[str]:
    ...

# Use collections.abc for abstract types
from collections.abc import Sequence, Mapping, Iterable

def process_items(items: Sequence[str]) -> Iterable[str]:
    """Process items - accepts list, tuple, or any sequence."""
    return (item.upper() for item in items)
```

**Python 3.12+ Type Features (PEP 695):**
```python
# Type parameters with new syntax
def first[T](items: list[T]) -> T | None:
    return items[0] if items else None

# Type statement for aliases
type Point = tuple[float, float]

# Generic classes
class Container[T]:
    def __init__(self, value: T) -> None:
        self.value = value

    def get(self) -> T:
        return self.value
```

**Advanced patterns:** See [references/core-language-features.md](references/core-language-features.md) for comprehensive type hint patterns, Protocol, TypedDict, Literal, and overload examples.

**Forbidden:**
- NEVER import from typing: `List`, `Dict`, `Tuple`, `Optional`, `Union` (replaced by built-in generics and `|` syntax). Imports like `Any`, `Self`, `Protocol`, `TypeVar`, `TypeGuard`, `TypeIs` are still valid.
- NEVER leave functions untyped

## Modern Features

### Dataclasses (Python 3.7+, slots from 3.10+)

```python
from dataclasses import dataclass
from typing import Self

@dataclass(slots=True)
class User:
    id: int
    name: str
    email: str | None = None

    def with_email(self, email: str) -> Self:
        return User(id=self.id, name=self.name, email=email)
```

### Pattern Matching - Basic (Python 3.10+)

```python
def handle_command(cmd: str) -> str:
    match cmd:
        case "quit" | "exit":
            return "Exiting"
        case "help":
            return "Showing help"
        case _:
            return f"Unknown: {cmd}"
```

### Functools Patterns

```python
from functools import cache, lru_cache

@cache  # Unbounded cache for pure functions
def expensive_computation(n: int) -> int:
    return n ** 2

@lru_cache(maxsize=128)  # Limited cache
def fetch_data(url: str) -> dict[str, Any]:
    ...
```

### Pathlib (not os.path)

```python
from pathlib import Path

config_dir = Path.home() / ".config" / "myapp"
config_file = config_dir / "config.json"
```

### Context Managers

```python
import os
from collections.abc import Iterator
from contextlib import contextmanager

@contextmanager
def temporary_setting(name: str, value: str) -> Iterator[None]:
    old_value = os.getenv(name)
    os.environ[name] = value
    try:
        yield
    finally:
        if old_value is None:
            del os.environ[name]
        else:
            os.environ[name] = old_value
```

## Async Programming

### Basic Async (All versions)

```python
import asyncio
import httpx

async def fetch_url(url: str, timeout: float = 10.0) -> str:
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url)
        return response.text
```

### Task Groups (Python 3.11+)

```python
async def fetch_all(urls: list[str], timeout: float = 30.0) -> list[str]:
    async with asyncio.timeout(timeout):
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(fetch_url(url)) for url in urls]
    return [task.result() for task in tasks]
```

**Advanced patterns:** See [references/core-language-features.md](references/core-language-features.md) for decorators, descriptors, walrus operator, context variables, advanced pattern matching, and metaclasses.

## Testing (pytest)

**Key patterns:**
- Use pytest (never unittest)
- Parametrize to test multiple scenarios
- Mock external dependencies
- Use fixtures for setup/teardown
- Mark async tests with `@pytest.mark.asyncio`

See [references/testing-guide.md](references/testing-guide.md) for comprehensive testing patterns, async testing, mocking, fixtures, and coverage configuration.

## Code Quality

### Ruff Configuration

```toml
[tool.ruff]
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "C4", "UP"]
```

### Type Checking

```toml
# ty (default for new projects)
[tool.ty]
python-version = "3.14"

# mypy (for existing projects that already use it)
[tool.mypy]
python_version = "3.14"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### Naming Conventions

- **Functions/variables:** snake_case
- **Classes:** PascalCase
- **Constants:** UPPER_SNAKE_CASE
- **Private:** prefix with `_`

✅ GOOD: `calculate_average()`, `UserManager`, `MAX_RETRIES`
❌ BAD: `CalculateAverage()`, `calc_avg()`, `userManager`

## Error Handling

**Standard exception handling (All versions):**
```python
try:
    risky_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
except TimeoutError:
    logger.warning("Operation timed out")
```

**Catching `Exception` - when it's acceptable:**
```python
# ✅ Top-level handler (API endpoint, CLI) - handle gracefully
@app.route("/api/data")
def get_data():
    try:
        return process_data()
    except Exception as e:
        logger.exception("Request failed")
        return {"error": "Internal server error"}, 500

# ✅ Batch processing - log and continue
for item in items:
    try:
        process(item)
    except Exception as e:
        logger.exception(f"Failed to process {item}")
        continue

# ✅ Add context and wrap
except Exception as e:
    raise ProcessingError(f"Failed for {item_id}") from e

# ❌ Never silently swallow
except Exception:
    pass
```

**Exception groups (Python 3.11+):**
```python
try:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(task1())
        tg.create_task(task2())
except* ValueError as eg:
    for exc in eg.exceptions:
        handle_value_error(exc)
```

## Logging

**Basic setup:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
)
```

**Production best practices:** See [references/logging-guide.md](references/logging-guide.md) for structured logging (structlog vs python-json-logger), async logging, correlation IDs, request tracking, and performance optimization.

## Dependencies

```toml
[project]
dependencies = [
    "httpx>=0.28.1",
    "pydantic>=2.5.0",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.14.10",
    "ty>=0.0.5",
]
test = [
    "pytest>=9.0.2",
    "pytest-asyncio>=1.3.0",
    "pytest-cov>=7.0.0",
]
```

## Anti-Patterns (Never Do)

- ❌ Mutable default arguments: `def func(items=[])`
- ❌ Bare `except:` (catches SystemExit, KeyboardInterrupt)
- ❌ Silently swallowing exceptions: `except Exception: pass`
- ❌ Using eval/exec on user input
- ❌ Using `os.path` (use pathlib)
- ❌ `from typing import List, Dict` (use built-in generics)
- ❌ Hardcoded secrets or API keys
- ❌ Unparameterized SQL queries

## Documentation

```python
def calculate_average(
    numbers: list[float],
    *,
    weights: list[float] | None = None
) -> float:
    """Calculate the average of numbers.

    Args:
        numbers: List of numbers to average
        weights: Optional weights for weighted average

    Returns:
        The calculated average

    Raises:
        ValueError: If numbers is empty

    Examples:
        >>> calculate_average([1, 2, 3])
        2.0
    """
```

**Rules:** Google or NumPy docstring style. Include docstrings for public APIs. Types in signature, not docstring.

## Python 3.13 and 3.14 Features

- **Python 3.13**: See [references/python-3.13-features.md](references/python-3.13-features.md)
- **Python 3.14**: See [references/python-3.14-features.md](references/python-3.14-features.md)

## Security Best Practices

**Critical rules:**
- ✅ ALWAYS validate and sanitize user input
- ✅ ALWAYS use parameterized queries for SQL
- ✅ ALWAYS hash passwords (Argon2 or bcrypt)
- ✅ ALWAYS load secrets from environment
- ✅ ALWAYS use HTTPS for external APIs
- ❌ NEVER hardcode secrets
- ❌ NEVER use string concatenation for SQL
- ❌ NEVER log sensitive data

See [references/security-guide.md](references/security-guide.md) for input validation, SQL injection prevention, path traversal prevention, password hashing, secrets management, and comprehensive security patterns.

## Checklist

### For Code Authors

When creating Python code:

- [ ] Python 3.12+ features used
- [ ] All functions have type hints
- [ ] Modern type syntax used (`|`, lowercase generics, `collections.abc`)
- [ ] Dataclasses with `slots=True` for data
- [ ] Pathlib instead of os.path
- [ ] F-strings for formatting
- [ ] Specific exceptions caught
- [ ] Async with proper error handling and timeouts
- [ ] Tests written (pytest) with mocking
- [ ] Security best practices followed
- [ ] Docstrings for public APIs
- [ ] No hardcoded secrets
- [ ] Ruff and type checker (ty/mypy) pass
- [ ] src/ layout used

### For Code Reviewers

**Review quality rules (apply before writing any comment):**

- **Only comment when confident.** If you are uncertain whether
  something is actually wrong, do not comment. A false positive wastes
  more reviewer and author time than a missed suggestion.
- **Signal over noise.** A review with 2 critical findings is more
  valuable than one with 15 mixed-confidence suggestions. Fewer,
  higher-quality comments.
- **Default scope: Priority 1 and 2 only.** Do not comment on Priority
  3 issues unless the repository overrides explicitly request it.
- **Never comment on pure style preferences** that the configured
  linter does not flag. If ruff passes, the style is acceptable.
- **Respect the codebase's current state.** If code is in a known
  migration, uses legacy patterns being phased out, or has documented
  tech debt, do not flag those patterns unless the override says
  otherwise.
- **Use domain context when available.** A missing timeout in a payment
  service is critical; the same missing timeout in a one-off migration
  script may not be. Weigh findings against what the code actually does,
  not just generic rules.
- **Honor review behavior overrides.** If the repository sets a maximum
  comment count, confidence threshold, or excludes certain categories,
  follow those constraints strictly.
- **Findings are sensor data, not verdicts.** Never imply a change is safe
  to merge because the review is clean — surface what you checked and what
  you could not. Borrowed confidence is itself a risk. You may be one of
  several reviewers on this PR; a clean result from you covers only the
  priorities in this skill, not the PR as a whole.
- **Stay in your lane.** Focus on the priorities defined here (Python
  correctness, security, resource safety). Don't expand into generic
  coverage another reviewer is better positioned to provide — independent,
  specialized signal is more valuable than correlated overlap.

### Review Priorities

When reviewing Python code, first classify each changed file by blast radius:

- **Critical** (auth, payments, crypto, data-deletion, DB migrations, anything handling untrusted input or PII): full rigor — escalate borderline findings up one priority level.
- **Standard** (business logic, APIs, service layers): normal priority rules.
- **Low** (config, docs, generated code, test-only changes): P1 only — do not nitpick.

Then prioritize findings:

**Priority 1 - Critical Issues (Must Fix):**
1. **Security vulnerabilities** (SQL injection, hardcoded secrets, path traversal, unsafe eval, prompt injection — untrusted/user-controlled text flowing into an LLM call without safeguards; this risk is latent in runtime data, not visible in the diff)
2. **Correctness issues** (mutable defaults, async errors, missing timeouts, bare except)
3. **Resource leaks** (missing context managers on DB connections, file handles, network sockets)
4. **Newly suppressed security-linter checks** — `# noqa S...` added in this diff; treat the suppressed warning as an active finding. Pre-existing suppressions are out of scope.
5. **Suspicious test changes** — assertions weakened or rewritten to match new (possibly broken) behavior, tests deleted or skipped, coverage of the changed code path removed. When a diff changes both code and its tests, verify the tests still assert *correct* behavior, not just *current* behavior.

**Priority 2 - Important Improvements (Should Fix):**
1. **Error handling** (overly broad exceptions, missing specificity, swallowed errors)
2. **Type safety** (missing type hints, forbidden typing imports like `List`/`Optional`)
3. **Testing gaps** (missing tests, low coverage <80%, not mocking external dependencies)

**Priority 3 - Nice to Have (Consider Fixing):**
1. **Modern Python adoption** (os.path vs pathlib, old-style formatting)
2. **Documentation** (missing/incomplete docstrings)
3. **Code quality** (naming conventions, could use pattern matching)
4. **Performance** (missing @cache, could use TaskGroups). Escalate to
   Priority 2 when the impact is concrete: O(n^2) over large inputs,
   repeated expensive calls in hot paths, or blocking sync I/O in async
   code.
5. **Reinvention** — new code that reimplements an existing stdlib or internal helper instead of reusing it. Escalate to Priority 2 if the reimplemented helper handles security-sensitive logic.
6. **Generic safety gate weakening** — `@pytest.mark.skip` on non-critical tests, unrelated `# noqa` or `# type: ignore` without justification, relaxed coverage thresholds, loosened `ruff` or type-checker config.

## PR Review Workflow

> **Tip:** For PRs that touch multiple languages, use the **pr-reviewer** skill — it orchestrates language-specific review across Go, Python, and more in a single pass.

When asked to review a PR (by number, URL, or branch name):

### Step 1: Gather context
- Fetch the PR description, metadata, and diff using `gh pr view` and
  `gh pr diff`
- **Fast-fail screening:** a sprawling diff, mass test rewrites, or a
  vague/missing intent statement are themselves findings. Flag "PR too
  large to review confidently — recommend splitting" rather than
  rubber-stamping.
- Read `pyproject.toml` for the project's actual tool configuration
- Read any local overrides (`.cursor/rules/`, `AGENTS.md`, `CLAUDE.md`)
- Fetch existing review comments (`gh pr view --comments`) and skip
  findings already raised by another reviewer or the author — don't
  restate them
- Identify which files changed and their purpose from the PR description

### Step 2: Review
- Apply the review quality rules and priority levels above
- Assess changes against the PR's stated intention — flag deviations
  from what the PR says it does, not just generic code quality
- Ignore files excluded by local overrides (e.g. frozen directories)

### Step 3: Present findings
- Show findings to the user grouped by priority, with file paths and
  line numbers
- Do NOT post to GitHub until the user explicitly approves
- If there are no findings worth flagging, say so — a clean review is
  a valid outcome

### Step 4: Post (only when approved)
- Post each finding as a separate inline review comment on the specific
  line in the PR
- Use a single review submission (not individual comments) so the
  author gets one notification, not N
- Submit as a neutral `COMMENT` review, not `REQUEST_CHANGES`. The user
  decides the disposition via follow-up commands below.

### Follow-up commands
These should work without repeating the full context:
- **"re-review"** — fetch latest changes, review only new/modified
  hunks, and present findings
- **"approve"** — approve the PR with a constructive comment
- **"request changes"** — submit the review requesting changes with a
  summary of outstanding issues

### Autonomous mode
When running without a human in the loop (CI, GitHub Actions, bots),
apply these defaults instead of the interactive steps above:
- **Scope: Priority 1 and 2 only.** Do not comment on P3 issues.
- **Maximum 5 review comments per PR.** If there are more findings,
  post the 5 most critical and note the count of remaining issues in
  the review summary.
- **Post directly** — skip the preview step (Step 3). There is no user
  to approve.
- **Submit as `COMMENT`**, never `REQUEST_CHANGES` or `APPROVE`.
- **If no P1 issues are found, do not post any review.** Silence means
  approval from the autonomous reviewer.
- **On new commits** to the same PR, re-review only the changed hunks.

Repository overrides can widen or narrow these defaults (e.g. include
P2, raise or lower the max comment count).

> **Note:** Posting to GitHub requires `gh` CLI to be installed and
> authenticated.

## Resources

- **Full reference:** See [references/REFERENCE.md](references/REFERENCE.md)
- **Core language features:** See [references/core-language-features.md](references/core-language-features.md)
- **Logging guide:** See [references/logging-guide.md](references/logging-guide.md)
- **Testing guide:** See [references/testing-guide.md](references/testing-guide.md)
- **Security guide:** See [references/security-guide.md](references/security-guide.md)
- **Python 3.13 features:** See [references/python-3.13-features.md](references/python-3.13-features.md)
- **Python 3.14 features:** See [references/python-3.14-features.md](references/python-3.14-features.md)
