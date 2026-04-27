from rightime.types import ConversionRequest, ProviderPrompt


INSTRUCTIONS = """You convert continuous pinyin mixed with English into natural Simplified Chinese.
Return only the converted text. Do not use Markdown. Do not explain the conversion.
Preserve clear English words. Product names, code identifiers, numbers, and punctuation should stay in English when intended as English.
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
