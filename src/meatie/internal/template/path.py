import re
from typing import Any

from typing_extensions import Self

_param_pattern = re.compile(r"{(?P<name>[a-zA-Z_]\w*?)}")  # Matches {name} for parameters
_cond_pattern = re.compile(
    r"\[(?P<name>[a-zA-Z_]\w*?)(?::(?P<content>[^]]+))?\]"
)  # Matches [name] and [name:content]


class PathTemplate:
    """
    A template class for constructing and formatting paths with dynamic parameters
    and conditionally included content.

    Example:
        template = PathTemplate.from_string("/{endpoint}/[all]/[event:events]")
        result = template.format(endpoint="users", all=True, event=False)
        # result -> "/users/all/"
    """

    __slots__ = ("template", "parameters", "conditionals")

    def __init__(self, template: str, parameters: list[str], conditionals: dict[str, str]) -> None:
        self.template = template  # Raw template string
        self.parameters = parameters  # List of {name} parameters
        self.conditionals = conditionals  # Dictionary of [name] or [name:content] conditionals

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, PathTemplate):
            return (
                self.template == other.template
                and self.parameters == other.parameters
                and self.conditionals == other.conditionals
            )
        if isinstance(other, str):
            return self.template == other
        return False

    def __contains__(self, item: str) -> bool:
        return item in self.parameters or item in self.conditionals

    def __hash__(self):
        return hash(self.template)

    def __str__(self):
        return self.template

    def format(self, **kwargs: dict[str, Any]) -> str:
        """Substitute parameters and handle conditional insertions within the template."""

        missing_params = [param for param in self.parameters if param not in kwargs]
        # Missing conditionals will just be False
        if missing_params:
            raise KeyError(
                f"Missing required parameters or conditionals: {', '.join(missing_params)}"
            )

        result = self.template
        result = self._process_conditionals(result, kwargs)
        return result.format(**kwargs)

    def _process_conditionals(self, result: str, kwargs: dict[str, Any]) -> str:
        """Process conditional patterns based on provided arguments."""
        for name, content in self.conditionals.items():
            pattern = f"[{name}]" if not content else f"[{name}:{content}]"
            result = self._replace_conditional(result, pattern, name, content, kwargs)
        return result

    def _replace_conditional(
        self, result: str, pattern: str, name: str, content: str, kwargs: dict[str, Any]
    ) -> str:
        """Replace or remove a conditional pattern based on its truthiness."""
        if kwargs.get(name, False):
            to_insert = content or name
            return re.sub(rf"(/?){re.escape(pattern)}(/?)", r"\1" + to_insert + r"\2", result)
        return re.sub(
            rf"(/?){re.escape(pattern)}(/?)",
            lambda m: "/" if m.group(1) and m.group(2) else "",
            result,
        )

    @classmethod
    def from_string(cls, template: str) -> Self:
        """Create a PathTemplate instance from a template string."""
        parameters = [match.group("name") for match in _param_pattern.finditer(template)]
        conditionals = {
            match.group("name"): match.group("content") or ""
            for match in _cond_pattern.finditer(template)
        }
        return cls(template, parameters, conditionals)
