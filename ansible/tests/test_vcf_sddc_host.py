"""Unit tests for vcf_sddc_host Ansible module."""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "library"))

from helpers import AnsibleExitJson, AnsibleFailJson, build_mock_module
from vcf_sddc_host import run_module


@pytest.fixture
def mock_module(module_args_base):
    """Patch AnsibleModule to capture exit/fail calls."""
    with patch("vcf_sddc_host.AnsibleModule") as mock_cls:
        params = {
            **module_args_base,
            "state": "commissioned",
            "hosts": [
                {
                    "fqdn": "esxi-05.lab.dreamfold.dev",
                    "username": "root",
                    "password": "test-pass",
                    "networkPoolName": "mgmt-pool",
                    "storageType": "VSAN",
                }
            ],
            "timeout": 10,
            "poll_interval": 1,
        }
        instance = build_mock_module(params)
        mock_cls.return_value = instance
        yield instance


class TestCommission:
    def test_successful_commission(self, mock_module):
        token_resp = {"accessToken": "test-token"}
        commission_resp = {"id": "task-456"}
        task_resp = {"id": "task-456", "status": "SUCCESSFUL"}

        with patch("vcf_sddc_host.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.side_effect = [
                json.dumps(token_resp).encode(),
                json.dumps(commission_resp).encode(),
                json.dumps(task_resp).encode(),
            ]
            mock_urlopen.return_value = mock_resp

            with pytest.raises(AnsibleExitJson) as exc_info:
                run_module()

        assert exc_info.value.kwargs["changed"] is True
        assert exc_info.value.kwargs["status"] == "SUCCESSFUL"

    def test_failed_commission(self, mock_module):
        token_resp = {"accessToken": "test-token"}
        commission_resp = {"id": "task-789"}
        task_resp = {"id": "task-789", "status": "FAILED", "errors": []}

        with patch("vcf_sddc_host.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.side_effect = [
                json.dumps(token_resp).encode(),
                json.dumps(commission_resp).encode(),
                json.dumps(task_resp).encode(),
            ]
            mock_urlopen.return_value = mock_resp

            with pytest.raises(AnsibleFailJson):
                run_module()


class TestDecommission:
    def test_decommission_by_fqdn(self, mock_module):
        mock_module.params["state"] = "absent"
        token_resp = {"accessToken": "test-token"}
        hosts_resp = {
            "elements": [
                {"id": "host-001", "fqdn": "esxi-05.lab.dreamfold.dev"},
                {"id": "host-002", "fqdn": "esxi-06.lab.dreamfold.dev"},
            ]
        }
        delete_resp = {}

        with patch("vcf_sddc_host.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.side_effect = [
                json.dumps(token_resp).encode(),
                json.dumps(hosts_resp).encode(),
                json.dumps(delete_resp).encode(),
            ]
            mock_urlopen.return_value = mock_resp

            with pytest.raises(AnsibleExitJson) as exc_info:
                run_module()

        assert exc_info.value.kwargs["changed"] is True


class TestCheckMode:
    def test_check_mode_no_action(self, mock_module):
        mock_module.check_mode = True

        with pytest.raises(AnsibleExitJson) as exc_info:
            run_module()

        assert exc_info.value.kwargs["changed"] is False
