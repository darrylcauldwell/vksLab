"""Unit tests for vcf_sddc_task Ansible module."""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "library"))

from helpers import AnsibleExitJson, AnsibleFailJson, build_mock_module
from vcf_sddc_task import run_module


@pytest.fixture
def mock_module(module_args_base):
    """Patch AnsibleModule to capture exit/fail calls."""
    with patch("vcf_sddc_task.AnsibleModule") as mock_cls:
        params = {
            **module_args_base,
            "task_id": "task-123",
            "timeout": 10,
            "poll_interval": 1,
        }
        instance = build_mock_module(params)
        mock_cls.return_value = instance
        yield instance


class TestTaskPolling:
    def test_successful_task(self, mock_module, sample_task_response_success):
        token_resp = {"accessToken": "test-token"}

        with patch("vcf_sddc_task.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.side_effect = [
                json.dumps(token_resp).encode(),
                json.dumps(sample_task_response_success).encode(),
            ]
            mock_urlopen.return_value = mock_resp

            with pytest.raises(AnsibleExitJson) as exc_info:
                run_module()

        assert exc_info.value.kwargs["status"] == "SUCCESSFUL"
        assert exc_info.value.kwargs["changed"] is True

    def test_failed_task(self, mock_module, sample_task_response_failed):
        token_resp = {"accessToken": "test-token"}

        with patch("vcf_sddc_task.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.side_effect = [
                json.dumps(token_resp).encode(),
                json.dumps(sample_task_response_failed).encode(),
            ]
            mock_urlopen.return_value = mock_resp

            with pytest.raises(AnsibleFailJson) as exc_info:
                run_module()

        assert "FAILED" in exc_info.value.kwargs["msg"]

    def test_task_polls_until_complete(
        self, mock_module, sample_task_response_in_progress, sample_task_response_success
    ):
        token_resp = {"accessToken": "test-token"}

        with patch("vcf_sddc_task.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.side_effect = [
                json.dumps(token_resp).encode(),
                json.dumps(sample_task_response_in_progress).encode(),
                json.dumps(sample_task_response_success).encode(),
            ]
            mock_urlopen.return_value = mock_resp

            with patch("vcf_sddc_task.time.sleep"):
                with pytest.raises(AnsibleExitJson) as exc_info:
                    run_module()

        assert exc_info.value.kwargs["status"] == "SUCCESSFUL"


class TestCheckMode:
    def test_check_mode_no_action(self, mock_module):
        mock_module.check_mode = True

        with pytest.raises(AnsibleExitJson) as exc_info:
            run_module()

        assert exc_info.value.kwargs["changed"] is False
