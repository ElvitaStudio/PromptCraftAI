class AssistantConfigurationError(RuntimeError):
    """Raised when an assistant API key is not configured."""


class AssistantAPIError(RuntimeError):
    """Raised when an assistant provider returns an invalid response."""
