"""Set location targeting on Google Ads campaigns.

Supports both radius targeting (around a point) and named location
targeting (city, state, DMA). Location intent defaults to
PRESENCE — "people in or regularly in your targeted locations."

Account ID is read from config. Requires API credentials.
"""

from .client import get_client, get_account_id, load_account_config, AdsClientError


def _customer_id() -> str:
    return get_account_id(hyphenated=False)


def get_geo_target_constant(client, location_name: str) -> str:
    """Search for a geo target constant by name and return its resource name.

    Uses the GeoTargetConstantService to find locations matching the query.
    Returns the best match resource name, or raises if not found.
    """
    gtc_service = client.get_service("GeoTargetConstantService")
    request = client.get_type("SuggestGeoTargetConstantsRequest")
    request.locale = "en"
    request.country_code = "US"
    request.location_names.names.append(location_name)

    response = gtc_service.suggest_geo_target_constants(request=request)
    if not response.geo_target_constant_suggestions:
        raise AdsClientError(
            f"No geo target found for '{location_name}'. "
            f"Try a more specific name (e.g., 'Bristol, Tennessee')."
        )
    best = response.geo_target_constant_suggestions[0]
    return best.geo_target_constant.resource_name


def set_location_targets(campaign_id: int, locations: list[str]) -> list[dict]:
    """Add named location targets to a campaign.

    Args:
        campaign_id: The campaign to target.
        locations: List of location names (e.g., ["Bristol, Tennessee"]).

    Returns:
        List of dicts with action details for each location added.
    """
    client = get_client()
    customer_id = _customer_id()
    campaign_service = client.get_service("CampaignService")
    campaign_resource = campaign_service.campaign_path(customer_id, campaign_id)

    operations = []
    resolved = []
    for loc_name in locations:
        geo_resource = get_geo_target_constant(client, loc_name)
        operation = client.get_type("CampaignCriterionOperation")
        criterion = operation.create
        criterion.campaign = campaign_resource
        criterion.location.geo_target_constant = geo_resource
        criterion.negative = False
        operations.append(operation)
        resolved.append({"location": loc_name, "resource": geo_resource})

    service = client.get_service("CampaignCriterionService")
    response = service.mutate_campaign_criteria(
        customer_id=customer_id, operations=operations
    )

    results = []
    for i, result in enumerate(response.results):
        results.append({
            "action": "add_location_target",
            "campaign_id": campaign_id,
            "location": resolved[i]["location"],
            "resource": result.resource_name,
        })
    return results


def set_radius_target(
    campaign_id: int,
    center_lat: float,
    center_lng: float,
    radius_miles: float,
    location_label: str = "",
) -> dict:
    """Add a radius-based location target to a campaign.

    Args:
        campaign_id: The campaign to target.
        center_lat: Latitude of the center point.
        center_lng: Longitude of the center point.
        radius_miles: Radius in miles.
        location_label: Human-readable label for logging.

    Returns:
        Dict with action details.
    """
    client = get_client()
    customer_id = _customer_id()
    campaign_service = client.get_service("CampaignService")
    campaign_resource = campaign_service.campaign_path(customer_id, campaign_id)

    operation = client.get_type("CampaignCriterionOperation")
    criterion = operation.create
    criterion.campaign = campaign_resource
    criterion.negative = False

    proximity = criterion.proximity
    proximity.address.CopyFrom(client.get_type("AddressInfo"))
    proximity.geo_point.latitude_in_micro_degrees = int(center_lat * 1_000_000)
    proximity.geo_point.longitude_in_micro_degrees = int(center_lng * 1_000_000)
    proximity.radius = radius_miles
    proximity.radius_units = client.enums.ProximityRadiusUnitsEnum.MILES

    service = client.get_service("CampaignCriterionService")
    response = service.mutate_campaign_criteria(
        customer_id=customer_id, operations=[operation]
    )

    return {
        "action": "add_radius_target",
        "campaign_id": campaign_id,
        "center": f"{center_lat}, {center_lng}",
        "radius_miles": radius_miles,
        "label": location_label or f"{center_lat}, {center_lng}",
        "resource": response.results[0].resource_name,
    }


def set_location_intent(campaign_id: int, intent: str = "PRESENCE") -> dict:
    """Set the location targeting intent for a campaign.

    Args:
        campaign_id: The campaign to update.
        intent: One of "PRESENCE" (people in the location — recommended)
                or "PRESENCE_OR_INTEREST" (people in or interested in).

    Returns:
        Dict with action details.
    """
    valid = {"PRESENCE", "PRESENCE_OR_INTEREST"}
    if intent.upper() not in valid:
        raise ValueError(f"Intent must be one of {valid}, got '{intent}'")

    client = get_client()
    customer_id = _customer_id()
    campaign_service = client.get_service("CampaignService")

    operation = client.get_type("CampaignOperation")
    campaign = operation.update
    campaign.resource_name = campaign_service.campaign_path(customer_id, campaign_id)
    campaign.geo_target_type_setting.positive_geo_target_type = (
        client.enums.PositiveGeoTargetTypeEnum[intent.upper()].value
    )

    field_mask = client.get_type("FieldMask")
    field_mask.paths.append("geo_target_type_setting.positive_geo_target_type")
    operation.update_mask.CopyFrom(field_mask)

    response = campaign_service.mutate_campaigns(
        customer_id=customer_id, operations=[operation]
    )

    return {
        "action": "set_location_intent",
        "campaign_id": campaign_id,
        "intent": intent.upper(),
        "resource": response.results[0].resource_name,
    }


def get_campaign_locations(campaign_id: int) -> list[dict]:
    """Retrieve current location targets for a campaign."""
    client = get_client()
    customer_id = _customer_id()
    ga_service = client.get_service("GoogleAdsService")

    query = (
        "SELECT campaign_criterion.location.geo_target_constant, "
        "campaign_criterion.proximity.geo_point.latitude_in_micro_degrees, "
        "campaign_criterion.proximity.geo_point.longitude_in_micro_degrees, "
        "campaign_criterion.proximity.radius, "
        "campaign_criterion.negative "
        "FROM campaign_criterion "
        f"WHERE campaign.id = {campaign_id} "
        "AND campaign_criterion.type IN ('LOCATION', 'PROXIMITY') "
        "AND campaign_criterion.negative = FALSE"
    )

    response = ga_service.search(customer_id=customer_id, query=query)
    results = []
    for row in response:
        cc = row.campaign_criterion
        if cc.location.geo_target_constant:
            results.append({
                "type": "location",
                "geo_target_constant": cc.location.geo_target_constant,
            })
        elif cc.proximity.geo_point.latitude_in_micro_degrees:
            results.append({
                "type": "radius",
                "lat": cc.proximity.geo_point.latitude_in_micro_degrees / 1_000_000,
                "lng": cc.proximity.geo_point.longitude_in_micro_degrees / 1_000_000,
                "radius": cc.proximity.radius,
            })
    return results


def apply_geotargeting_from_config(campaign_id: int) -> list[dict]:
    """Apply geotargeting settings from account.yaml to a campaign.

    Reads the geotargeting config and applies either radius or named
    location targeting, plus sets location intent.

    Returns a list of all actions taken.
    """
    config = load_account_config()
    geo = config.get("geotargeting")
    if not geo:
        raise AdsClientError(
            "No geotargeting config found in account.yaml. "
            "Run the getting-started skill to configure location targeting."
        )

    results = []

    # Set location intent first
    intent = geo.get("intent", "PRESENCE")
    results.append(set_location_intent(campaign_id, intent))

    # Apply radius targeting if configured
    if geo.get("radius"):
        r = geo["radius"]
        result = set_radius_target(
            campaign_id=campaign_id,
            center_lat=r["lat"],
            center_lng=r["lng"],
            radius_miles=r["miles"],
            location_label=r.get("label", ""),
        )
        results.append(result)

    # Apply named locations if configured
    if geo.get("locations"):
        loc_results = set_location_targets(campaign_id, geo["locations"])
        results.extend(loc_results)

    return results
