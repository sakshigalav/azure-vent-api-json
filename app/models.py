from typing import List
from pydantic import BaseModel, Field


class SubnetRequest(BaseModel):
    name: str = Field(min_length=1)
    address_prefix: str = Field(min_length=1)


class VNetRequest(BaseModel):
    name: str = Field(min_length=1)
    resource_group: str = Field(min_length=1)
    location: str = Field(min_length=1)
    address_space: List[str] = Field(min_length=1)
    subnets: List[SubnetRequest] = Field(min_length=1)


class SubnetResponse(BaseModel):
    name: str
    address_prefix: str


class VNetResponse(BaseModel):
    id: str
    name: str
    resource_group: str
    location: str
    address_space: List[str]
    subnets: List[SubnetResponse]
