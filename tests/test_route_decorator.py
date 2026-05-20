"""Tests for the @route decorator + collect_routes + build_router helpers."""

from __future__ import annotations

import pytest

from dryade_plugins_sdk import build_router, collect_routes, route
from dryade_plugins_sdk.route import RouteSpec


def test_route_decorator_stamps_canonical_meta():
    @route(path="/status", method="GET")
    def status() -> dict[str, bool]:
        return {"ok": True}

    meta = getattr(status, "_dryade_route_meta")
    assert meta == {
        "path": "/status",
        "method": "GET",
        "auth_required": True,
        "name": None,
    }


def test_route_decorator_keeps_legacy_spec_attribute():
    @route(path="/v1/echo", method="POST", auth_required=False, name="echo")
    def echo(body: dict) -> dict:
        return body

    assert isinstance(echo.spec, RouteSpec)
    assert echo.spec.path == "/v1/echo"
    assert echo.spec.method == "POST"
    assert echo.spec.auth_required is False
    assert echo.spec.name == "echo"


def test_collect_routes_returns_decorated_methods_only():
    class Plugin:
        @route(path="/a", method="GET")
        def handler_a(self):
            return "a"

        @route(path="/b", method="POST")
        def handler_b(self):
            return "b"

        def not_a_route(self):  # NOT decorated — must NOT be collected.
            return "no"

    p = Plugin()
    collected = collect_routes(p)
    paths = [meta["path"] for meta, _ in collected]
    # Both decorated handlers picked up.
    assert sorted(paths) == ["/a", "/b"]
    # `not_a_route` must not show up.
    assert "/c" not in paths
    assert len(collected) == 2


def test_collect_routes_ordering_is_stable_by_qualname():
    class Plugin:
        @route(path="/z", method="GET")
        def aaa(self):  # qualname sorts first
            return None

        @route(path="/a", method="GET")
        def bbb(self):
            return None

        @route(path="/m", method="GET")
        def ccc(self):
            return None

    p = Plugin()
    collected = collect_routes(p)
    # Ordering follows __qualname__, which goes aaa < bbb < ccc.
    assert [meta["path"] for meta, _ in collected] == ["/z", "/a", "/m"]


def test_collect_routes_handles_inherited_legacy_spec_attribute():
    """A method carrying only the legacy `spec` attribute is still discovered."""

    class Plugin:
        @route(path="/legacy", method="GET")
        def handler(self):
            return None

    p = Plugin()
    # Strip the canonical attribute to simulate a pre-1.1.2 plugin.
    delattr(type(p).handler, "_dryade_route_meta")
    collected = collect_routes(p)
    assert len(collected) == 1
    assert collected[0][0]["path"] == "/legacy"


def test_build_router_wires_decorated_methods_into_fastapi():
    fastapi = pytest.importorskip("fastapi")
    TestClient = pytest.importorskip("fastapi.testclient").TestClient  # noqa: N806

    class Plugin:
        @route(path="/ping", method="GET")
        def ping(self) -> dict[str, str]:
            return {"pong": "ok"}

        @route(path="/echo", method="POST")
        def echo(self, payload: dict | None = None) -> dict:
            return payload or {}

    p = Plugin()
    router = build_router(p)
    assert isinstance(router, fastapi.APIRouter)

    app = fastapi.FastAPI()
    app.include_router(router)
    client = TestClient(app)

    r = client.get("/ping")
    assert r.status_code == 200
    assert r.json() == {"pong": "ok"}

    r = client.post("/echo", json={"x": 1})
    assert r.status_code == 200
    assert r.json() == {"x": 1}


def test_build_router_returns_legacy_self_router_unchanged():
    """Plugins that pre-built their own router get that router back as-is."""
    fastapi = pytest.importorskip("fastapi")

    legacy = fastapi.APIRouter()

    @legacy.get("/legacy")
    def legacy_handler():
        return {"legacy": True}

    class Plugin:
        router = legacy

        @route(path="/new", method="GET")
        def new_handler(self):
            return {"new": True}

    p = Plugin()
    got = build_router(p)
    # No double-mount: build_router returns the plugin's legacy router untouched.
    assert got is legacy


def test_build_router_with_no_routes_returns_empty_router():
    pytest.importorskip("fastapi")

    class Plugin:
        pass

    got = build_router(Plugin())
    # Either an empty APIRouter (FastAPI installed) or None (not installed).
    # We installed FastAPI for the importorskip above, so this must be a router.
    assert got is not None
    # Empty router has no routes.
    assert getattr(got, "routes", []) == []
