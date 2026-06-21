from app.scrapers.base import RawJob


def test_fingerprint_dedupe():
    a = RawJob(source="x", external_id="1", title="Backend Engineer", company="Acme", location="Remote")
    b = RawJob(source="y", external_id="2", title="backend  engineer", company="ACME", location="remote")
    assert a.fingerprint() == b.fingerprint()


def test_fingerprint_differs():
    a = RawJob(source="x", external_id="1", title="Backend Engineer", company="Acme")
    b = RawJob(source="x", external_id="1", title="Frontend Engineer", company="Acme")
    assert a.fingerprint() != b.fingerprint()
