import os
import unittest
from unittest.mock import patch

from rightime.runtime import RuntimeConfig, build_engine, load_runtime_config


class RuntimeConfigTest(unittest.TestCase):
    def test_load_runtime_config_reads_required_environment(self) -> None:
        env = {
            "RIGHTIME_OPENAI_API_KEY": "secret",
            "RIGHTIME_OPENAI_MODEL": "test-model",
            "RIGHTIME_OPENAI_ENDPOINT": "https://example.test/responses",
        }

        with patch.dict(os.environ, env, clear=True):
            config = load_runtime_config()

        self.assertEqual(config.api_key, "secret")
        self.assertEqual(config.model, "test-model")
        self.assertEqual(config.endpoint, "https://example.test/responses")

    def test_load_runtime_config_reports_missing_names(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "RIGHTIME_OPENAI_API_KEY"):
                load_runtime_config()

    def test_build_engine_uses_provider_settings(self) -> None:
        created = []

        class FakeProvider:
            model = "fake"

            def __init__(self, **kwargs) -> None:
                created.append(kwargs)

        engine = build_engine(
            RuntimeConfig(api_key="secret", model="test-model", endpoint=None),
            provider_cls=FakeProvider,
        )

        self.assertEqual(created, [{"api_key": "secret", "model": "test-model"}])
        self.assertEqual(engine._provider.model, "fake")


if __name__ == "__main__":
    unittest.main()
