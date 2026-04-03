"""Pull performance data from the Google Ads API.

Provides functions to fetch campaign, ad group, keyword, and ad-level
metrics for a given date range. Returns data as lists of dicts.
Account ID is read from config — nothing hardcoded.
"""

from datetime import date, timedelta
from typing import Optional

from .client import get_client, get_account_id


def _date_range(days: int) -> tuple[str, str]:
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def _run_query(query: str) -> list:
    client = get_client()
    service = client.get_service("GoogleAdsService")
    customer_id = get_account_id(hyphenated=False)
    results = []
    response = service.search(customer_id=customer_id, query=query)
    for row in response:
        results.append(row)
    return results


def get_campaign_performance(days: int = 7) -> list[dict]:
    """Get campaign-level performance metrics."""
    start, end = _date_range(days)
    query = f"""
        SELECT
            campaign.id, campaign.name, campaign.status,
            campaign.advertising_channel_type, campaign_budget.amount_micros,
            metrics.impressions, metrics.clicks, metrics.ctr,
            metrics.average_cpc, metrics.cost_micros, metrics.conversions,
            metrics.cost_per_conversion, metrics.search_impression_share,
            metrics.search_budget_lost_impression_share,
            metrics.search_rank_lost_impression_share
        FROM campaign
        WHERE segments.date BETWEEN '{start}' AND '{end}'
            AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
    """
    campaigns = []
    for row in _run_query(query):
        c, m, b = row.campaign, row.metrics, row.campaign_budget
        campaigns.append({
            "campaign_id": c.id, "campaign_name": c.name,
            "status": c.status.name, "channel": c.advertising_channel_type.name,
            "daily_budget": b.amount_micros / 1_000_000 if b.amount_micros else None,
            "impressions": m.impressions, "clicks": m.clicks, "ctr": m.ctr,
            "avg_cpc": m.average_cpc / 1_000_000 if m.average_cpc else 0,
            "cost": m.cost_micros / 1_000_000, "conversions": m.conversions,
            "cost_per_conversion": m.cost_per_conversion / 1_000_000 if m.cost_per_conversion else None,
            "impression_share": m.search_impression_share,
            "budget_lost_is": m.search_budget_lost_impression_share,
            "rank_lost_is": m.search_rank_lost_impression_share,
        })
    return campaigns


def get_ad_group_performance(campaign_id: Optional[int] = None, days: int = 7) -> list[dict]:
    """Get ad group-level performance metrics."""
    start, end = _date_range(days)
    where_clause = f"AND campaign.id = {campaign_id}" if campaign_id else ""
    query = f"""
        SELECT campaign.name, ad_group.id, ad_group.name, ad_group.status,
            metrics.impressions, metrics.clicks, metrics.ctr,
            metrics.average_cpc, metrics.cost_micros, metrics.conversions,
            metrics.cost_per_conversion
        FROM ad_group
        WHERE segments.date BETWEEN '{start}' AND '{end}'
            AND ad_group.status != 'REMOVED' {where_clause}
        ORDER BY metrics.cost_micros DESC
    """
    ad_groups = []
    for row in _run_query(query):
        ag, m = row.ad_group, row.metrics
        ad_groups.append({
            "campaign_name": row.campaign.name, "ad_group_id": ag.id,
            "ad_group_name": ag.name, "status": ag.status.name,
            "impressions": m.impressions, "clicks": m.clicks, "ctr": m.ctr,
            "avg_cpc": m.average_cpc / 1_000_000 if m.average_cpc else 0,
            "cost": m.cost_micros / 1_000_000, "conversions": m.conversions,
            "cost_per_conversion": m.cost_per_conversion / 1_000_000 if m.cost_per_conversion else None,
        })
    return ad_groups


def get_keyword_performance(campaign_id: Optional[int] = None, days: int = 7) -> list[dict]:
    """Get keyword-level performance metrics including quality score."""
    start, end = _date_range(days)
    where_clause = f"AND campaign.id = {campaign_id}" if campaign_id else ""
    query = f"""
        SELECT campaign.name, ad_group.name,
            ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type,
            ad_group_criterion.quality_info.quality_score, ad_group_criterion.status,
            metrics.impressions, metrics.clicks, metrics.ctr,
            metrics.average_cpc, metrics.cost_micros, metrics.conversions,
            metrics.cost_per_conversion
        FROM keyword_view
        WHERE segments.date BETWEEN '{start}' AND '{end}'
            AND ad_group_criterion.status != 'REMOVED' {where_clause}
        ORDER BY metrics.cost_micros DESC
    """
    keywords = []
    for row in _run_query(query):
        kw, m = row.ad_group_criterion, row.metrics
        keywords.append({
            "campaign_name": row.campaign.name, "ad_group_name": row.ad_group.name,
            "keyword": kw.keyword.text, "match_type": kw.keyword.match_type.name,
            "quality_score": kw.quality_info.quality_score if kw.quality_info.quality_score else None,
            "status": kw.status.name,
            "impressions": m.impressions, "clicks": m.clicks, "ctr": m.ctr,
            "avg_cpc": m.average_cpc / 1_000_000 if m.average_cpc else 0,
            "cost": m.cost_micros / 1_000_000, "conversions": m.conversions,
            "cost_per_conversion": m.cost_per_conversion / 1_000_000 if m.cost_per_conversion else None,
        })
    return keywords


def get_ad_performance(campaign_id: Optional[int] = None, days: int = 7) -> list[dict]:
    """Get ad-level performance metrics for RSAs."""
    start, end = _date_range(days)
    where_clause = f"AND campaign.id = {campaign_id}" if campaign_id else ""
    query = f"""
        SELECT campaign.name, ad_group.name,
            ad_group_ad.ad.id, ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            ad_group_ad.ad.final_urls, ad_group_ad.status,
            metrics.impressions, metrics.clicks, metrics.ctr,
            metrics.cost_micros, metrics.conversions
        FROM ad_group_ad
        WHERE segments.date BETWEEN '{start}' AND '{end}'
            AND ad_group_ad.status != 'REMOVED'
            AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD' {where_clause}
        ORDER BY metrics.impressions DESC
    """
    ads = []
    for row in _run_query(query):
        ad, m = row.ad_group_ad.ad, row.metrics
        headlines = [h.text for h in ad.responsive_search_ad.headlines] if ad.responsive_search_ad.headlines else []
        descriptions = [d.text for d in ad.responsive_search_ad.descriptions] if ad.responsive_search_ad.descriptions else []
        ads.append({
            "campaign_name": row.campaign.name, "ad_group_name": row.ad_group.name,
            "ad_id": ad.id, "headlines": headlines, "descriptions": descriptions,
            "final_urls": list(ad.final_urls) if ad.final_urls else [],
            "status": row.ad_group_ad.status.name,
            "impressions": m.impressions, "clicks": m.clicks, "ctr": m.ctr,
            "cost": m.cost_micros / 1_000_000, "conversions": m.conversions,
        })
    return ads
