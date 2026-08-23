import json
import logging

from arendabot.bootstrap.logging import JsonFormatter


def test_json_formatter_emits_core_and_context_fields() -> None:
    record = logging.LogRecord(
        name="arendabot.test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=10,
        msg="dispatch failed",
        args=(),
        exc_info=None,
    )
    record.update_id = 42

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "ERROR"
    assert payload["logger"] == "arendabot.test"
    assert payload["message"] == "dispatch failed"
    assert payload["update_id"] == 42
    assert payload["timestamp"].endswith("Z")
