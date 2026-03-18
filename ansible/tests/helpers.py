"""Test helpers for custom Ansible module tests."""

import sys
from types import ModuleType
from unittest.mock import MagicMock

# Mock ansible.module_utils.basic so tests run without ansible-core installed
if "ansible" not in sys.modules:
    ansible_mod = ModuleType("ansible")
    ansible_mu = ModuleType("ansible.module_utils")
    ansible_mub = ModuleType("ansible.module_utils.basic")
    ansible_mub.AnsibleModule = MagicMock
    ansible_mod.module_utils = ansible_mu
    ansible_mu.basic = ansible_mub
    sys.modules["ansible"] = ansible_mod
    sys.modules["ansible.module_utils"] = ansible_mu
    sys.modules["ansible.module_utils.basic"] = ansible_mub


class AnsibleExitJson(Exception):
    """Raised by mocked exit_json to halt module execution."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        super().__init__()


class AnsibleFailJson(Exception):
    """Raised by mocked fail_json to halt module execution."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        super().__init__()


def _raise_exit(**kwargs):
    raise AnsibleExitJson(**kwargs)


def _raise_fail(**kwargs):
    raise AnsibleFailJson(**kwargs)


def build_mock_module(params, check_mode=False):
    """Create a mock AnsibleModule that raises on exit/fail."""
    instance = MagicMock()
    instance.params = params
    instance.check_mode = check_mode
    instance.exit_json.side_effect = _raise_exit
    instance.fail_json.side_effect = _raise_fail
    return instance
