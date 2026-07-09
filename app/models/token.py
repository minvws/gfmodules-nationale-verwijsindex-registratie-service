from pydantic import BaseModel, Field
import time

TOKEN_EXPIRES_IN = 600  # 10 minutes


class AccessToken(BaseModel):
    access_token: str
    scope: str
    expires_in: int | None = None
    added_at: int = Field(default_factory=lambda: int(time.time()))

    def has_scope(self, scope: str) -> bool:
        token_scopes = self.scope.split()
        requested_scopes = scope.split()
        return all(s in token_scopes for s in requested_scopes)

    @property
    def is_expired(self) -> bool:
        expires_in = self.expires_in or TOKEN_EXPIRES_IN
        return (self.added_at + expires_in) <= int(time.time())
