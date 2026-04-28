"""System configuration models for SDDC Manager API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DNSConfiguration(BaseModel):
    """DNS configuration response model."""

    dns_servers: Optional[List[Dict[str, str]]] = Field(default=None, alias="dnsServers")
    search_domains: Optional[List[str]] = Field(default=None, alias="searchDomains")

    model_config = ConfigDict(populate_by_name=True)


class NTPConfiguration(BaseModel):
    """NTP configuration response model."""

    ntp_servers: Optional[List[Dict[str, str]]] = Field(default=None, alias="ntpServers")

    model_config = ConfigDict(populate_by_name=True)


class BackupConfiguration(BaseModel):
    """Backup configuration response model."""

    server: Optional[str] = Field(default=None)
    port: Optional[int] = Field(default=None)
    protocol: Optional[str] = Field(default=None)
    username: Optional[str] = Field(default=None)
    directory: Optional[str] = Field(default=None)
    backup_schedule: Optional[Dict[str, Any]] = Field(default=None, alias="backupSchedule")
    encryption: Optional[Dict[str, Any]] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class DepotConfiguration(BaseModel):
    """Depot settings response model."""

    vmware_account: Optional[Dict[str, Any]] = Field(default=None, alias="vmwareAccount")

    model_config = ConfigDict(populate_by_name=True)


class ProxyConfiguration(BaseModel):
    """Proxy configuration response model."""

    host: Optional[str] = Field(default=None)
    port: Optional[int] = Field(default=None)
    is_enabled: Optional[bool] = Field(default=None, alias="isEnabled")

    model_config = ConfigDict(populate_by_name=True)


class HealthSummary(BaseModel):
    """Health summary response model."""

    id: str = Field(description="Health check ID")
    status: Optional[str] = Field(default=None)
    health_check_count: Optional[int] = Field(default=None, alias="healthCheckCount")
    health_checks: Optional[List[Dict[str, Any]]] = Field(
        default=None, alias="healthChecks"
    )

    model_config = ConfigDict(populate_by_name=True)
