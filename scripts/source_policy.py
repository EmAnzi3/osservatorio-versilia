#!/usr/bin/env python3
"""Risoluzione e validazione delle politiche di aggiornamento delle fonti."""

from __future__ import annotations

from typing import Any


REQUIRED_POLICY_FIELDS = (
    "publisher",
    "frequency",
    "frequencyLabel",
    "expectedRelease",
    "acquisitionMethod",
    "licenseName",
)


def resolve_metric_policy(
    metric_key: str,
    metric: dict[str, Any],
    registry: dict[str, Any],
) -> dict[str, Any]:
    """Restituisce la politica effettiva, unendo default, profilo e override."""
    defaults = registry.get("defaults")
    profiles = registry.get("sourceProfiles")
    url_profiles = registry.get("sourceProfileByUrl")
    metric_overrides = registry.get("metricOverrides")

    defaults = defaults if isinstance(defaults, dict) else {}
    profiles = profiles if isinstance(profiles, dict) else {}
    url_profiles = url_profiles if isinstance(url_profiles, dict) else {}
    metric_overrides = metric_overrides if isinstance(metric_overrides, dict) else {}

    override = metric_overrides.get(metric_key)
    override = override if isinstance(override, dict) else {}
    source_url = str(metric.get("sourceUrl") or "")
    profile_id = str(override.get("profile") or url_profiles.get(source_url) or "")
    profile = profiles.get(profile_id)
    profile = profile if isinstance(profile, dict) else {}

    policy = {**defaults, **profile, **override}
    policy.pop("profile", None)
    policy["profileId"] = profile_id
    policy["sourceUrl"] = source_url
    policy["resolved"] = bool(profile_id and profile)
    return policy


def validate_registry(
    data: dict[str, Any],
    registry: dict[str, Any],
) -> list[dict[str, str]]:
    """Valida che ogni indicatore abbia una politica esplicita e completa."""
    errors: list[dict[str, str]] = []
    profiles = registry.get("sourceProfiles")
    url_profiles = registry.get("sourceProfileByUrl")

    if registry.get("schemaVersion") != 2:
        errors.append(
            {
                "metric": "",
                "code": "registry_schema",
                "message": "Il registro fonti deve usare schemaVersion 2.",
            }
        )
    if not isinstance(profiles, dict) or not profiles:
        errors.append(
            {
                "metric": "",
                "code": "source_profiles_missing",
                "message": "Profili delle fonti assenti dal registro.",
            }
        )
        profiles = {}
    if not isinstance(url_profiles, dict) or not url_profiles:
        errors.append(
            {
                "metric": "",
                "code": "source_mapping_missing",
                "message": "Mappatura URL-profilo assente dal registro.",
            }
        )

    for profile_id, profile in profiles.items():
        if not isinstance(profile, dict):
            errors.append(
                {
                    "metric": "",
                    "code": "source_profile_shape",
                    "message": f"Profilo fonte non valido: {profile_id}.",
                }
            )
            continue
        missing = [field for field in REQUIRED_POLICY_FIELDS if not profile.get(field)]
        if missing:
            errors.append(
                {
                    "metric": "",
                    "code": "source_profile_fields",
                    "message": f"Profilo {profile_id} incompleto: {', '.join(missing)}.",
                }
            )

    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        return errors
    for metric_key, metric in metrics.items():
        if not isinstance(metric, dict):
            continue
        policy = resolve_metric_policy(metric_key, metric, registry)
        if not policy["resolved"]:
            errors.append(
                {
                    "metric": metric_key,
                    "code": "source_policy_unresolved",
                    "message": "Nessun profilo fonte associato all'indicatore.",
                }
            )
            continue
        missing = [field for field in REQUIRED_POLICY_FIELDS if not policy.get(field)]
        if missing:
            errors.append(
                {
                    "metric": metric_key,
                    "code": "source_policy_fields",
                    "message": f"Politica fonte incompleta: {', '.join(missing)}.",
                }
            )
    return errors
