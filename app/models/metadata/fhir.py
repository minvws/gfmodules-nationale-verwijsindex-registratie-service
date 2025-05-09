from typing import List

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

# These are not actual represetations of FHIR resources and types.
# It is just typings for the required fields needed to run the synchronization


class Identifier(BaseModel):
    model_config = ConfigDict(extra="allow")

    value: str
    system: str


class Meta(BaseModel):
    model_config = ConfigDict(extra="allow")

    last_updated: str = Field(
        alias="lastUpdated",
        validation_alias=AliasChoices("lastUpdated", "last_updated"),
    )


class Link(BaseModel):
    model_config = ConfigDict(extra="allow")

    relation: str
    url: str


class Resource(BaseModel):
    model_config = ConfigDict(extra="allow")

    meta: Meta
    identifier: List[Identifier] | None = None
    resource_type: str = Field(
        alias="resourceType",
        validation_alias=AliasChoices("resourceType", "resource_type"),
    )


class Entry(BaseModel):
    model_config = ConfigDict(extra="allow")

    resource: Resource
    meta: Meta | None = None


class Bundle(BaseModel):
    model_config = ConfigDict(extra="allow")

    link: List[Link]
    entry: List[Entry] | None = None
