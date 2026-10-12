"""Hardened YAML reader for the knowledge files (spec 008 FR-008-07).

PyYAML's safe loader is extended because its defaults would hide errors: the last duplicate key silently wins,
aliases share
objects (alias bombs), and unquoted dates become `datetime` objects. This reader rejects, before any value is
constructed,
files over 1 MiB, invalid UTF-8, anchors and aliases, tags outside the YAML core schema, merge keys, repeated mapping
keys,
nesting deeper than 8 levels and several documents. PyYAML is imported on first use, so importing the package reads
nothing.
"""

from __future__ import annotations

from typing import Any

__all__ = ["MAX_BYTES", "MAX_DEPTH", "YamlRejected", "load_document"]

MAX_BYTES = 1_048_576
MAX_DEPTH = 8

_CORE_TAGS = frozenset("tag:yaml.org,2002:" + name for name in ("str", "int", "float", "bool", "null", "map", "seq"))
_MERGE_TAG = "tag:yaml.org,2002:merge"
_loader_class: type | None = None


class YamlRejected(ValueError):
    """The file violates a hardening rule; the message names the rule."""


def _make_loader() -> type:
    import yaml

    class _KnowledgeLoader(yaml.SafeLoader):
        yaml_implicit_resolvers = {  # noqa: RUF012
            first: [(tag, regexp) for tag, regexp in entries if tag != "tag:yaml.org,2002:timestamp"]
            for first, entries in yaml.SafeLoader.yaml_implicit_resolvers.items()
        }

        def __init__(self, stream: str) -> None:
            super().__init__(stream)
            self._depth = 0

        def compose_node(self, parent: Any, index: Any) -> Any:
            if self.check_event(yaml.events.AliasEvent):
                raise YamlRejected("aliases are not allowed")
            event = self.peek_event()
            if event.anchor is not None:
                raise YamlRejected("anchors are not allowed")
            if event.tag is not None and event.tag not in _CORE_TAGS:
                raise YamlRejected(f"tag {event.tag!r} is outside the YAML core schema")
            collection = isinstance(event, yaml.events.MappingStartEvent | yaml.events.SequenceStartEvent)
            if collection:
                self._depth += 1
                if self._depth > MAX_DEPTH:
                    raise YamlRejected(f"nesting is deeper than {MAX_DEPTH} levels")
            try:
                return super().compose_node(parent, index)
            finally:
                if collection:
                    self._depth -= 1

        def construct_mapping(self, node: Any, deep: bool = False) -> Any:
            seen: set[Any] = set()
            for key_node, _ in node.value:
                if key_node.tag == _MERGE_TAG:
                    raise YamlRejected("merge keys are not allowed")
                key = self.construct_object(key_node, deep=True)
                try:
                    duplicate = key in seen
                except TypeError:
                    raise YamlRejected("a mapping key is not a scalar") from None
                if duplicate:
                    raise YamlRejected(f"repeated mapping key {key!r}")
                seen.add(key)
            return super().construct_mapping(node, deep)

    return _KnowledgeLoader


def load_document(raw: bytes) -> Any:
    """Parse one knowledge YAML document from bytes; raises `YamlRejected` with the violated rule."""
    global _loader_class
    if len(raw) > MAX_BYTES:
        raise YamlRejected(f"the file is larger than {MAX_BYTES} bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as err:
        raise YamlRejected(f"the file is not valid UTF-8: {err.reason}") from None
    import yaml

    if _loader_class is None:
        _loader_class = _make_loader()
    loader = _loader_class(text)
    try:
        node = loader.get_single_node()
        if node is None:
            return None
        return loader.construct_document(node)
    except YamlRejected:
        raise
    except yaml.YAMLError as err:
        raise YamlRejected(f"not valid YAML: {str(err).splitlines()[0] if str(err) else type(err).__name__}") from None
    except RecursionError:
        raise YamlRejected("the document is nested too deeply") from None
    finally:
        loader.dispose()
