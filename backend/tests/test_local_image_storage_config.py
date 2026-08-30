"""Tests for the local image storage fallback configuration properties (WIQ-V1-054).

Verifies that the production boundary is enforced:
- deployment_mode=production: Cloudinary is mandatory, local storage is NEVER active.
- deployment_mode=local-simulation: Local storage is allowed (with explicit opt-in).
- deployment_mode=development: No image storage requirements.
"""

from app.core.config import get_settings

# ─── deployment_mode = production ─────────────────────────────────────────────


def test_production_cloudinary_required():
    """Production always requires Cloudinary."""
    settings = get_settings().model_copy(
        update={
            "deployment_mode": "production",
            "cloudinary_cloud_name": None,
            "cloudinary_api_key": None,
            "cloudinary_api_secret": None,
        }
    )
    assert settings.cloudinary_required is True


def test_production_cloudinary_required_even_with_fallback_flag():
    """CRITICAL: production + LOCAL_IMAGE_STORAGE_ENABLED=true does NOT disable the requirement.

    This is the core security boundary: deployment_mode=production is the gate that
    prevents local storage from ever being used, regardless of other settings.
    """
    settings = get_settings().model_copy(
        update={
            "deployment_mode": "production",
            "cloudinary_cloud_name": None,
            "cloudinary_api_key": None,
            "cloudinary_api_secret": None,
            "local_image_storage_enabled": True,
        }
    )
    assert settings.cloudinary_required is True
    assert settings.local_image_storage_active is False


def test_production_cloudinary_required_even_with_environment_production():
    """deployment_mode overrides environment=production for the image storage boundary."""
    settings = get_settings().model_copy(
        update={
            "environment": "production",
            "deployment_mode": "production",
            "cloudinary_cloud_name": None,
            "cloudinary_api_key": None,
            "cloudinary_api_secret": None,
            "local_image_storage_enabled": True,
        }
    )
    assert settings.cloudinary_required is True
    assert settings.local_image_storage_active is False


def test_production_ready_when_cloudinary_configured():
    """Production + Cloudinary configured = ready."""
    settings = get_settings().model_copy(
        update={
            "deployment_mode": "production",
            "cloudinary_cloud_name": "cloud",
            "cloudinary_api_key": "key",
            "cloudinary_api_secret": "secret",
        }
    )
    assert settings.cloudinary_required is True
    assert settings.cloudinary_configured is True
    assert settings.local_image_storage_active is False


# ─── deployment_mode = local-simulation ────────────────────────────────────────


def test_local_simulation_cloudinary_not_required():
    """Local simulation does not require Cloudinary by default."""
    settings = get_settings().model_copy(
        update={
            "deployment_mode": "local-simulation",
            "cloudinary_cloud_name": None,
            "cloudinary_api_key": None,
            "cloudinary_api_secret": None,
        }
    )
    assert settings.cloudinary_required is False


def test_local_simulation_local_storage_active_when_fallback_enabled():
    """Local simulation + LOCAL_IMAGE_STORAGE_ENABLED=true + no Cloudinary = active."""
    settings = get_settings().model_copy(
        update={
            "deployment_mode": "local-simulation",
            "cloudinary_cloud_name": None,
            "cloudinary_api_key": None,
            "cloudinary_api_secret": None,
            "local_image_storage_enabled": True,
        }
    )
    assert settings.local_image_storage_active is True
    assert settings.cloudinary_required is False


def test_local_simulation_cloudinary_wins_over_fallback():
    """Local simulation with Cloudinary configured: Cloudinary takes precedence."""
    settings = get_settings().model_copy(
        update={
            "deployment_mode": "local-simulation",
            "cloudinary_cloud_name": "cloud",
            "cloudinary_api_key": "key",
            "cloudinary_api_secret": "secret",
            "local_image_storage_enabled": True,
        }
    )
    assert settings.cloudinary_configured is True
    assert settings.local_image_storage_active is False


def test_local_simulation_fallback_false_inactive():
    """Local simulation without explicit opt-in: fallback is inactive."""
    settings = get_settings().model_copy(
        update={
            "deployment_mode": "local-simulation",
            "cloudinary_cloud_name": None,
            "cloudinary_api_key": None,
            "cloudinary_api_secret": None,
            "local_image_storage_enabled": False,
        }
    )
    assert settings.local_image_storage_active is False


# ─── deployment_mode = development ────────────────────────────────────────────


def test_development_cloudinary_not_required():
    """Development never requires Cloudinary."""
    settings = get_settings().model_copy(
        update={
            "deployment_mode": "development",
            "cloudinary_cloud_name": None,
            "cloudinary_api_key": None,
            "cloudinary_api_secret": None,
        }
    )
    assert settings.cloudinary_required is False
    assert settings.local_image_storage_active is False


def test_development_fallback_flag_ignored():
    """In development, LOCAL_IMAGE_STORAGE_ENABLED is ignored (not a simulation)."""
    settings = get_settings().model_copy(
        update={
            "deployment_mode": "development",
            "cloudinary_cloud_name": None,
            "cloudinary_api_key": None,
            "cloudinary_api_secret": None,
            "local_image_storage_enabled": True,
        }
    )
    assert settings.local_image_storage_active is False


# ─── Cloudinary configuration requirements ─────────────────────────────────────


def test_cloudinary_configured_requires_all_three_fields():
    """Partial Cloudinary config is not sufficient."""
    settings = get_settings().model_copy(
        update={
            "deployment_mode": "production",
            "cloudinary_cloud_name": "cloud",
            "cloudinary_api_key": None,
            "cloudinary_api_secret": None,
        }
    )
    assert settings.cloudinary_configured is False


def test_cloudinary_configured_with_all_three():
    """All three Cloudinary fields must be present."""
    settings = get_settings().model_copy(
        update={
            "deployment_mode": "production",
            "cloudinary_cloud_name": "cloud",
            "cloudinary_api_key": "key",
            "cloudinary_api_secret": "secret",
        }
    )
    assert settings.cloudinary_configured is True


# ─── Backward compatibility: environment still works ───────────────────────────


def test_environment_production_still_sets_is_production():
    """The is_production property still works from ENVIRONMENT variable."""
    settings = get_settings().model_copy(
        update={
            "environment": "production",
            "deployment_mode": "local-simulation",
        }
    )
    assert settings.is_production is True
    assert settings.deployment_mode == "local-simulation"
