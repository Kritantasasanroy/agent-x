"""Parsing tests for every scraper, with httpx mocked (no real network)."""

from __future__ import annotations

import app.scrapers.ashby as ashby_mod
import app.scrapers.greenhouse as gh_mod
import app.scrapers.lever as lever_mod
import app.scrapers.remoteok as rok_mod
import app.scrapers.weworkremotely as wwr_mod
import app.scrapers.ycombinator as yc_mod


class FakeResp:
    def __init__(self, json_data=None, text="", status_code=200):
        self._json = json_data
        self.text = text
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_greenhouse_parse(monkeypatch):
    payload = {
        "jobs": [
            {
                "id": 123,
                "title": "Backend Engineer",
                "location": {"name": "Remote"},
                "content": "Build &amp; ship Python APIs",
                "absolute_url": "https://boards.greenhouse.io/acme/jobs/123",
            }
        ]
    }
    monkeypatch.setattr(gh_mod.httpx, "get", lambda *a, **k: FakeResp(json_data=payload))
    jobs = gh_mod.GreenhouseScraper(boards=["acme"]).fetch(limit=10)
    assert len(jobs) == 1
    j = jobs[0]
    assert j.source == "greenhouse"
    assert j.title == "Backend Engineer"
    assert j.company == "acme"
    assert j.remote is True
    assert "&amp;" not in j.description and "Build & ship" in j.description
    assert j.raw["board"] == "acme" and str(j.raw["gh_id"]) == "123"


def test_greenhouse_no_boards_returns_empty(monkeypatch):
    # never calls network when no boards configured
    monkeypatch.setattr(gh_mod.httpx, "get", lambda *a, **k: (_ for _ in ()).throw(AssertionError))
    assert gh_mod.GreenhouseScraper(boards=[]).fetch() == []


def test_lever_parse(monkeypatch):
    payload = [
        {
            "id": "abc",
            "text": "Senior Developer",
            "categories": {"location": "Remote - US", "commitment": "Full-time"},
            "descriptionPlain": "Python work",
            "hostedUrl": "https://jobs.lever.co/acme/abc",
        }
    ]
    monkeypatch.setattr(lever_mod.httpx, "get", lambda *a, **k: FakeResp(json_data=payload))
    jobs = lever_mod.LeverScraper(companies=["acme"]).fetch()
    assert len(jobs) == 1
    assert jobs[0].title == "Senior Developer"
    assert jobs[0].remote is True
    assert jobs[0].apply_url.endswith("/abc")


def test_ashby_parse(monkeypatch):
    payload = {
        "jobs": [
            {
                "id": "x1",
                "title": "ML Engineer",
                "location": "New York",
                "descriptionPlain": "PyTorch and ML",
                "isRemote": False,
                "jobUrl": "https://jobs.ashbyhq.com/acme/x1",
            }
        ]
    }
    monkeypatch.setattr(ashby_mod.httpx, "get", lambda *a, **k: FakeResp(json_data=payload))
    jobs = ashby_mod.AshbyScraper(orgs=["acme"]).fetch()
    assert len(jobs) == 1
    assert jobs[0].title == "ML Engineer"
    assert jobs[0].remote is False


def test_yc_picks_official_thread_and_skips_noise(monkeypatch):
    search = {
        "hits": [
            {"objectID": "111", "title": "Ask HN: Who is hiring? (June 2026)", "created_at_i": 1000},
            {"objectID": "222", "title": "Ask HN: Who wants to be hired?", "created_at_i": 2000},
            {"objectID": "333", "title": "A random story about hiring trends", "created_at_i": 3000},
        ]
    }
    item = {
        "children": [
            {"id": 1, "author": "acmeco", "text": "<p>AcmeCo | Backend Engineer | Remote | Python</p>"},
            {"id": 2, "author": "whoishiring", "text": "<p>meta sub-thread</p>"},
            {"id": 3, "author": "foo", "text": ""},
        ]
    }

    def fake_get(url, params=None, timeout=None):
        if "/search" in url:
            return FakeResp(json_data=search)
        return FakeResp(json_data=item)

    monkeypatch.setattr(yc_mod.httpx, "get", fake_get)
    jobs = yc_mod.YCombinatorScraper().fetch()
    # only the official "Who is hiring?" thread is used; only the real job comment survives
    assert len(jobs) == 1
    assert jobs[0].company == "AcmeCo"
    assert jobs[0].title == "Backend Engineer"
    assert jobs[0].remote is True


def test_remoteok_parse_skips_legal_notice(monkeypatch):
    data = [
        {"legal": "notice — first element has no id"},
        {
            "id": 1,
            "position": "Backend Engineer",
            "company": "Acme",
            "location": "Remote",
            "description": "<b>Python</b> role",
            "url": "https://remoteok.com/x",
            "tags": ["python"],
        },
    ]
    monkeypatch.setattr(rok_mod.httpx, "get", lambda *a, **k: FakeResp(json_data=data))
    jobs = rok_mod.RemoteOKScraper().fetch()
    assert len(jobs) == 1
    assert jobs[0].title == "Backend Engineer"
    assert "<b>" not in jobs[0].description


def test_wwr_parse(monkeypatch):
    rss = (
        '<?xml version="1.0"?><rss><channel>'
        "<item><title>Acme: Backend Engineer</title>"
        "<link>https://weworkremotely.com/remote-jobs/acme-be</link>"
        "<description>&lt;b&gt;Python&lt;/b&gt;</description></item>"
        "</channel></rss>"
    )
    monkeypatch.setattr(wwr_mod.httpx, "get", lambda *a, **k: FakeResp(text=rss))
    jobs = wwr_mod.WeWorkRemotelyScraper().fetch()
    assert jobs
    assert jobs[0].company == "Acme"
    assert "Backend Engineer" in jobs[0].title
