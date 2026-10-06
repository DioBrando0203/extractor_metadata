import time
from dataclasses import replace

import pytest
from msg_factory import make_msg

from app.core.errors import ExtractionError
from app.services import worker


def slow_worker(connection, *args):
    time.sleep(10)


def test_timeout_terminates_worker_and_returns_diagnostic(tmp_path, monkeypatch):
    path = tmp_path / "slow.msg"
    path.write_bytes(make_msg())
    monkeypatch.setattr(worker, "_worker", slow_worker)
    monkeypatch.setattr(worker, "settings", replace(worker.settings, extraction_timeout_seconds=1))
    start = time.monotonic()
    with pytest.raises(ExtractionError) as result:
        worker.run_extraction(path, "slow.msg", path.stat().st_size)
    assert result.value.code == "EXTRACTION_TIMEOUT"
    assert time.monotonic() - start < 5


def test_timeout_scales_with_file_size(monkeypatch):
    monkeypatch.setattr(
        worker,
        "settings",
        replace(
            worker.settings,
            extraction_timeout_seconds=1,
            minimum_processing_bytes_per_second=10,
        ),
    )
    assert worker._timeout_for_size(101) == 11


def test_failed_worker_has_safe_diagnostic(tmp_path):
    path = tmp_path / "broken.msg"
    path.write_bytes(b"broken")
    with pytest.raises(ExtractionError) as result:
        worker.run_extraction(path, "broken.msg", 6)
    assert result.value.code == "INVALID_OR_CORRUPT_MSG"
    assert str(tmp_path) not in str(result.value)
