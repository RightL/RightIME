# rightIME Conversion Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Milestone 1: a shared cloud conversion engine plus CLI runner for converting continuous pinyin mixed with English into Chinese.

**Architecture:** Implement a small Python package under `src/rightime`. The conversion engine builds a provider-independent prompt from raw text and session context, calls one cloud provider implementation, returns one plain-text result, and reports visible provider failures. The CLI is only a debug runner; it does not implement the later floating composer or native IME shells.

**Tech Stack:** Python 3.11+ in the `part` conda environment, standard library runtime code, `unittest` for tests, OpenAI Responses API over `urllib.request`.

**References:**
- Approved spec: `docs/superpowers/specs/2026-04-27-rightime-design.md`
- OpenAI Responses API reference: https://platform.openai.com/docs/api-reference/responses/create

---

## Scope

This plan implements only Milestone 1 from the approved design:

- conversion request and response types
- session context model
- cloud provider interface
- OpenAI Responses provider implementation
- prompt template for mixed pinyin and English input
- example corpus for quality testing
- CLI debug runner

This plan does not implement the hotkey floating composer, global shortcuts, auto-paste, Windows TSF, macOS InputMethodKit, packaging, signing, local models, or surrounding-text inspection.

## File Structure

- Create: `pyproject.toml`  
  Python package metadata and console entry point.
- Create: `src/rightime/__init__.py`  
  Public package exports.
- Create: `src/rightime/types.py`  
  Immutable request, settings, metadata, prompt, and result data types.
- Create: `src/rightime/context.py`  
  Session-local accepted-output context.
- Create: `src/rightime/prompt.py`  
  Provider-independent prompt construction.
- Create: `src/rightime/provider.py`  
  Provider protocol, provider output type, and provider error type.
- Create: `src/rightime/engine.py`  
  Conversion engine orchestration.
- Create: `src/rightime/providers/__init__.py`  
  Provider package marker.
- Create: `src/rightime/providers/openai_responses.py`  
  OpenAI Responses API provider using `urllib.request`.
- Create: `src/rightime/cli.py`  
  Debug CLI entry point.
- Create: `examples/conversion_cases.jsonl`  
  Initial quality examples.
- Create: `tests/test_package_import.py`  
  Package import smoke test.
- Create: `tests/test_types.py`  
  Domain type tests.
- Create: `tests/test_context.py`  
  Session context tests.
- Create: `tests/test_prompt.py`  
  Prompt construction tests.
- Create: `tests/test_engine.py`  
  Engine orchestration tests.
- Create: `tests/test_openai_responses_provider.py`  
  Provider request and response parsing tests without network.
- Create: `tests/test_cli.py`  
  CLI behavior tests.

## Task 0: Initialize Git Repository

**Files:**
- Modify: `.git/` repository metadata

- [ ] **Step 1: Initialize Git if needed**

Run:

```bash
git init
```

Expected: Git reports that it initialized or reinitialized the repository.

- [ ] **Step 2: Commit approved planning docs**

Run:

```bash
git add .gitignore DESIGN_NOTES.md docs/superpowers/specs/2026-04-27-rightime-design.md docs/superpowers/plans/2026-04-27-rightime-conversion-engine.md
git commit -m "docs: add rightIME conversion engine plan"
```

Expected: Git creates the first docs commit.

## Task 1: Package Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `src/rightime/__init__.py`
- Test: `tests/test_package_import.py`

- [ ] **Step 1: Write the failing import test**

Create `tests/test_package_import.py`:

```python
import unittest

import rightime


class PackageImportTest(unittest.TestCase):
    def test_version_is_exposed(self) -> None:
        self.assertEqual(rightime.__version__, "0.1.0")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_package_import -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'rightime'`.

- [ ] **Step 3: Add package metadata and package init**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "rightime"
version = "0.1.0"
description = "Cloud-first pinyin-to-Chinese conversion engine for rightIME"
requires-python = ">=3.11"
dependencies = []

[project.scripts]
rightime-convert = "rightime.cli:main"

[tool.setuptools.packages.find]
where = ["src"]
```

Create `src/rightime/__init__.py`:

```python
__version__ = "0.1.0"
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_package_import -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add pyproject.toml src/rightime/__init__.py tests/test_package_import.py
git commit -m "chore: scaffold rightIME Python package"
```

Expected: Git creates the scaffold commit.

## Task 2: Domain Types

**Files:**
- Create: `src/rightime/types.py`
- Modify: `src/rightime/__init__.py`
- Test: `tests/test_types.py`

- [ ] **Step 1: Write the failing type tests**

Create `tests/test_types.py`:

```python
import unittest
from dataclasses import FrozenInstanceError

from rightime import (
    ConversionMetadata,
    ConversionRequest,
    ConversionResult,
    ConversionSettings,
    ProviderPrompt,
)


class DomainTypesTest(unittest.TestCase):
    def test_conversion_request_defaults(self) -> None:
        request = ConversionRequest(raw_text="wo zai xie rightIME")

        self.assertEqual(request.raw_text, "wo zai xie rightIME")
        self.assertEqual(request.session_context, ())
        self.assertEqual(request.settings.locale, "zh-Hans")
        self.assertTrue(request.settings.preserve_ascii_terms)

    def test_types_are_immutable(self) -> None:
        result = ConversionResult(
            text="我在写 rightIME",
            metadata=ConversionMetadata(model="test-model", latency_ms=12, token_count=8),
        )

        with self.assertRaises(FrozenInstanceError):
            result.text = "changed"

    def test_provider_prompt_carries_instructions_and_input(self) -> None:
        prompt = ProviderPrompt(
            instructions="Return plain text only.",
            input_text="Draft: wo yao ceshi",
        )

        self.assertIn("plain text", prompt.instructions)
        self.assertIn("wo yao ceshi", prompt.input_text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_types -v
```

Expected: FAIL with missing exports or missing `rightime.types`.

- [ ] **Step 3: Add immutable domain types**

Create `src/rightime/types.py`:

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ConversionSettings:
    locale: str = "zh-Hans"
    preserve_ascii_terms: bool = True


@dataclass(frozen=True)
class ConversionRequest:
    raw_text: str
    session_context: tuple[str, ...] = ()
    settings: ConversionSettings = field(default_factory=ConversionSettings)


@dataclass(frozen=True)
class ProviderPrompt:
    instructions: str
    input_text: str


@dataclass(frozen=True)
class ConversionMetadata:
    model: str
    latency_ms: int
    token_count: int | None = None


@dataclass(frozen=True)
class ConversionResult:
    text: str
    metadata: ConversionMetadata
```

Modify `src/rightime/__init__.py`:

```python
from rightime.types import (
    ConversionMetadata,
    ConversionRequest,
    ConversionResult,
    ConversionSettings,
    ProviderPrompt,
)

__version__ = "0.1.0"

__all__ = [
    "ConversionMetadata",
    "ConversionRequest",
    "ConversionResult",
    "ConversionSettings",
    "ProviderPrompt",
    "__version__",
]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_types -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/rightime/__init__.py src/rightime/types.py tests/test_types.py
git commit -m "feat: add conversion domain types"
```

Expected: Git creates the domain types commit.

## Task 3: Session Context

**Files:**
- Create: `src/rightime/context.py`
- Modify: `src/rightime/__init__.py`
- Test: `tests/test_context.py`

- [ ] **Step 1: Write the failing context tests**

Create `tests/test_context.py`:

```python
import unittest

from rightime import SessionContext


class SessionContextTest(unittest.TestCase):
    def test_accept_returns_new_context_with_text(self) -> None:
        context = SessionContext()
        updated = context.accept("我现在在写 rightIME")

        self.assertEqual(context.accepted_outputs, ())
        self.assertEqual(updated.accepted_outputs, ("我现在在写 rightIME",))

    def test_as_prompt_context_lists_recent_outputs(self) -> None:
        context = (
            SessionContext()
            .accept("第一句")
            .accept("第二句")
            .accept("第三句")
        )

        self.assertEqual(context.as_prompt_context(max_items=2), "- 第二句\n- 第三句")

    def test_empty_context_has_explicit_marker(self) -> None:
        self.assertEqual(SessionContext().as_prompt_context(), "(no accepted text yet)")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_context -v
```

Expected: FAIL with missing `SessionContext`.

- [ ] **Step 3: Add session context model**

Create `src/rightime/context.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class SessionContext:
    accepted_outputs: tuple[str, ...] = ()

    def accept(self, text: str) -> "SessionContext":
        return SessionContext(accepted_outputs=(*self.accepted_outputs, text))

    def as_prompt_context(self, max_items: int = 6) -> str:
        if not self.accepted_outputs:
            return "(no accepted text yet)"
        recent = self.accepted_outputs[-max_items:]
        return "\n".join(f"- {item}" for item in recent)
```

Modify `src/rightime/__init__.py`:

```python
from rightime.context import SessionContext
from rightime.types import (
    ConversionMetadata,
    ConversionRequest,
    ConversionResult,
    ConversionSettings,
    ProviderPrompt,
)

__version__ = "0.1.0"

__all__ = [
    "ConversionMetadata",
    "ConversionRequest",
    "ConversionResult",
    "ConversionSettings",
    "ProviderPrompt",
    "SessionContext",
    "__version__",
]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_context -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/rightime/__init__.py src/rightime/context.py tests/test_context.py
git commit -m "feat: add session context model"
```

Expected: Git creates the session context commit.

## Task 4: Prompt Builder

**Files:**
- Create: `src/rightime/prompt.py`
- Test: `tests/test_prompt.py`

- [ ] **Step 1: Write the failing prompt tests**

Create `tests/test_prompt.py`:

```python
import unittest

from rightime import ConversionRequest
from rightime.prompt import build_prompt


class PromptBuilderTest(unittest.TestCase):
    def test_prompt_contains_context_and_current_draft(self) -> None:
        prompt = build_prompt(
            ConversionRequest(
                raw_text="wo xiang yao continuous input",
                session_context=("我们在讨论 rightIME。",),
            )
        )

        self.assertIn("Return only the converted text", prompt.instructions)
        self.assertIn("Do not use Markdown", prompt.instructions)
        self.assertIn("我们在讨论 rightIME。", prompt.input_text)
        self.assertIn("wo xiang yao continuous input", prompt.input_text)

    def test_prompt_preserves_ascii_terms_instruction(self) -> None:
        prompt = build_prompt(ConversionRequest(raw_text="ba API key fang zai settings li"))

        self.assertIn("Preserve clear English words", prompt.instructions)
        self.assertIn("Product names, code identifiers", prompt.instructions)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_prompt -v
```

Expected: FAIL with missing `rightime.prompt`.

- [ ] **Step 3: Add prompt builder**

Create `src/rightime/prompt.py`:

```python
from rightime.types import ConversionRequest, ProviderPrompt


INSTRUCTIONS = """You convert continuous pinyin mixed with English into natural Simplified Chinese.
Return only the converted text. Do not use Markdown. Do not explain the conversion.
Preserve clear English words, product names, code identifiers, numbers, and punctuation when they are intended as English.
Use the accepted session context only to preserve tone, terminology, and continuity.
"""


def build_prompt(request: ConversionRequest) -> ProviderPrompt:
    context = "\n".join(f"- {item}" for item in request.session_context)
    if not context:
        context = "(no accepted text yet)"

    input_text = "\n".join(
        [
            "Accepted session context:",
            context,
            "",
            "Current draft:",
            request.raw_text,
        ]
    )

    return ProviderPrompt(instructions=INSTRUCTIONS, input_text=input_text)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_prompt -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/rightime/prompt.py tests/test_prompt.py
git commit -m "feat: add conversion prompt builder"
```

Expected: Git creates the prompt builder commit.

## Task 5: Conversion Engine And Provider Contract

**Files:**
- Create: `src/rightime/provider.py`
- Create: `src/rightime/engine.py`
- Modify: `src/rightime/__init__.py`
- Test: `tests/test_engine.py`

- [ ] **Step 1: Write the failing engine tests**

Create `tests/test_engine.py`:

```python
import unittest

from rightime import ConversionRequest
from rightime.engine import ConversionEngine
from rightime.provider import ProviderError, ProviderOutput


class FakeProvider:
    model = "fake-model"

    def __init__(self) -> None:
        self.prompts = []

    def convert(self, prompt):
        self.prompts.append(prompt)
        return ProviderOutput(text="我想要 continuous input", token_count=17)


class FailingProvider:
    model = "broken-model"

    def convert(self, prompt):
        raise ProviderError("provider_unavailable", "network request failed")


class ConversionEngineTest(unittest.TestCase):
    def test_convert_returns_provider_text_and_metadata(self) -> None:
        provider = FakeProvider()
        ticks = iter([10.0, 10.125])
        engine = ConversionEngine(provider=provider, clock=lambda: next(ticks))

        result = engine.convert(
            ConversionRequest(
                raw_text="wo xiang yao continuous input",
                session_context=("我们在讨论 rightIME。",),
            )
        )

        self.assertEqual(result.text, "我想要 continuous input")
        self.assertEqual(result.metadata.model, "fake-model")
        self.assertEqual(result.metadata.latency_ms, 125)
        self.assertEqual(result.metadata.token_count, 17)
        self.assertEqual(len(provider.prompts), 1)
        self.assertIn("我们在讨论 rightIME。", provider.prompts[0].input_text)

    def test_provider_failure_is_visible(self) -> None:
        engine = ConversionEngine(provider=FailingProvider())

        with self.assertRaisesRegex(ProviderError, "network request failed"):
            engine.convert(ConversionRequest(raw_text="wo yao shibai"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_engine -v
```

Expected: FAIL with missing `rightime.engine` or `rightime.provider`.

- [ ] **Step 3: Add provider contract and conversion engine**

Create `src/rightime/provider.py`:

```python
from dataclasses import dataclass
from typing import Protocol

from rightime.types import ProviderPrompt


@dataclass(frozen=True)
class ProviderOutput:
    text: str
    token_count: int | None = None


class ProviderError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class ConversionProvider(Protocol):
    model: str

    def convert(self, prompt: ProviderPrompt) -> ProviderOutput:
        raise NotImplementedError
```

Create `src/rightime/engine.py`:

```python
from collections.abc import Callable
from time import monotonic

from rightime.prompt import build_prompt
from rightime.provider import ConversionProvider
from rightime.types import ConversionMetadata, ConversionRequest, ConversionResult


class ConversionEngine:
    def __init__(
        self,
        provider: ConversionProvider,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self._provider = provider
        self._clock = clock

    def convert(self, request: ConversionRequest) -> ConversionResult:
        prompt = build_prompt(request)
        started = self._clock()
        provider_output = self._provider.convert(prompt)
        finished = self._clock()

        metadata = ConversionMetadata(
            model=self._provider.model,
            latency_ms=round((finished - started) * 1000),
            token_count=provider_output.token_count,
        )
        return ConversionResult(text=provider_output.text, metadata=metadata)
```

Modify `src/rightime/__init__.py`:

```python
from rightime.context import SessionContext
from rightime.engine import ConversionEngine
from rightime.provider import ConversionProvider, ProviderError, ProviderOutput
from rightime.types import (
    ConversionMetadata,
    ConversionRequest,
    ConversionResult,
    ConversionSettings,
    ProviderPrompt,
)

__version__ = "0.1.0"

__all__ = [
    "ConversionEngine",
    "ConversionMetadata",
    "ConversionProvider",
    "ConversionRequest",
    "ConversionResult",
    "ConversionSettings",
    "ProviderError",
    "ProviderOutput",
    "ProviderPrompt",
    "SessionContext",
    "__version__",
]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_engine -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/rightime/__init__.py src/rightime/provider.py src/rightime/engine.py tests/test_engine.py
git commit -m "feat: add conversion engine contract"
```

Expected: Git creates the engine contract commit.

## Task 6: OpenAI Responses Provider

**Files:**
- Create: `src/rightime/providers/__init__.py`
- Create: `src/rightime/providers/openai_responses.py`
- Test: `tests/test_openai_responses_provider.py`

- [ ] **Step 1: Write the failing provider tests**

Create `tests/test_openai_responses_provider.py`:

```python
import json
import unittest
from io import BytesIO
from urllib.error import HTTPError

from rightime.provider import ProviderError
from rightime.providers.openai_responses import OpenAIResponsesProvider
from rightime.types import ProviderPrompt


class FakeHttpResponse:
    status = 200

    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class CapturingOpener:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.requests = []
        self.timeouts = []

    def __call__(self, request, timeout):
        self.requests.append(request)
        self.timeouts.append(timeout)
        return FakeHttpResponse(self.payload)


class OpenAIResponsesProviderTest(unittest.TestCase):
    def test_sends_responses_request_and_parses_output_text(self) -> None:
        opener = CapturingOpener(
            {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {"type": "output_text", "text": "我在写 rightIME。"}
                        ],
                    }
                ],
                "usage": {"input_tokens": 12, "output_tokens": 9},
            }
        )
        provider = OpenAIResponsesProvider(
            api_key="secret",
            model="test-model",
            opener=opener,
            timeout_s=7,
        )

        output = provider.convert(
            ProviderPrompt(
                instructions="Return only text.",
                input_text="Current draft:\nwo zai xie rightIME",
            )
        )

        self.assertEqual(output.text, "我在写 rightIME。")
        self.assertEqual(output.token_count, 21)
        sent = opener.requests[0]
        body = json.loads(sent.data.decode("utf-8"))
        self.assertEqual(sent.full_url, "https://api.openai.com/v1/responses")
        self.assertEqual(sent.get_method(), "POST")
        self.assertEqual(sent.headers["Authorization"], "Bearer secret")
        self.assertEqual(body["model"], "test-model")
        self.assertEqual(body["instructions"], "Return only text.")
        self.assertEqual(body["input"], "Current draft:\nwo zai xie rightIME")
        self.assertEqual(body["text"]["format"]["type"], "text")
        self.assertEqual(opener.timeouts, [7])

    def test_rejects_response_without_output_text(self) -> None:
        provider = OpenAIResponsesProvider(
            api_key="secret",
            model="test-model",
            opener=CapturingOpener({"output": []}),
        )

        with self.assertRaisesRegex(ProviderError, "missing output_text"):
            provider.convert(ProviderPrompt(instructions="i", input_text="x"))

    def test_http_error_is_visible(self) -> None:
        def raising_opener(request, timeout):
            raise HTTPError(
                url=request.full_url,
                code=401,
                msg="Unauthorized",
                hdrs={},
                fp=BytesIO(b'{"error":{"message":"bad key"}}'),
            )

        provider = OpenAIResponsesProvider(
            api_key="secret",
            model="test-model",
            opener=raising_opener,
        )

        with self.assertRaisesRegex(ProviderError, "401"):
            provider.convert(ProviderPrompt(instructions="i", input_text="x"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_openai_responses_provider -v
```

Expected: FAIL with missing `rightime.providers.openai_responses`.

- [ ] **Step 3: Add OpenAI Responses provider**

Create `src/rightime/providers/__init__.py`:

```python
"""Cloud provider implementations for rightIME."""
```

Create `src/rightime/providers/openai_responses.py`:

```python
import json
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from rightime.provider import ProviderError, ProviderOutput
from rightime.types import ProviderPrompt


class OpenAIResponsesProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        endpoint: str = "https://api.openai.com/v1/responses",
        timeout_s: int = 20,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._endpoint = endpoint
        self._timeout_s = timeout_s
        self._opener = opener

    def convert(self, prompt: ProviderPrompt) -> ProviderOutput:
        payload = {
            "model": self.model,
            "instructions": prompt.instructions,
            "input": prompt.input_text,
            "text": {"format": {"type": "text"}},
        }
        data = json.dumps(payload).encode("utf-8")
        request = Request(
            self._endpoint,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with self._opener(request, timeout=self._timeout_s) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise ProviderError("request_rejected", f"OpenAI request failed with HTTP {exc.code}: {body}") from exc
        except URLError as exc:
            raise ProviderError("provider_unavailable", f"OpenAI request failed: {exc.reason}") from exc

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ProviderError("invalid_provider_response", "OpenAI response was not JSON") from exc

        text = _extract_output_text(parsed)
        token_count = _extract_token_count(parsed)
        return ProviderOutput(text=text, token_count=token_count)


def _extract_output_text(parsed: dict[str, Any]) -> str:
    for output_item in parsed.get("output", []):
        for content_item in output_item.get("content", []):
            if content_item.get("type") == "output_text":
                text = content_item.get("text")
                if isinstance(text, str):
                    return text
    raise ProviderError("invalid_provider_response", "OpenAI response missing output_text")


def _extract_token_count(parsed: dict[str, Any]) -> int | None:
    usage = parsed.get("usage")
    if not isinstance(usage, dict):
        return None

    total = usage.get("total_tokens")
    if isinstance(total, int):
        return total

    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    if isinstance(input_tokens, int) and isinstance(output_tokens, int):
        return input_tokens + output_tokens

    return None
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_openai_responses_provider -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/rightime/providers/__init__.py src/rightime/providers/openai_responses.py tests/test_openai_responses_provider.py
git commit -m "feat: add OpenAI responses provider"
```

Expected: Git creates the provider commit.

## Task 7: CLI Debug Runner

**Files:**
- Create: `src/rightime/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing CLI tests**

Create `tests/test_cli.py`:

```python
import os
import unittest
from io import StringIO
from unittest.mock import patch

from rightime import ConversionMetadata, ConversionResult
from rightime.cli import main


class FakeEngine:
    requests = []

    def __init__(self, provider) -> None:
        self.provider = provider

    def convert(self, request):
        self.requests.append(request)
        return ConversionResult(
            text="我在写 rightIME。",
            metadata=ConversionMetadata(model="fake-model", latency_ms=33, token_count=10),
        )


class FakeProvider:
    def __init__(self, api_key: str, model: str, endpoint: str | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self.endpoint = endpoint


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        FakeEngine.requests = []

    def test_cli_prints_conversion_text(self) -> None:
        env = {
            "RIGHTIME_OPENAI_API_KEY": "secret",
            "RIGHTIME_OPENAI_MODEL": "test-model",
        }
        stdout = StringIO()

        with patch.dict(os.environ, env, clear=True), patch(
            "rightime.cli.OpenAIResponsesProvider", FakeProvider
        ), patch("rightime.cli.ConversionEngine", FakeEngine), patch("sys.stdout", stdout):
            code = main(["wo zai xie rightIME", "--context-line", "我们在讨论输入法。"])

        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue(), "我在写 rightIME。\n")
        self.assertEqual(FakeEngine.requests[0].raw_text, "wo zai xie rightIME")
        self.assertEqual(FakeEngine.requests[0].session_context, ("我们在讨论输入法。",))

    def test_cli_requires_api_key_and_model(self) -> None:
        stderr = StringIO()

        with patch.dict(os.environ, {}, clear=True), patch("sys.stderr", stderr):
            code = main(["wo yao ceshi"])

        self.assertEqual(code, 2)
        self.assertIn("RIGHTIME_OPENAI_API_KEY", stderr.getvalue())
        self.assertIn("RIGHTIME_OPENAI_MODEL", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_cli -v
```

Expected: FAIL with missing `rightime.cli`.

- [ ] **Step 3: Add CLI runner**

Create `src/rightime/cli.py`:

```python
import argparse
import os
import sys

from rightime.engine import ConversionEngine
from rightime.providers.openai_responses import OpenAIResponsesProvider
from rightime.types import ConversionRequest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rightime-convert")
    parser.add_argument("text", help="Pinyin and English mixed draft to convert")
    parser.add_argument(
        "--context-line",
        action="append",
        default=[],
        help="Accepted session context line. May be passed multiple times.",
    )
    args = parser.parse_args(argv)

    api_key = os.environ.get("RIGHTIME_OPENAI_API_KEY")
    model = os.environ.get("RIGHTIME_OPENAI_MODEL")
    endpoint = os.environ.get("RIGHTIME_OPENAI_ENDPOINT")

    missing = [
        name
        for name, value in (
            ("RIGHTIME_OPENAI_API_KEY", api_key),
            ("RIGHTIME_OPENAI_MODEL", model),
        )
        if not value
    ]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        return 2

    provider_kwargs = {"api_key": api_key, "model": model}
    if endpoint:
        provider_kwargs["endpoint"] = endpoint

    provider = OpenAIResponsesProvider(**provider_kwargs)
    engine = ConversionEngine(provider=provider)
    result = engine.convert(
        ConversionRequest(
            raw_text=args.text,
            session_context=tuple(args.context_line),
        )
    )
    print(result.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest tests.test_cli -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/rightime/cli.py tests/test_cli.py
git commit -m "feat: add conversion debug cli"
```

Expected: Git creates the CLI commit.

## Task 8: Example Corpus And Full Test Run

**Files:**
- Create: `examples/conversion_cases.jsonl`

- [ ] **Step 1: Add initial quality examples**

Create `examples/conversion_cases.jsonl`:

```jsonl
{"input":"wo xianzai zai he LLM taolun rightIME de sheji","context":[],"acceptable":["我现在在和 LLM 讨论 rightIME 的设计"]}
{"input":"zhege gongneng dui zhong yingwen hunhe hen youyong","context":[],"acceptable":["这个功能对中英文混合很有用"]}
{"input":"ba API key fang zai settings li, buyao xie dao code limian","context":["我们在讨论 rightIME 的桌面设置。"],"acceptable":["把 API key 放在 settings 里，不要写到 code 里面"]}
{"input":"manual trigger he pause trigger dou keyi, danshi moren yong manual","context":["第一版使用 hotkey composer。"],"acceptable":["manual trigger 和 pause trigger 都可以，但是默认用 manual"]}
{"input":"ruguo cloud request shibai, UI yinggai mingque gaosu yonghu","context":[],"acceptable":["如果 cloud request 失败，UI 应该明确告诉用户"]}
```

- [ ] **Step 2: Run the full local test suite**

Run:

```bash
PYTHONPATH=src conda run -n part python -m unittest discover -s tests -v
```

Expected: all tests PASS.

- [ ] **Step 3: Run the CLI with a real provider configuration**

Run after setting `RIGHTIME_OPENAI_API_KEY` and `RIGHTIME_OPENAI_MODEL` in the shell:

```bash
PYTHONPATH=src conda run -n part python -m rightime.cli "wo xianzai zai ceshi rightIME"
```

Expected: stdout prints one converted plain-text Chinese result and no Markdown explanation.

- [ ] **Step 4: Commit**

Run:

```bash
git add examples/conversion_cases.jsonl
git commit -m "test: add initial conversion examples"
```

Expected: Git creates the examples commit.

## Completion Criteria

- `PYTHONPATH=src conda run -n part python -m unittest discover -s tests -v` passes.
- Conversion behavior is available through `ConversionEngine.convert()`.
- The engine returns one primary text result and metadata.
- The engine does not mutate session context or auto-commit text.
- Provider failure raises `ProviderError` with a visible message.
- The OpenAI provider test suite covers request shape, output parsing, and HTTP failure.
- The CLI can call the engine using `RIGHTIME_OPENAI_API_KEY` and `RIGHTIME_OPENAI_MODEL`.
- No Windows TSF, macOS InputMethodKit, global hotkey, auto-paste, or desktop UI code exists in this milestone.
