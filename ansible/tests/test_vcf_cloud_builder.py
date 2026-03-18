"""Unit tests for vcf_cloud_builder Ansible module."""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "library"))

from helpers import AnsibleExitJson, AnsibleFailJson, build_mock_module
from vcf_cloud_builder import run_module


@pytest.fixture
def mock_module(cloud_builder_args):
    """Patch AnsibleModule to capture exit/fail calls."""
    with patch("vcf_cloud_builder.AnsibleModule") as mock_cls:
        instance = build_mock_module(cloud_builder_args)
        mock_cls.return_value = instance
        yield instance


class TestValidation:
    def test_validation_returns_validation_id(self, mock_module):
        mock_module.params["state"] = "validated"
        validation_resp = {"id": "val-001", "executionStatus": "COMPLETED"}

        with patch("vcf_cloud_builder.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(validation_resp).encode()
            mock_urlopen.return_value = mock_resp

            with pytest.raises(AnsibleExitJson) as exc_info:
                run_module()

        assert exc_info.value.kwargs["validation_id"] == "val-001"
        assert exc_info.value.kwargs["changed"] is False


class TestDeployment:
    def test_successful_deployment(self, mock_module):
        deploy_resp = {"id": "sddc-001", "status": "IN_PROGRESS"}
        status_resp = {"id": "sddc-001", "status": "COMPLETED"}

        with patch("vcf_cloud_builder.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.side_effect = [
                json.dumps(deploy_resp).encode(),
                json.dumps(status_resp).encode(),
            ]
            mock_urlopen.return_value = mock_resp

            with pytest.raises(AnsibleExitJson) as exc_info:
                run_module()

        assert exc_info.value.kwargs["changed"] is True
        assert exc_info.value.kwargs["deployment_id"] == "sddc-001"

    def test_failed_deployment(self, mock_module):
        deploy_resp = {"id": "sddc-002", "status": "IN_PROGRESS"}
        status_resp = {"id": "sddc-002", "status": "FAILED"}

        with patch("vcf_cloud_builder.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.side_effect = [
                json.dumps(deploy_resp).encode(),
                json.dumps(status_resp).encode(),
            ]
            mock_urlopen.return_value = mock_resp

            with pytest.raises(AnsibleFailJson) as exc_info:
                run_module()

        assert "FAILED" in exc_info.value.kwargs["msg"]


class TestCheckMode:
    def test_check_mode_no_action(self, mock_module):
        mock_module.check_mode = True

        with pytest.raises(AnsibleExitJson) as exc_info:
            run_module()

        assert exc_info.value.kwargs["changed"] is False


class TestSpecLoading:
    def test_spec_from_file(self, mock_module, tmp_path):
        spec_file = tmp_path / "bringup.json"
        spec_file.write_text(json.dumps({"dnsSpec": {"domain": "test.local"}}))
        mock_module.params["spec"] = str(spec_file)
        mock_module.params["state"] = "validated"

        validation_resp = {"id": "val-002"}
        with patch("vcf_cloud_builder.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(validation_resp).encode()
            mock_urlopen.return_value = mock_resp

            with pytest.raises(AnsibleExitJson):
                run_module()

    def test_invalid_spec_type_fails(self, mock_module):
        mock_module.params["spec"] = "not-a-file-and-not-a-dict"

        with pytest.raises(AnsibleFailJson) as exc_info:
            run_module()

        assert "must be a dict" in exc_info.value.kwargs["msg"]
