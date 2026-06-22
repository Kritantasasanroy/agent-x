"""Config: CSV list parsing + scraper enable flags."""

from __future__ import annotations

from app.core.config import Settings


def test_csv_list_helpers():
    s = Settings(greenhouse_boards="a, b ,c", lever_companies="", ashby_orgs="x")
    assert s.greenhouse_boards_list() == ["a", "b", "c"]
    assert s.lever_companies_list() == []
    assert s.ashby_orgs_list() == ["x"]


def test_enabled_scrapers_reflect_flags():
    s = Settings(
        enable_remoteok=True, enable_weworkremotely=False, enable_ycombinator=False,
        enable_greenhouse=True, enable_lever=False, enable_ashby=True,
    )
    enabled = s.enabled_scrapers()
    assert "remoteok" in enabled
    assert "greenhouse" in enabled
    assert "ashby" in enabled
    assert "weworkremotely" not in enabled
    assert "lever" not in enabled


def test_restricted_sources_off_by_default():
    s = Settings()
    enabled = s.enabled_scrapers()
    for blocked in ("linkedin", "indeed", "glassdoor", "wellfound", "naukri", "foundit"):
        assert blocked not in enabled


def test_real_apply_off_by_default():
    assert Settings().enable_real_apply is False
