from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    status: str
    services: dict[str, str]