"""Certificate models for SDDC Manager API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CertificateAuthority(BaseModel):
    """Certificate Authority response model."""

    id: str = Field(description="CA UUID")
    server_url: Optional[str] = Field(default=None, alias="serverUrl")
    username: Optional[str] = Field(default=None)
    ca_type: Optional[str] = Field(
        default=None, alias="caType",
        description="Microsoft or OpenSSL"
    )

    model_config = ConfigDict(populate_by_name=True)


class Certificate(BaseModel):
    """Certificate response model."""

    domain: Optional[str] = Field(default=None)
    certificates: Optional[List[Dict[str, Any]]] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class CSR(BaseModel):
    """Certificate Signing Request response model."""

    csr_string: Optional[str] = Field(default=None, alias="csrString")
    resource: Optional[Dict[str, Any]] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)
