"""Shared fixtures for custom Ansible module tests."""

import json
import os
import sys

import pytest

# Ensure helpers module is importable and Ansible mocks are set up
sys.path.insert(0, os.path.dirname(__file__))
import helpers  # noqa: F401, E402 — triggers ansible mock setup


@pytest.fixture
def module_args_base():
    """Base module args used across VCF module tests."""
    return {
        "sddc_hostname": "sddc-manager.lab.dreamfold.dev",
        "username": "admin@local",
        "password": "test-password",
        "validate_certs": False,
    }


@pytest.fixture
def cloud_builder_args():
    """Module args for vcf_cloud_builder."""
    return {
        "hostname": "vcf-installer.lab.dreamfold.dev",
        "username": "admin",
        "password": "test-password",
        "validate_certs": False,
        "state": "deployed",
        "spec": {"dnsSpec": {"domain": "lab.dreamfold.dev"}},
        "timeout": 60,
        "poll_interval": 1,
    }


@pytest.fixture
def sample_task_response_success():
    return {"id": "task-123", "status": "SUCCESSFUL", "errors": []}


@pytest.fixture
def sample_task_response_in_progress():
    return {"id": "task-123", "status": "IN_PROGRESS", "errors": []}


@pytest.fixture
def sample_task_response_failed():
    return {
        "id": "task-123",
        "status": "FAILED",
        "errors": [{"message": "Host validation failed"}],
    }
