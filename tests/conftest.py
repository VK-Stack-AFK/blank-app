import pytest

@pytest.fixture(autouse=True)
def isolated_storage(tmp_path,monkeypatch):
    monkeypatch.setenv('HOMEGUARD_DATA_DIR',str(tmp_path/'runtime'))

@pytest.fixture
def complete_home():
    from homeguard.synthetic import synthetic_application
    return synthetic_application(3,'A',900)
