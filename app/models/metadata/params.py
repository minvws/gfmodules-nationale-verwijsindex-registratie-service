from pydantic import AliasChoices, BaseModel, Field


class MetadataResourceParams(BaseModel):
    last_updated: str | None = Field(
        alias="_lastUpdated",
        validation_alias=AliasChoices("_lastUpdated", "last_updated"),
        default=None,
    )
    include: str | None = Field(
        alias="_include",
        validation_alias=AliasChoices("_include", "include"),
        default=None,
    )
