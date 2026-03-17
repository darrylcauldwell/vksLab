"""Shared test fixtures for vkslab-esxi."""

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_config(tmp_path: Path) -> Path:
    """Create a sample lab config YAML for testing."""
    config = tmp_path / "lab.yaml"
    config.write_text("""\
domain: lab.dreamfold.dev
gateway: 10.0.10.1
dns_server: 10.0.10.2
ntp_servers:
  - 10.0.10.2
  - 10.0.10.1
esxi_password: testpass123

hosts:
  - name: esxi-01
    ip: 10.0.10.11
    mac: "00:50:56:aa:bb:01"
    domain: management
  - name: esxi-02
    ip: 10.0.10.12
    mac: "00:50:56:aa:bb:02"
    domain: management
  - name: esxi-03
    ip: 10.0.10.13
    mac: "00:50:56:aa:bb:03"
    domain: management
  - name: esxi-04
    ip: 10.0.10.14
    mac: "00:50:56:aa:bb:04"
    domain: management
  - name: esxi-05
    ip: 10.0.10.15
    mac: "00:50:56:aa:bb:05"
    domain: workload
  - name: esxi-06
    ip: 10.0.10.16
    mac: "00:50:56:aa:bb:06"
    domain: workload
  - name: esxi-07
    ip: 10.0.10.17
    mac: "00:50:56:aa:bb:07"
    domain: workload
""")
    return config
