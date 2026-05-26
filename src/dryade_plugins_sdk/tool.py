"""Tool Protocol — what a plugin tool must satisfy."""

from __future__ import annotations

from typing import Any, Callable, Protocol, runtime_checkable

from pydantic import BaseModel


class ToolSchema(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any] = {}
    output_schema: dict[str, Any] = {}
    lim_callable: bool = True  # is this tool LLM-callable via Plugin Tool Bridge?


@runtime_checkable
class Tool(Protocol):
    schema: ToolSchema

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


def tool(*, name: str, description: str, lim_callable: bool = True) -> Callable[..., Any]:
    """Decorator that marks a function as a plugin tool.

    Usage:
        @tool(name="my_tool", description="example")
        def my_tool(x: int) -> int:
            return x + 1
    """

    def _wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
        fn.schema = ToolSchema(  # type: ignore[attr-defined]
            name=name,
            description=description,
            input_schema={},
            output_schema={},
            lim_callable=lim_callable,
        )
        return fn

    return _wrap
