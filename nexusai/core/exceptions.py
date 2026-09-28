"""
NexusAI Domain Exceptions.
Clean domain-level exception hierarchy for LLD error handling.
"""


class NexusException(Exception):
    """Base exception for all domain-specific NexusAI errors."""
    pass


class AuthenticationError(NexusException):
    """Raised when authentication fails or token is invalid."""
    pass


class UserNotFoundError(NexusException):
    """Raised when a user account cannot be found."""
    pass


class ThreadNotFoundError(NexusException):
    """Raised when a conversation thread cannot be found or is unauthorized."""
    pass


class CredentialVaultError(NexusException):
    """Raised when an operation on the credential vault fails."""
    pass


class AgentExecutionError(NexusException):
    """Raised when the LangGraph agent orchestrator encounters an execution failure."""
    pass
