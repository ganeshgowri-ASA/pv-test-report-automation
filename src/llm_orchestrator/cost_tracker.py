"""Cost tracking and optimization for LLM usage."""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from .models import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


@dataclass
class CostStats:
    """Cost statistics."""

    total_cost: float = 0.0
    total_requests: int = 0
    total_tokens: int = 0
    by_provider: Dict[str, float] = field(default_factory=dict)
    by_date: Dict[str, float] = field(default_factory=dict)


class CostTracker:
    """Track and analyze LLM costs.

    Features:
    - Cost tracking per provider
    - Daily/monthly cost aggregation
    - Budget alerts
    - Cost optimization recommendations
    """

    def __init__(self, monthly_budget: Optional[float] = None):
        """Initialize cost tracker.

        Args:
            monthly_budget: Optional monthly budget in USD.
        """
        self.monthly_budget = monthly_budget
        self.responses: List[LLMResponse] = []
        logger.info(f"CostTracker initialized with budget: ${monthly_budget or 'unlimited'}")

    def track_response(self, response: LLMResponse) -> None:
        """Track an LLM response.

        Args:
            response: LLM response to track.
        """
        self.responses.append(response)
        logger.debug(
            f"Tracked response: {response.provider} - "
            f"${response.cost:.4f} - "
            f"{response.tokens_used} tokens"
        )

        # Check budget
        if self.monthly_budget:
            current_month_cost = self.get_monthly_cost()
            if current_month_cost > self.monthly_budget:
                logger.warning(
                    f"Monthly budget exceeded! "
                    f"Current: ${current_month_cost:.2f}, "
                    f"Budget: ${self.monthly_budget:.2f}"
                )
            elif current_month_cost > self.monthly_budget * 0.8:
                logger.warning(
                    f"80% of monthly budget reached! "
                    f"Current: ${current_month_cost:.2f}, "
                    f"Budget: ${self.monthly_budget:.2f}"
                )

    def get_total_cost(self) -> float:
        """Get total cost across all requests.

        Returns:
            Total cost in USD.
        """
        return sum(r.cost for r in self.responses)

    def get_daily_cost(self, date: Optional[datetime] = None) -> float:
        """Get cost for a specific day.

        Args:
            date: Date to get cost for. Defaults to today.

        Returns:
            Daily cost in USD.
        """
        if date is None:
            date = datetime.utcnow()

        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        return sum(
            r.cost for r in self.responses
            if day_start <= r.timestamp < day_end
        )

    def get_monthly_cost(self, year: Optional[int] = None, month: Optional[int] = None) -> float:
        """Get cost for a specific month.

        Args:
            year: Year. Defaults to current year.
            month: Month (1-12). Defaults to current month.

        Returns:
            Monthly cost in USD.
        """
        now = datetime.utcnow()
        year = year or now.year
        month = month or now.month

        return sum(
            r.cost for r in self.responses
            if r.timestamp.year == year and r.timestamp.month == month
        )

    def get_cost_by_provider(self) -> Dict[str, float]:
        """Get cost breakdown by provider.

        Returns:
            Dictionary mapping provider to total cost.
        """
        costs: Dict[str, float] = {}
        for response in self.responses:
            provider = response.provider.value
            costs[provider] = costs.get(provider, 0.0) + response.cost

        return costs

    def get_stats(self, days: int = 30) -> CostStats:
        """Get cost statistics.

        Args:
            days: Number of days to include in stats.

        Returns:
            Cost statistics.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_responses = [r for r in self.responses if r.timestamp >= cutoff]

        stats = CostStats(
            total_cost=sum(r.cost for r in recent_responses),
            total_requests=len(recent_responses),
            total_tokens=sum(r.tokens_used for r in recent_responses),
        )

        # By provider
        for response in recent_responses:
            provider = response.provider.value
            stats.by_provider[provider] = stats.by_provider.get(provider, 0.0) + response.cost

        # By date
        for response in recent_responses:
            date_key = response.timestamp.date().isoformat()
            stats.by_date[date_key] = stats.by_date.get(date_key, 0.0) + response.cost

        return stats

    def get_optimization_recommendations(self) -> List[str]:
        """Get cost optimization recommendations.

        Returns:
            List of recommendation strings.
        """
        recommendations = []

        cost_by_provider = self.get_cost_by_provider()
        if not cost_by_provider:
            return recommendations

        # Find most expensive provider
        most_expensive = max(cost_by_provider.items(), key=lambda x: x[1])

        # Calculate average cost per request by provider
        avg_costs = {}
        for response in self.responses:
            provider = response.provider.value
            if provider not in avg_costs:
                avg_costs[provider] = []
            avg_costs[provider].append(response.cost)

        for provider, costs in avg_costs.items():
            avg_costs[provider] = sum(costs) / len(costs)

        # Generate recommendations
        if "anthropic" in cost_by_provider and "openai" in cost_by_provider:
            if cost_by_provider["anthropic"] > cost_by_provider["openai"] * 1.5:
                recommendations.append(
                    "Consider using OpenAI more frequently - it's currently more cost-effective"
                )

        if "google" in avg_costs:
            recommendations.append(
                f"Google Gemini has lowest average cost per request (${avg_costs['google']:.4f}). "
                "Consider using it for simpler tasks."
            )

        total_cost = self.get_total_cost()
        if total_cost > 100:
            recommendations.append(
                "High total cost detected. Consider implementing request caching or "
                "reducing max_tokens for simple queries."
            )

        if self.monthly_budget:
            monthly_cost = self.get_monthly_cost()
            if monthly_cost > self.monthly_budget * 0.9:
                recommendations.append(
                    f"Approaching monthly budget limit (${monthly_cost:.2f} / ${self.monthly_budget:.2f}). "
                    "Consider using cheaper models or reducing request volume."
                )

        return recommendations
