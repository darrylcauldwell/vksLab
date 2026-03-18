"""Unit tests for vcf_sddc_domain Ansible module."""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "library"))

from helpers import AnsibleExitJson, AnsibleFailJson, build_mock_module
from vcf_sddc_domain import run_module


@pytest.fixture
def mock_module(module_args_base):
    """Patch AnsibleModule to capture exit/fail calls."""
    with patch("vcf_sddc_domain.AnsibleModule") as mock_cls:
        params = {
            **module_args_base,
            "state": "present",
            "domain_spec": {
                "domainName": "workload-domain",
                "vcenterSpec": {"name": "vcenter-wld"},
            },
            "timeout": 10,
            "poll_interval": 1,
        }
        instance = build_mock_module(params)
        mock_cls.return_value = instance
        yield instance


class TestValidation:
    def test_validation_returns_id(self, mock_module):
        mock_module.params["state"] = "validated"

        token_resp = {"accessToken": "test-token"}
        validation_resp = {"id": "val-domain-001"}

        with patch("vcf_sddc_domain.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.side_effect = [
                json.dumps(token_resp).encode(),
                json.dumps(validation_resp).encode(),
            ]
            mock_urlopen.return_value = mock_resp

            with pytest.raises(AnsibleExitJson) as exc_info:
                run_module()

        assert exc_info.value.kwargs["validation_id"] == "val-domain-001"
        assert exc_info.value.kwargs["changed"] is False


class TestDomainCreation:
    def test_successful_domain_creation(self, mock_module):
        token_resp = {"accessToken": "test-token"}
        create_resp = {"id": "domain-task-001"}
        task_resp = {"id": "domain-task-001", "status": "SUCCESSFUL"}

        with patch("vcf_sddc_domain.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.side_effect = [
                json.dumps(token_resp).encode(),
                json.dumps(create_resp).encode(),
                json.dumps(task_resp).encode(),
            ]
            mock_urlopen.return_value = mock_resp

            with pytest.raises(AnsibleExitJson) as exc_info:
                run_module()

        assert exc_info.value.kwargs["changed"] is True
        assert exc_info.value.kwargs["status"] == "SUCCESSFUL"

    def test_failed_domain_creation(self, mock_module):
        token_resp = {"accessToken": "test-token"}
        create_resp = {"id": "domain-task-002"}
        task_resp = {"id": "domain-task-002", "status": "FAILED"}

        with patch("vcf_sddc_domain.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.side_effect = [
                json.dumps(token_resp).encode(),
                json.dumps(create_resp).encode(),
                json.dumps(task_resp).encode(),
            ]
            mock_urlopen.return_value = mock_resp

            with pytest.raises(AnsibleFailJson):
                run_module()


class TestSpecLoading:
    def test_spec_from_file(self, mock_module, tmp_path):
        spec_file = tmp_path / "domain.json"
        spec_file.write_text(json.dumps({"domainName": "wld-01"}))
        mock_module.params["domain_spec"] = str(spec_file)
        mock_module.params["state"] = "validated"

        token_resp = {"accessToken": "test-token"}
        validation_resp = {"id": "val-003"}

        with patch("vcf_sddc_domain.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.side_effect = [
                json.dumps(token_resp).encode(),
                json.dumps(validation_resp).encode(),
            ]
            mock_urlopen.return_value = mock_resp

            with pytest.raises(AnsibleExitJson):
                run_module()

    def test_invalid_spec_type_fails(self, mock_module):
        mock_module.params["domain_spec"] = "not-a-real-file"

        with pytest.raises(AnsibleFailJson) as exc_info:
            run_module()

        assert "must be a dict" in exc_info.value.kwargs["msg"]


class TestCheckMode:
    def test_check_mode_no_action(self, mock_module):
        mock_module.check_mode = True

        with pytest.raises(AnsibleExitJson) as exc_info:
            run_module()

        assert exc_info.value.kwargs["changed"] is False
