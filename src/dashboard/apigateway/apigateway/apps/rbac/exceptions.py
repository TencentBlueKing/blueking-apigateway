class GatewayMemberError(Exception):
    """Base class for gateway member domain errors."""


class GatewayMemberInvalidArgumentError(GatewayMemberError):
    """Raised when gateway member arguments are invalid."""


class LastGatewayAdministratorError(GatewayMemberError):
    """Raised when an operation would remove the last gateway administrator."""


class GatewayMemberNotFoundError(GatewayMemberError):
    """Raised when a gateway member does not exist in the target gateway."""
