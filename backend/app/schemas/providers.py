from __future__ import annotations

from pydantic import BaseModel


class ProviderResponse(BaseModel):
    id: str
    name: str
    logo_url: str = ""
    base_url: str = ""
    brand_color: str = "#000000"
    requires_subscription: bool = False
    is_active: bool = True
    priority: int = 100
    connected: bool = False

    model_config = {"from_attributes": True}


class ConnectRequest(BaseModel):
    provider_id: str
