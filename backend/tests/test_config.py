from app.core.config import env_list


def test_lan_lists_come_from_environment(monkeypatch):
    monkeypatch.setenv("APP_ALLOWED_HOSTS", " 192.168.1.20 , localhost,,")
    assert env_list("APP_ALLOWED_HOSTS", ("127.0.0.1",)) == ("192.168.1.20", "localhost")


def test_empty_environment_keeps_loopback_defaults(monkeypatch):
    monkeypatch.setenv("APP_ALLOWED_ORIGINS", " , ")
    assert env_list("APP_ALLOWED_ORIGINS", ("http://127.0.0.1:5173",)) == ("http://127.0.0.1:5173",)
    monkeypatch.delenv("APP_ALLOWED_HOSTS", raising=False)
    assert env_list("APP_ALLOWED_HOSTS", ("localhost",)) == ("localhost",)
