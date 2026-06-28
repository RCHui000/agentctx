from __future__ import annotations

from agentctx.core.doctor import run_doctor


def test_doctor_reports_ok_for_complete_safe_context(sample_context: dict) -> None:
    report = run_doctor(sample_context["workspace"], sample_context["agent_home"])

    assert report.result == "ok"
    assert report.errors == []
    assert report.warnings == []


def test_doctor_warns_when_local_session_is_not_gitignored(sample_context: dict) -> None:
    (sample_context["workspace"] / ".gitignore").write_text(".env\n", encoding="utf-8")

    report = run_doctor(sample_context["workspace"], sample_context["agent_home"])

    assert report.result == "warning"
    assert any(".agent/local.current.yaml" in item.message for item in report.warnings)


def test_doctor_finds_missing_device_and_secret_fields(sample_context: dict) -> None:
    device_path = sample_context["agent_home"] / "devices" / "example-nas.yaml"
    text = device_path.read_text(encoding="utf-8")
    device_path.write_text(
        text + "\npassword: should-not-be-here\npem_path: D:/secret/nas.pem\n",
        encoding="utf-8",
    )
    (sample_context["agent_home"] / "bindings" / "sample-app.cloud-prod.yaml").unlink()

    report = run_doctor(sample_context["workspace"], sample_context["agent_home"])

    assert report.result == "error"
    assert any("sample-app.cloud-prod" in item.message for item in report.errors)
    assert any("password" in item.message for item in report.warnings)
    assert any("pem_path" in item.message for item in report.warnings)
