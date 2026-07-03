import asyncio

import pytest

from bot.storage import TokenStore


def _run(coro):
    return asyncio.run(coro)


def test_set_get_delete(tmp_path):
    store = TokenStore(str(tmp_path / "tokens.json"))
    rec = {"athlete_id": 1, "name": "@vasya", "access_token": "a",
           "refresh_token": "r", "expires_at": 123}

    async def scenario():
        await store.set(42, rec)
        got = await store.get(42)
        assert got == rec
        allrows = await store.all()
        assert "42" in allrows
        assert await store.delete(42) is True
        assert await store.get(42) is None
        assert await store.delete(42) is False

    _run(scenario())


def test_missing_file_is_empty(tmp_path):
    store = TokenStore(str(tmp_path / "nope.json"))
    assert _run(store.all()) == {}
    assert _run(store.get(1)) is None


def test_persists_across_instances(tmp_path):
    path = str(tmp_path / "t.json")
    _run(TokenStore(path).set(7, {"name": "@x"}))
    got = _run(TokenStore(path).get(7))
    assert got == {"name": "@x"}
