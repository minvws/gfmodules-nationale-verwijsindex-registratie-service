from pydantic import BaseModel, Field
import time

TOKEN_EXPIRES_IN = 600  # 10 minutes
TOKEN_EXPIRY_BUFFER = 30  # Refresh token 30 seconds before expiry
REFRESH_TOKEN_EXPIRES_IN = 3600  # 1 hour


class AccessToken(BaseModel):
    access_token: str
    token_type: str
    scope: str
    refresh_token: str | None = None
    expires_in: int | None = None
    added_at: int = Field(default_factory=lambda: int(time.time()))
    target_audience: str | None = None

    def has_scope_and_target_audience(self, scope: str, target_audience: str) -> bool:
        """
        Checks if this token has all the requested scopes and matches the target audience.
        """
        token_scopes = self.scope.split()
        requested_scopes = scope.split()
        return all(s in token_scopes for s in requested_scopes) and self.target_audience == target_audience

    @property
    def is_expired(self) -> bool:
        expires_in = self.expires_in or TOKEN_EXPIRES_IN
        return (self.added_at + expires_in - TOKEN_EXPIRY_BUFFER) <= int(time.time())

    @property
    def is_refresh_token_expired(self) -> bool:
        if self.refresh_token is None:
            return True
        return (self.added_at + REFRESH_TOKEN_EXPIRES_IN - TOKEN_EXPIRY_BUFFER) <= int(time.time())

    @property
    def can_refresh(self) -> bool:
        return self.refresh_token is not None and not self.is_refresh_token_expired
