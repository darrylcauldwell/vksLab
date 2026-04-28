"""Runtime version checking for VCF SDK.

Provides a decorator and utilities to check API version compatibility
at runtime, issuing warnings for deprecated features and raising errors
for unsupported endpoints.
"""

import functools
import logging
import warnings
from typing import Optional

from vcf_sdk.versions import (
    check_version,
)

logger = logging.getLogger(__name__)


class UnsupportedVersionError(Exception):
    """Raised when an API endpoint is not available on the connected version."""

    def __init__(self, feature: str, required: str, current: str):
        self.feature = feature
        self.required = required
        self.current = current
        super().__init__(
            f"'{feature}' requires version {required}+, "
            f"but connected to version {current}"
        )


class DeprecatedFeatureWarning(UserWarning):
    """Warning for deprecated API features."""

    pass


def requires_version(
    required_version: str,
    feature_name: str = None,
    product: str = "VCF",
):
    """
    Decorator that checks the connected API version before calling a method.

    The decorated method's `self` must have a `_api_version` attribute
    (set during client initialization).

    Args:
        required_version: Minimum version string (e.g., "5.2.0")
        feature_name: Human-readable feature name for error messages
        product: "VCF" or "NSX" for error messages
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            current = getattr(self, "_api_version", None)
            if current and not check_version(current, required_version):
                name = feature_name or func.__qualname__
                raise UnsupportedVersionError(name, required_version, current)
            return func(self, *args, **kwargs)

        # Annotate the docstring
        version_note = f"\n\n    .. versionadded:: {product} {required_version}"
        if wrapper.__doc__:
            wrapper.__doc__ += version_note
        else:
            wrapper.__doc__ = f"Requires {product} {required_version}+.{version_note}"

        return wrapper

    return decorator


def check_manager_version(
    manager_name: str,
    current_version: Optional[str],
    version_map: dict,
    deprecated_map: dict = None,
    product: str = "VCF",
) -> None:
    """
    Check if a manager is supported on the current version.
    Issues warnings for deprecated features, raises for unsupported.

    Called during SDDCManager/NSXManager __init__ when wiring managers.
    """
    if not current_version:
        return  # No version info — skip checks

    required = version_map.get(manager_name)
    if required is not None and not check_version(current_version, required):
        logger.warning(
            f"Manager '{manager_name}' requires {product} {required}+, "
            f"but connected to {current_version}. "
            f"API calls may fail with HTTP errors."
        )

    if deprecated_map and manager_name in deprecated_map:
        info = deprecated_map[manager_name]
        if check_version(current_version, info["deprecated_in"]):
            warnings.warn(
                f"{info['message']} (deprecated in {product} {info['deprecated_in']})",
                DeprecatedFeatureWarning,
                stacklevel=3,
            )
