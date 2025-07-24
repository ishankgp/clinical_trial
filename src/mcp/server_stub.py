class InitializationOptions:
    def __init__(self, capabilities=None, tools=None):
        self.capabilities = capabilities or {}
        self.tools = tools or []


class Server:
    def __init__(self, name="clinical-trial-mcp-server-fixed"):
        self.name = name
        self._list_handlers = []
        self._call_handlers = []

    def list_tools(self):
        def decorator(func):
            self._list_handlers.append(func)
            return func

        return decorator

    def call_tool(self):
        def decorator(func):
            self._call_handlers.append(func)
            return func

        return decorator

    async def run(self, *args, **kwargs):
        pass

    def get_capabilities(self):
        return {}


class Tool:
    def __init__(self, name, description="", inputSchema=None):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema or {}


class ListToolsResult:
    def __init__(self, tools=None):
        self.tools = tools or []


class CallToolResult:
    def __init__(self, result=None):
        self.result = result


class ListToolsRequest: ...


class CallToolRequest: ...


class TextContent(str):
    pass


class ImageContent(str):
    pass


class EmbeddedResource(str):
    pass


class LoggingLevel:
    INFO = "INFO"
