from __future__ import annotations
from typing import Any

def relation_signatures(protocol: dict[str, Any]) -> dict[str, tuple[str, str, str]]:
    return {
        relation["relation_id"]: (
            relation["source_role"],
            relation["relation_type"],
            relation["target_role"],
        )
        for relation in protocol["fixed_relations"]
    }

def exact_keys(value: dict[str, Any], expected: set[str], context: str) -> list[str]:
    actual = set(value)
    errors: list[str] = []
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        errors.append(f"{context}: missing keys {missing}")
    if extra:
        errors.append(f"{context}: extra keys {extra}")
    return errors

def validate_payload(payload: dict[str, Any], protocol: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["payload is not a JSON object"]
    errors.extend(
        exact_keys(
            payload,
            {"image_id", "graph_status", "quality_flags", "roles", "evidence", "relations"},
            "payload",
        )
    )
    if errors:
        return errors

    allowed = protocol["allowed_values"]
    if payload["graph_status"] not in allowed["graph_status"]:
        errors.append(f"graph_status: invalid value {payload['graph_status']!r}")

    quality = payload["quality_flags"]
    if not isinstance(quality, dict):
        errors.append("quality_flags is not an object")
    else:
        quality_keys = {
            "boundary_truncation",
            "shadow_interference",
            "orthophoto_distortion",
        }
        errors.extend(exact_keys(quality, quality_keys, "quality_flags"))
        for key in quality_keys & set(quality):
            if quality[key] not in allowed["quality_flag"]:
                errors.append(f"quality_flags.{key}: invalid value {quality[key]!r}")

    roles = payload["roles"]
    expected_roles = set(protocol["fixed_roles"])
    if not isinstance(roles, dict):
        errors.append("roles is not an object")
        roles = {}
    else:
        errors.extend(exact_keys(roles, expected_roles, "roles"))
    for role in expected_roles & set(roles):
        attributes = roles[role]
        if not isinstance(attributes, dict):
            errors.append(f"roles.{role} is not an object")
            continue
        errors.extend(
            exact_keys(attributes, {"presence", "organization", "visibility"}, f"roles.{role}")
        )
        if attributes.get("presence") not in allowed["presence"]:
            errors.append(f"roles.{role}.presence: invalid value")
        if attributes.get("organization") not in allowed["organization"]:
            errors.append(f"roles.{role}.organization: invalid value")
        if attributes.get("visibility") not in allowed["visibility_or_observability"]:
            errors.append(f"roles.{role}.visibility: invalid value")
        if attributes.get("presence") == "absent" and attributes.get("organization") != "not_applicable":
            errors.append(f"roles.{role}: absent requires organization=not_applicable")

    evidence = payload["evidence"]
    expected_evidence = set(protocol["fixed_evidence"])
    if not isinstance(evidence, dict):
        errors.append("evidence is not an object")
        evidence = {}
    else:
        errors.extend(exact_keys(evidence, expected_evidence, "evidence"))
    for code in expected_evidence & set(evidence):
        attributes = evidence[code]
        if not isinstance(attributes, dict):
            errors.append(f"evidence.{code} is not an object")
            continue
        errors.extend(exact_keys(attributes, {"state", "observability"}, f"evidence.{code}"))
        if attributes.get("state") not in allowed["evidence_state"]:
            errors.append(f"evidence.{code}.state: invalid value")
        if attributes.get("observability") not in allowed["visibility_or_observability"]:
            errors.append(f"evidence.{code}.observability: invalid value")
        if (attributes.get("state") == "not_applicable") != (
            attributes.get("observability") == "not_applicable"
        ):
            errors.append(f"evidence.{code}: not_applicable state/observability mismatch")

    diagnostic_requirements = {
        "elevated_porous": ("porous_crown_texture", "branching_structure"),
        "ground_vegetation": ("continuous_fine_vegetation_texture",),
        "elevated_closed_rigid": ("closed_rigid_contour", "roof_surface_consistency"),
        "open_hard_surface": ("open_hard_surface_continuity",),
        "small_rigid_group": ("repeated_small_rigid_shapes",),
    }
    for role, codes in diagnostic_requirements.items():
        if roles.get(role, {}).get("presence") == "present":
            if not any(evidence.get(code, {}).get("state") == "present" for code in codes):
                errors.append(f"roles.{role}: present without required diagnostic evidence")

    relations = payload["relations"]
    signatures = relation_signatures(protocol)
    if not isinstance(relations, list):
        errors.append("relations is not an array")
        relations = []
    if len(relations) != 4:
        errors.append(f"relations: expected 4, got {len(relations)}")
    seen_relation_ids: set[str] = set()
    for index, relation in enumerate(relations):
        context = f"relations[{index}]"
        if not isinstance(relation, dict):
            errors.append(f"{context} is not an object")
            continue
        errors.extend(
            exact_keys(
                relation,
                {
                    "relation_id",
                    "source_role",
                    "relation_type",
                    "target_role",
                    "state",
                    "observability",
                },
                context,
            )
        )
        relation_id = relation.get("relation_id")
        if relation_id not in signatures:
            errors.append(f"{context}.relation_id: invalid value {relation_id!r}")
            continue
        if relation_id in seen_relation_ids:
            errors.append(f"{context}: duplicate relation_id {relation_id}")
        seen_relation_ids.add(relation_id)
        actual_signature = (
            relation.get("source_role"),
            relation.get("relation_type"),
            relation.get("target_role"),
        )
        if actual_signature != signatures[relation_id]:
            errors.append(f"{context}: signature differs from frozen {relation_id}")
        state = relation.get("state")
        observability = relation.get("observability")
        if state not in allowed["relation_state"]:
            errors.append(f"{context}.state: invalid value {state!r}")
        if observability not in allowed["visibility_or_observability"]:
            errors.append(f"{context}.observability: invalid value {observability!r}")
        if (state == "not_applicable") != (observability == "not_applicable"):
            errors.append(f"{context}: not_applicable state/observability mismatch")

        source_presence = roles.get(actual_signature[0], {}).get("presence")
        target_presence = roles.get(actual_signature[2], {}).get("presence")
        endpoint_states = {source_presence, target_presence}
        if "absent" in endpoint_states and state != "not_applicable":
            errors.append(f"{context}: absent endpoint requires not_applicable")
        elif "absent" not in endpoint_states and "unknown" in endpoint_states and state != "unknown":
            errors.append(f"{context}: unknown endpoint requires unknown")
        elif endpoint_states == {"present"} and state == "not_applicable":
            errors.append(f"{context}: present endpoints cannot be not_applicable")
        elif state in {"observed", "not_observed"} and endpoint_states != {"present"}:
            errors.append(f"{context}: {state} requires both endpoints present")
    if seen_relation_ids != set(signatures):
        errors.append("relations: R1-R4 must each occur exactly once")
    return errors

def parse_compact_groups(
    text: str,
    expected_count: int,
    field_count: int,
    label: str,
) -> list[list[str]]:
    groups = [group.strip() for group in text.split(";") if group.strip()]
    if len(groups) != expected_count:
        raise ValueError(f"{label}: expected {expected_count} groups, got {len(groups)}")
    parsed = [[field.strip() for field in group.split(",")] for group in groups]
    for index, fields in enumerate(parsed):
        if len(fields) != field_count:
            raise ValueError(
                f"{label}[{index}]: expected {field_count} fields, got {len(fields)}"
            )
    return parsed

def compact_to_payload(args, protocol):
    graph_map = {"u": "usable", "p": "partial", "n": "no_reliable_evidence"}
    quality_map = {"n": "none", "m": "mild", "s": "strong"}
    presence_map = {"p": "present", "a": "absent", "u": "unknown"}
    organization_map = {
        "iso": "isolated",
        "sca": "scattered",
        "clu": "clustered",
        "con": "continuous",
        "fra": "fragmented",
        "rep": "repeated",
        "u": "unknown",
        "na": "not_applicable",
    }
    visibility_map = {"c": "clear", "p": "partial", "x": "poor", "na": "not_applicable"}
    evidence_map = {"p": "present", "a": "absent", "u": "unknown", "na": "not_applicable"}
    relation_map = {"o": "observed", "n": "not_observed", "u": "unknown", "na": "not_applicable"}

    quality_codes = [item.strip() for item in args.quality.split(",")]
    if len(quality_codes) != 3:
        raise ValueError("quality requires exactly three comma-separated codes")
    role_groups = parse_compact_groups(args.roles, 5, 3, "roles")
    evidence_groups = parse_compact_groups(args.evidence, 8, 2, "evidence")
    relation_groups = parse_compact_groups(args.relations, 4, 2, "relations")

    try:
        roles = {
            role: {
                "presence": presence_map[group[0]],
                "organization": organization_map[group[1]],
                "visibility": visibility_map[group[2]],
            }
            for role, group in zip(protocol["fixed_roles"], role_groups)
        }
        evidence = {
            code: {
                "state": evidence_map[group[0]],
                "observability": visibility_map[group[1]],
            }
            for code, group in zip(protocol["fixed_evidence"], evidence_groups)
        }
        signatures = relation_signatures(protocol)
        relations = []
        for relation_id, group in zip(("R1", "R2", "R3", "R4"), relation_groups):
            source, relation_type, target = signatures[relation_id]
            relations.append(
                {
                    "relation_id": relation_id,
                    "source_role": source,
                    "relation_type": relation_type,
                    "target_role": target,
                    "state": relation_map[group[0]],
                    "observability": visibility_map[group[1]],
                }
            )
        payload = {
            "image_id": args.image_id,
            "graph_status": graph_map[args.graph],
            "quality_flags": {
                "boundary_truncation": quality_map[quality_codes[0]],
                "shadow_interference": quality_map[quality_codes[1]],
                "orthophoto_distortion": quality_map[quality_codes[2]],
            },
            "roles": roles,
            "evidence": evidence,
            "relations": relations,
        }
    except KeyError as error:
        raise ValueError(f"unknown compact code: {error.args[0]}") from error

    return payload
