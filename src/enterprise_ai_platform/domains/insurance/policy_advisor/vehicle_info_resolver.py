"""
Vehicle information resolution for the Policy Advisor workflow.
"""

from __future__ import annotations

from typing import Any

from enterprise_ai_platform.domains.insurance.policy_advisor.vehicle_category import (
    classify_vehicle_category,
)


class VehicleInfoResolver:
    """
    Single, stable entry point for resolving vehicle details from
    whatever information is available about a customer's vehicle.

    THIS IS A SKELETON FOR A PLANNED FUTURE CAPABILITY. Today, this
    only classifies vehicle_category from free-text vehicle_segment
    (keyword matching). The planned evolution is a registration-
    number-based resolution path -- RC Book OCR, or a vehicle
    registry API (e.g. VAHAN) -- that would provide AUTHORITATIVE
    vehicle details (category, make, model, fuel type, manufacture
    year) directly from a registration number, no free-text
    classification needed at all for those customers.

    `resolve()` is the ONLY method anything else in this codebase
    should call (currently just the tool node handler). When
    registration-number resolution is implemented, it is added HERE,
    tried first (authoritative), falling back to free-text
    classification only when no registration number is given or the
    lookup fails/is unavailable -- nothing calling `resolve()` needs
    to change when that happens, since the return shape stays the
    same (a dict of resolved fields), just with more keys populated
    and more of them authoritative rather than inferred.

    vehicle_registration_number is captured in the extraction schema
    now (as "Sensitive Personal", per the platform's Vehicle domain
    canonical_schema, and already denylisted in ConversationLogger)
    specifically so it's already flowing through the pipeline,
    correctly redacted, ready for this resolver to actually use once
    OCR/API resolution exists -- capturing it now avoids a second,
    separate migration later just to start collecting it.
    """

    def resolve(
        self,
        vehicle_segment: str | None = None,
        vehicle_registration_number: str | None = None,
    ) -> dict[str, Any]:
        """
        Returns a dict of resolved vehicle fields. Currently always
        just {"vehicle_category": ...}; the shape is expected to grow
        (fuel_type, manufacture_year, make/model) once registration-
        based resolution exists.
        """

        # FUTURE EXTENSION POINT -- not yet implemented:
        #
        # if vehicle_registration_number is not None:
        #     resolved = self._resolve_from_registration(
        #         vehicle_registration_number
        #     )
        #     if resolved is not None:
        #         return resolved
        #
        # def _resolve_from_registration(self, registration_number):
        #     """
        #     Would call an RC Book OCR result already parsed
        #     upstream, or a live vehicle registry API, returning
        #     authoritative vehicle_category/fuel_type/manufacture_year/
        #     make/model. Returns None if the lookup fails or the
        #     registration number isn't recognized, so callers
        #     correctly fall through to free-text classification
        #     rather than failing hard.
        #     """
        #     raise NotImplementedError

        return {
            "vehicle_category": classify_vehicle_category(vehicle_segment),
        }