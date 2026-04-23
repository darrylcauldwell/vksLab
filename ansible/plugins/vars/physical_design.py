"""
Ansible vars plugin that reads configuration from the physical design markdown.

The physical design document (docs/markdown/physical-design.md) is the
authoritative source for lab configuration. Tables tagged with HTML comments
(e.g., <!-- pd_vlans -->) are parsed and injected as Ansible variables.

Tagged tables:
  <!-- pd_vlans -->   → pd_vlans (list of dicts: vlan_id, name, subnet, gateway, mtu)
  <!-- pd_hosts -->   → pd_hosts (list of dicts: ip, hostname, domain, role)
  <!-- pd_ip_pools -->→ pd_ip_pools (list of dicts: pool_name, start_ip, end_ip, ...)
  <!-- pd_bgp -->     → pd_bgp (list of dicts: peer_name, ip, asn, role)

Usage in ansible.cfg:
  [defaults]
  vars_plugins_enabled = host_group_vars,physical_design

Column names in the markdown tables become dict keys directly — no
transformation needed. Use snake_case column names in the document.
"""

import os
import re
from typing import Any, Dict, List

from ansible.plugins.vars import BaseVarsPlugin

DOCUMENTATION = """
    name: physical_design
    version_added: "1.0"
    short_description: Load variables from physical-design.md
    description:
        - Reads the physical design markdown and parses tagged tables into variables.
    options: {}
"""

# Integer fields — values are cast to int during parsing
INT_FIELDS = {"vlan_id", "mtu", "asn"}


def parse_markdown_table(lines: List[str]) -> List[Dict[str, Any]]:
    """Parse a markdown table into a list of dicts."""
    if len(lines) < 3:
        return []

    headers = [h.strip() for h in lines[0].strip("|").split("|")]
    rows = []
    for line in lines[2:]:
        line = line.strip()
        if not line or not line.startswith("|"):
            break
        values = [v.strip() for v in line.strip("|").split("|")]
        if len(values) == len(headers):
            row = {}
            for key, val in zip(headers, values):
                if key in INT_FIELDS:
                    try:
                        row[key] = int(val)
                    except ValueError:
                        row[key] = val
                else:
                    row[key] = val
            rows.append(row)
    return rows


def parse_tagged_tables(content: str) -> Dict[str, List[Dict[str, Any]]]:
    """Find all <!-- pd_xxx --> tagged tables and parse them."""
    result = {}
    lines = content.split("\n")

    for i, line in enumerate(lines):
        match = re.match(r"^<!--\s+(pd_\w+)\s+-->", line.strip())
        if match:
            tag = match.group(1)
            # Find the next table (lines starting with |)
            table_lines = []
            for j in range(i + 1, len(lines)):
                stripped = lines[j].strip()
                if stripped.startswith("|"):
                    table_lines.append(stripped)
                elif table_lines:
                    break  # End of table
            if table_lines:
                result[tag] = parse_markdown_table(table_lines)

    return result


def parse_physical_design(filepath: str) -> Dict[str, Any]:
    """Parse the physical design markdown and return variables."""
    with open(filepath) as f:
        content = f.read()

    return parse_tagged_tables(content)


class VarsModule(BaseVarsPlugin):
    """Read variables from physical-design.md."""

    REQUIRES_ENABLED = True

    def get_vars(self, loader, path, entities, cache=True):
        """Return variables parsed from the physical design document."""
        super().get_vars(loader, path, entities)

        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        ansible_dir = os.path.dirname(os.path.dirname(plugin_dir))
        repo_root = os.path.dirname(ansible_dir)
        doc_path = os.path.join(repo_root, "docs", "markdown", "physical-design.md")

        if not os.path.exists(doc_path):
            return {}

        try:
            return parse_physical_design(doc_path)
        except Exception:
            return {}
