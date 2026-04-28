"""Certificate management."""

import logging
from typing import Any, Dict, List

from vcf_sdk.managers.base import BaseManager
from vcf_sdk.models import CertificateAuthority, Certificate, CSR

logger = logging.getLogger(__name__)


class CertificateManager(BaseManager):
    """Certificate Authority, CSR, and certificate management."""

    # Certificate Authorities

    def list_cas(self) -> List[CertificateAuthority]:
        """List all certificate authorities."""
        response = self._get("/v1/certificate-authorities")
        return [CertificateAuthority(**ca) for ca in response.get("elements", [])]

    def create_ca(self, spec: Dict[str, Any]) -> CertificateAuthority:
        """Configure a certificate authority."""
        response = self._post("/v1/certificate-authorities", data=spec)
        return CertificateAuthority(**response)

    def delete_ca(self, ca_id: str) -> None:
        """Remove a certificate authority."""
        self._delete(f"/v1/certificate-authorities/{ca_id}")

    def set_microsoft_ca(
        self, server_url: str, username: str, password: str, template_name: str
    ) -> None:
        """
        Configure Microsoft Certificate Authority integration.

        Args:
            server_url: HTTPS URL for the Microsoft CA (e.g., https://ca.lab.dev/certsrv)
            username: CA username
            password: CA password
            template_name: Certificate template name (e.g., VMware)
        """
        spec = {
            "microsoftCertificateAuthoritySpec": {
                "serverUrl": server_url,
                "username": username,
                "secret": password,
                "templateName": template_name,
            }
        }
        self._put("/v1/certificate-authorities", data=spec)

    def set_openssl_ca(
        self,
        common_name: str,
        organization: str,
        organization_unit: str,
        locality: str,
        state: str,
        country: str,
    ) -> None:
        """
        Configure OpenSSL Certificate Authority integration.

        Args:
            common_name: CA common name (e.g., sddc-manager.lab.dev)
            organization: Organization name
            organization_unit: Organizational unit
            locality: City/locality
            state: State/province
            country: Two-letter country code
        """
        spec = {
            "openSSLCertificateAuthoritySpec": {
                "commonName": common_name,
                "organization": organization,
                "organizationUnit": organization_unit,
                "locality": locality,
                "state": state,
                "country": country,
            }
        }
        self._put("/v1/certificate-authorities", data=spec)

    # CSRs

    def get_csrs(self, domain_name: str) -> List[CSR]:
        """Get CSRs for a domain."""
        response = self._get(f"/v1/domains/{domain_name}/csrs")
        return [CSR(**c) for c in response.get("elements", [])]

    def generate_csrs(self, domain_name: str, spec: Dict[str, Any]) -> List[CSR]:
        """Generate CSRs for a domain's resources."""
        response = self._put(f"/v1/domains/{domain_name}/csrs", data=spec)
        return [CSR(**c) for c in response.get("elements", [])]

    # Certificates

    def get_certificates(self, domain_name: str) -> List[Certificate]:
        """Get certificates for a domain."""
        response = self._get(f"/v1/domains/{domain_name}/certificates")
        return [Certificate(**c) for c in response.get("elements", [])]

    def request_certificates(self, domain_name: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Request certificates for a domain (from CA)."""
        return self._put(f"/v1/domains/{domain_name}/certificates", data=spec)

    def install_certificates(self, domain_name: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Install certificates on a domain's resources."""
        return self._patch(f"/v1/domains/{domain_name}/certificates", data=spec)
