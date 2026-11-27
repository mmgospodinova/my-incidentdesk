from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from incidentdesk.api import postmortems as postmortems_api
from incidentdesk.postmortems import postmortem_markdown


def complete_postmortem():
    return SimpleNamespace(
        title="Billing service is down",
        incident=SimpleNamespace(key="INC-4708"),
        summary="Billing was unavailable for 81 minutes.",
        impact="12% of billing requests failed.",
        root_cause="A dependency released a breaking change.",
        actions=[
            "Pin the dependency version",
            "Add a compatibility test",
        ],
    )


def test_complete_postmortem_has_exact_markdown_content():
    """Proves: the complete postmortem export contains the title, incident, Summary, Impact, Root cause, and unchecked Actions checklist."""
    assert postmortem_markdown(complete_postmortem()) == (
        "# Billing service is down\n"
        "\n"
        "Incident: INC-4708\n"
        "\n"
        "## Summary\n"
        "\n"
        "Billing was unavailable for 81 minutes.\n"
        "\n"
        "## Impact\n"
        "\n"
        "12% of billing requests failed.\n"
        "\n"
        "## Root cause\n"
        "\n"
        "A dependency released a breaking change.\n"
        "\n"
        "## Actions\n"
        "\n"
        "- [ ] Pin the dependency version\n"
        "- [ ] Add a compatibility test\n"
    )


def test_export_postmortem_returns_markdown_content_type(monkeypatch):
    """Proves: GET /postmortems/{key}/export.md returns a text/markdown response."""
    monkeypatch.setattr(
        postmortems_api,
        "get_postmortem",
        lambda session, key: complete_postmortem(),
    )

    response = postmortems_api.export_postmortem("PM-101", object())

    assert response.headers["content-type"].partition(";")[0] == "text/markdown"
    assert response.body.decode() == postmortem_markdown(complete_postmortem())


@pytest.mark.parametrize("root_cause", [None, ""])
def test_postmortem_without_root_cause_is_not_exported(monkeypatch, root_cause):
    """Proves: a draft without a root cause is not exported and GET /postmortems/{key}/export.md returns 404."""
    postmortem = complete_postmortem()
    postmortem.root_cause = root_cause
    monkeypatch.setattr(
        postmortems_api,
        "get_postmortem",
        lambda session, key: postmortem,
    )

    with pytest.raises(HTTPException) as exc_info:
        postmortems_api.export_postmortem("PM-101", object())

    assert exc_info.value.status_code == 404
