import unittest

from rightime import ConversionMetadata, ConversionResult
from rightime.desktop.controller import ComposerController
from rightime.provider import ProviderError


class FakeEngine:
    def __init__(self) -> None:
        self.requests = []
        self.results = [
            ConversionResult(
                text="我在写 rightIME。",
                metadata=ConversionMetadata(model="fake-model", latency_ms=12, token_count=9),
            )
        ]

    def convert(self, request):
        self.requests.append(request)
        return self.results.pop(0)


class FailingEngine:
    def convert(self, request):
        raise ProviderError("provider_unavailable", "network request failed")


class ComposerControllerTest(unittest.TestCase):
    def test_convert_uses_draft_and_session_context(self) -> None:
        engine = FakeEngine()
        copied = []
        pasted = []
        controller = ComposerController(
            engine=engine,
            copy_text=copied.append,
            paste_text=lambda text: pasted.append(text) or True,
        )

        controller.set_draft("wo zai xie rightIME")
        state = controller.convert()

        self.assertEqual(state.result_text, "我在写 rightIME。")
        self.assertEqual(state.status, "result")
        self.assertEqual(engine.requests[0].raw_text, "wo zai xie rightIME")
        self.assertEqual(engine.requests[0].session_context, ())

    def test_accept_auto_pastes_and_records_session_context(self) -> None:
        engine = FakeEngine()
        pasted = []
        controller = ComposerController(
            engine=engine,
            copy_text=lambda text: None,
            paste_text=lambda text: pasted.append(text) or True,
        )

        controller.set_draft("wo zai xie rightIME")
        controller.convert()
        state = controller.accept()

        self.assertEqual(pasted, ["我在写 rightIME。"])
        self.assertEqual(state.status, "ready")
        self.assertEqual(controller.session_context.accepted_outputs, ("我在写 rightIME。",))

    def test_copy_result_does_not_accept_session_context(self) -> None:
        engine = FakeEngine()
        copied = []
        controller = ComposerController(
            engine=engine,
            copy_text=copied.append,
            paste_text=lambda text: True,
        )

        controller.set_draft("wo zai xie rightIME")
        controller.convert()
        state = controller.copy_result()

        self.assertEqual(copied, ["我在写 rightIME。"])
        self.assertEqual(state.status, "result")
        self.assertEqual(controller.session_context.accepted_outputs, ())

    def test_paste_failure_is_visible_and_result_stays_available(self) -> None:
        engine = FakeEngine()
        controller = ComposerController(
            engine=engine,
            copy_text=lambda text: None,
            paste_text=lambda text: False,
        )

        controller.set_draft("wo zai xie rightIME")
        controller.convert()
        state = controller.accept()

        self.assertEqual(state.status, "error")
        self.assertIn("Paste failed", state.message)
        self.assertEqual(state.result_text, "我在写 rightIME。")

    def test_provider_failure_is_visible(self) -> None:
        controller = ComposerController(
            engine=FailingEngine(),
            copy_text=lambda text: None,
            paste_text=lambda text: True,
        )

        controller.set_draft("wo yao shibai")
        state = controller.convert()

        self.assertEqual(state.status, "error")
        self.assertIn("network request failed", state.message)


if __name__ == "__main__":
    unittest.main()
