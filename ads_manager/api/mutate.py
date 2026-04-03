"""Push changes to Google Ads via the API.

Supports updating campaign budgets, keyword bids/status, and creating
new responsive search ads. Account ID and ad copy rules are read from config.
"""

from .client import get_client, get_account_id, load_account_config, AdsClientError


def update_campaign_budget(campaign_id: int, new_daily_budget: float) -> dict:
    """Update the daily budget for a campaign."""
    client = get_client()
    customer_id = get_account_id(hyphenated=False)

    ga_service = client.get_service("GoogleAdsService")
    query = f"SELECT campaign.id, campaign.campaign_budget FROM campaign WHERE campaign.id = {campaign_id}"
    response = ga_service.search(customer_id=customer_id, query=query)
    budget_resource = None
    for row in response:
        budget_resource = row.campaign.campaign_budget
        break
    if not budget_resource:
        raise AdsClientError(f"Campaign {campaign_id} not found.")

    budget_service = client.get_service("CampaignBudgetService")
    budget_operation = client.get_type("CampaignBudgetOperation")
    budget = budget_operation.update
    budget.resource_name = budget_resource
    budget.amount_micros = int(new_daily_budget * 1_000_000)
    field_mask = client.get_type("FieldMask")
    field_mask.paths.append("amount_micros")
    budget_operation.update_mask.CopyFrom(field_mask)

    response = budget_service.mutate_campaign_budgets(
        customer_id=customer_id, operations=[budget_operation])
    return {"action": "update_budget", "campaign_id": campaign_id,
            "new_daily_budget": new_daily_budget,
            "resource": response.results[0].resource_name}


def update_keyword_bid(ad_group_id: int, criterion_id: int, new_cpc: float) -> dict:
    """Update the max CPC bid for a keyword."""
    client = get_client()
    customer_id = get_account_id(hyphenated=False)
    service = client.get_service("AdGroupCriterionService")
    operation = client.get_type("AdGroupCriterionOperation")
    criterion = operation.update
    criterion.resource_name = service.ad_group_criterion_path(customer_id, ad_group_id, criterion_id)
    criterion.cpc_bid_micros = int(new_cpc * 1_000_000)
    field_mask = client.get_type("FieldMask")
    field_mask.paths.append("cpc_bid_micros")
    operation.update_mask.CopyFrom(field_mask)
    response = service.mutate_ad_group_criteria(customer_id=customer_id, operations=[operation])
    return {"action": "update_keyword_bid", "ad_group_id": ad_group_id,
            "criterion_id": criterion_id, "new_cpc": new_cpc,
            "resource": response.results[0].resource_name}


def update_keyword_status(ad_group_id: int, criterion_id: int, status: str) -> dict:
    """Pause, enable, or remove a keyword."""
    client = get_client()
    customer_id = get_account_id(hyphenated=False)
    service = client.get_service("AdGroupCriterionService")
    valid_statuses = {"ENABLED", "PAUSED", "REMOVED"}
    if status.upper() not in valid_statuses:
        raise ValueError(f"Status must be one of {valid_statuses}, got '{status}'")
    operation = client.get_type("AdGroupCriterionOperation")
    if status.upper() == "REMOVED":
        operation.remove = service.ad_group_criterion_path(customer_id, ad_group_id, criterion_id)
    else:
        criterion = operation.update
        criterion.resource_name = service.ad_group_criterion_path(customer_id, ad_group_id, criterion_id)
        criterion.status = client.enums.AdGroupCriterionStatusEnum[status.upper()].value
        field_mask = client.get_type("FieldMask")
        field_mask.paths.append("status")
        operation.update_mask.CopyFrom(field_mask)
    response = service.mutate_ad_group_criteria(customer_id=customer_id, operations=[operation])
    return {"action": "update_keyword_status", "ad_group_id": ad_group_id,
            "criterion_id": criterion_id, "new_status": status.upper(),
            "resource": response.results[0].resource_name}


def create_responsive_search_ad(
    ad_group_id: int, headlines: list[str], descriptions: list[str],
    final_url: str, path1: str = "", path2: str = "",
) -> dict:
    """Create a new responsive search ad. Validates limits from config."""
    config = load_account_config()
    ad_rules = config.get("ad_copy", {})
    hl_max = ad_rules.get("headline_max_chars", 30)
    desc_max = ad_rules.get("description_max_chars", 90)
    path_max = ad_rules.get("path_max_chars", 15)

    for i, h in enumerate(headlines):
        if len(h) > hl_max:
            raise ValueError(f"Headline {i+1} exceeds {hl_max} chars ({len(h)}): '{h}'")
    for i, d in enumerate(descriptions):
        if len(d) > desc_max:
            raise ValueError(f"Description {i+1} exceeds {desc_max} chars ({len(d)}): '{d}'")
    if path1 and len(path1) > path_max:
        raise ValueError(f"Path1 exceeds {path_max} chars: '{path1}'")
    if path2 and len(path2) > path_max:
        raise ValueError(f"Path2 exceeds {path_max} chars: '{path2}'")
    if len(headlines) < ad_rules.get("min_headlines", 3):
        raise ValueError(f"Need at least {ad_rules.get('min_headlines', 3)} headlines")
    if len(descriptions) < ad_rules.get("min_descriptions", 2):
        raise ValueError(f"Need at least {ad_rules.get('min_descriptions', 2)} descriptions")

    client = get_client()
    customer_id = get_account_id(hyphenated=False)
    service = client.get_service("AdGroupAdService")
    operation = client.get_type("AdGroupAdOperation")
    ad_group_ad = operation.create
    ad_group_ad.ad_group = client.get_service("AdGroupService").ad_group_path(customer_id, ad_group_id)
    ad_group_ad.status = client.enums.AdGroupAdStatusEnum.PAUSED
    ad = ad_group_ad.ad
    ad.final_urls.append(final_url)
    for ht in headlines:
        h = client.get_type("AdTextAsset"); h.text = ht
        ad.responsive_search_ad.headlines.append(h)
    for dt in descriptions:
        d = client.get_type("AdTextAsset"); d.text = dt
        ad.responsive_search_ad.descriptions.append(d)
    if path1: ad.responsive_search_ad.path1 = path1
    if path2: ad.responsive_search_ad.path2 = path2
    response = service.mutate_ad_group_ads(customer_id=customer_id, operations=[operation])
    return {"action": "create_rsa", "ad_group_id": ad_group_id,
            "headlines": headlines, "descriptions": descriptions,
            "final_url": final_url, "status": "PAUSED",
            "resource": response.results[0].resource_name}
