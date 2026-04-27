# DESIGN_NOTES

## Project

- 2026-04-27: rightIME is designed cloud-first because the user accepts network-required conversion and quality matters more than offline support for the first version.
- 2026-04-27: The first user-facing shell is a hotkey-triggered floating composer, not Windows TSF or macOS InputMethodKit, because the conversion workflow should be proven before native IME integration work begins.
- 2026-04-27: The conversion engine is shared and provider-independent so later desktop shells and native IME shells do not duplicate LLM behavior.
- 2026-04-27: The first context boundary is session-local context only, because it improves paragraph flow while avoiding unreliable and privacy-sensitive inspection of other apps.
- 2026-04-27: The engine should fail visibly on cloud failure instead of silently using heuristic conversion, because low-quality hidden substitution would undermine trust in an input method.
- 2026-04-27: Milestone 1 is planned as a Python standard-library conversion engine plus CLI because conversion quality and provider boundaries can be tested before choosing the desktop shell framework.
