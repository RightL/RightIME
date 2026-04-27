# rightIME Design

Date: 2026-04-27

## Goal

rightIME is a Chinese input workflow for Windows and macOS that lets a user type continuous pinyin mixed with English, send that text to a cloud LLM, and receive fluent Chinese text without traditional word-by-word candidate selection.

The long-term product is a real OS input method. The first usable phase is a hotkey-triggered floating composer that validates the conversion workflow before native Windows TSF and macOS InputMethodKit shells are built.

## Approved Product Shape

The first user-facing version is a minimal floating composer:

1. The user presses a global hotkey.
2. A small composer appears.
3. The user types continuous pinyin mixed with English.
4. The user manually triggers conversion. Optional pause-trigger conversion can be added later.
5. The composer sends the current pinyin plus session-local context to a cloud LLM.
6. The composer shows one primary converted result.
7. The user accepts the result, which attempts to auto-paste into the previous app. If paste cannot complete, the UI reports the failure and leaves the result available for explicit copy.

This bridge product gives a real workflow without taking on native OS input method complexity immediately.

## Architecture

The system has three primary parts in the hotkey composer phase:

### Floating Composer Desktop Shell

The desktop shell owns the global hotkey, focused input box, manual conversion trigger, result preview, retry action, accept action, copy action, and auto-paste behavior.

This shell is intentionally temporary. It should prove the interaction and conversion quality, not become the final OS input method architecture.

### Shared Conversion Engine

The conversion engine owns:

- request and response types
- session context
- prompt construction
- provider-independent conversion contract
- model response parsing
- conversion metadata
- repeatable test examples

The engine should expose a small conceptual operation:

```text
convert(input, context, settings) -> result
```

Future Windows TSF and macOS InputMethodKit shells should call this same engine instead of duplicating LLM behavior.

### Cloud LLM Provider

The first implementation is cloud-first. The app does not need offline conversion in the first version.

The provider boundary should hide model-vendor details from the composer and conversion engine. Later provider implementations can support other cloud models, local models, or hybrid routing without changing the UI contract.

## Engine Behavior Contract

Input:

- current raw text from the composer, usually pinyin mixed with English
- session context from prior accepted outputs
- mode settings

Output:

- one primary converted Chinese result
- metadata such as latency, model name, token or cost estimate, and error type if the request fails

Rules:

- The engine never auto-commits text. The UI must require user acceptance.
- The model output must be plain text only, with no Markdown or explanation.
- The output should preserve obvious English words, product names, code identifiers, numbers, and punctuation.
- The first version uses only session-local context. It should not inspect surrounding text from other apps.
- Cloud request failure should be visible. The engine should not silently replace the LLM result with low-quality heuristic conversion.

## Milestones

### Milestone 1: Shared Conversion Engine

Build:

- conversion request and response types
- session context model
- cloud provider interface
- one provider implementation
- prompt template for mixed pinyin and English input
- example corpus for quality testing
- CLI or tiny debug UI for repeated conversion tests

Do not build yet:

- Windows TSF
- macOS InputMethodKit
- app packaging and signing
- local model support
- automatic surrounding-text capture from other apps
- complex candidate selection UI

### Milestone 2: Minimal Floating Composer

Build:

- global hotkey
- input panel
- manual conversion trigger
- result preview
- accept, copy, and retry actions
- auto-paste into the previous app with visible failure reporting
- copy-only setting

### Milestone 3: Desktop Hardening

Build:

- settings
- API key management
- latency and cost display
- conversion history controls
- startup behavior
- crash and error reporting

### Milestone 4: Native IME Shells

Build native shells after the behavior is proven:

- Windows TSF shell
- macOS InputMethodKit shell

Both native shells should reuse the shared conversion engine.

## Testing Direction

The first tests should focus on conversion quality and contract stability:

- mixed Chinese-English pinyin inputs
- long continuous pinyin sentences
- punctuation preservation
- product names and code identifiers
- failure handling for cloud timeouts and invalid responses
- session context improving follow-up conversion

OS-level integration tests should wait until the floating composer exists.

## Explicit Non-Goals For The First Version

- Fully native OS IME behavior
- Offline conversion
- candidate-list-heavy traditional IME UX
- automatic reading of text from arbitrary apps
- complex multi-model routing
- silent fallback conversion when the cloud model fails

## Implementation Planning Decisions

These do not change the approved product shape, but should be decided during implementation planning:

- exact desktop framework for the floating composer
- first cloud model provider
- prompt and response schema
- global hotkey default
- auto-paste implementation per platform
- API key storage mechanism
