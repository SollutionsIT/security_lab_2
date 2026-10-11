import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from security.scripts.run_ci import assert_free_port, lab_environment, stop_owned, wait_ready

ROOT = Path(__file__).resolve().parents[2]


def test_owned_lab_overrides_production_settings_without_mutating_input() -> None:
    source = {"NODE_ENV": "production", "HOST": "0.0.0.0", "PORT": "80", "LAB_TEST_MODE": "false"}
    environment = lab_environment(source)
    assert environment["NODE_ENV"] == "test"
    assert environment["HOST"] == "127.0.0.1"
    assert environment["PORT"] == "3001"
    assert environment["LAB_TEST_MODE"] == "true"
    assert source["NODE_ENV"] == "production"


def test_occupied_port_is_not_silently_reused() -> None:
    with patch("security.scripts.run_ci.socket.socket") as factory:
        factory.return_value.__enter__.return_value.bind.side_effect = OSError("occupied")
        with pytest.raises(RuntimeError, match="do not reuse or stop"):
            assert_free_port()


def test_readiness_rejects_an_exited_owned_process() -> None:
    process = Mock(spec=subprocess.Popen)
    process.poll.return_value = 1
    with pytest.raises(RuntimeError, match="exited before readiness"):
        wait_ready(process)


def test_cleanup_only_terminates_its_owned_live_process() -> None:
    process = Mock(spec=subprocess.Popen)
    process.poll.return_value = None
    stop_owned(process)
    process.terminate.assert_called_once_with()
    process.wait.assert_called_once_with(timeout=5)
    process.kill.assert_not_called()


def test_cleanup_escalates_only_after_owned_process_timeout() -> None:
    process = Mock(spec=subprocess.Popen)
    process.poll.return_value = None
    process.wait.side_effect = [subprocess.TimeoutExpired("owned-node", 5), 0]
    stop_owned(process)
    process.terminate.assert_called_once_with()
    process.kill.assert_called_once_with()


def test_cleanup_does_not_signal_an_exited_process() -> None:
    process = Mock(spec=subprocess.Popen)
    process.poll.return_value = 0
    stop_owned(process)
    process.terminate.assert_not_called()
    process.kill.assert_not_called()


def test_github_native_contract_keeps_untrusted_code_unprivileged() -> None:
    pipeline = yaml.safe_load((ROOT / ".github/workflows/portfolio-native.yml").read_text())
    triggers = pipeline.get("on", pipeline.get(True))  # PyYAML uses YAML 1.1 booleans.
    assert "pull_request" in triggers
    assert "pull_request_target" not in triggers
    assert pipeline["permissions"] == {"contents": "read"}
    steps = pipeline["jobs"]["local-evidence"]["steps"]
    assert any(step.get("run") == "make ci-verify" for step in steps)
    checkout = next(step for step in steps if step.get("uses", "").startswith("actions/checkout@"))
    assert checkout["with"]["persist-credentials"] is False
    upload = next(
        step for step in steps if step.get("uses", "").startswith("actions/upload-artifact@")
    )
    assert upload["if"] == "always()"
    assert "reports/bdd/results.xml" in upload["with"]["path"]
    assert "reports/ci/lab.log" not in upload["with"]["path"]


def test_gitlab_contract_uses_pinned_images_required_jobs_and_junit() -> None:
    pipeline = yaml.safe_load((ROOT / ".gitlab-ci.yml").read_text())
    assert "@sha256:" in pipeline["default"]["image"]
    assert "timeout" not in pipeline["default"]
    for name in (
        "native-security",
        "secret-scan",
        "custom-sast",
        "trivy-filesystem",
        "scanner-policy",
    ):
        job = pipeline[name]
        assert job.get("allow_failure", False) is False
        assert job["timeout"]
        assert job["artifacts"]["when"] == "always"
        image = job.get("image", {})
        if image:
            assert "@sha256:" in image["name"]
    native = pipeline["native-security"]
    assert native["script"][0] == "make ci-verify"
    assert "reports/bdd/results.xml" in native["artifacts"]["reports"]["junit"]
    release = pipeline["release-evidence"]
    assert release["stage"] == "delivery"
    assert "CI_COMMIT_REF_PROTECTED" in release["rules"][0]["if"]
    assert {entry["job"] for entry in release["needs"]} == {
        "native-security",
        "secret-scan",
        "custom-sast",
        "scanner-policy",
    }
