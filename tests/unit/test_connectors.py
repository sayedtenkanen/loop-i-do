"""Tests for ConnectorRegistry."""

from loop_engineering.connectors import Connector, ConnectorRegistry


class TestConnector:
    def test_connector_creation(self):
        def my_tool(x: str) -> str:
            return f"result: {x}"

        conn = Connector(
            name="test",
            description="A test tool",
            input_schema={"type": "object", "properties": {"x": {"type": "string"}}},
            fn=my_tool,
        )
        assert conn.name == "test"
        assert conn.description == "A test tool"

    def test_to_tool_spec(self):
        def my_tool(x: str) -> str:
            return f"result: {x}"

        conn = Connector(
            name="test",
            description="A test tool",
            input_schema={"type": "object"},
            fn=my_tool,
        )
        spec = conn.to_tool_spec()
        assert spec["name"] == "test"
        assert spec["description"] == "A test tool"
        assert "input_schema" in spec


class TestConnectorRegistry:
    def test_register_and_call(self):
        registry = ConnectorRegistry()

        schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        @registry.register("greet", "Say hello", schema)
        def greet(name: str) -> str:
            return f"Hello, {name}!"

        result = registry.call("greet", name="World")
        assert result == "Hello, World!"

    def test_unknown_connector_returns_error(self):
        registry = ConnectorRegistry()
        result = registry.call("nonexistent")
        assert "error" in result

    def test_tool_specs(self):
        registry = ConnectorRegistry()

        @registry.register("tool1", "Tool 1", {"type": "object"})
        def tool1() -> str:
            return "1"

        specs = registry.tool_specs()
        assert len(specs) == 1
        assert specs[0]["name"] == "tool1"
