"""Cost tracking for GPT API usage."""

import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock


class CostTracker:
    """Track and manage GPT API costs."""

    def __init__(
        self,
        storage_path: Optional[str] = None,
        alert_threshold_usd: float = 100.0
    ):
        """
        Initialize cost tracker.

        Args:
            storage_path: Path to store cost data
            alert_threshold_usd: Alert when costs exceed this threshold
        """
        self.storage_path = storage_path or "cost_data.json"
        self.alert_threshold_usd = alert_threshold_usd
        self._lock = Lock()
        self._costs: List[Dict] = []
        self._load_costs()

    def _load_costs(self) -> None:
        """Load cost data from storage."""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    self._costs = data.get("costs", [])
        except Exception as e:
            print(f"Warning: Could not load cost data: {e}")
            self._costs = []

    def _save_costs(self) -> None:
        """Save cost data to storage."""
        try:
            with open(self.storage_path, "w") as f:
                json.dump({"costs": self._costs}, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cost data: {e}")

    def record_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Record API usage cost.

        Args:
            model: Model used
            prompt_tokens: Tokens in prompt
            completion_tokens: Tokens in completion
            cost_usd: Cost in USD
            metadata: Additional metadata
        """
        with self._lock:
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "cost_usd": cost_usd,
                "metadata": metadata or {}
            }
            self._costs.append(entry)
            self._save_costs()

            # Check if threshold exceeded
            total_cost = self.get_total_cost()
            if total_cost >= self.alert_threshold_usd:
                print(
                    f"⚠️  Cost Alert: Total costs (${total_cost:.2f}) "
                    f"exceed threshold (${self.alert_threshold_usd:.2f})"
                )

    def get_total_cost(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        """
        Get total cost for a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Total cost in USD
        """
        with self._lock:
            filtered_costs = self._costs

            if start_date:
                filtered_costs = [
                    c for c in filtered_costs
                    if datetime.fromisoformat(c["timestamp"]) >= start_date
                ]

            if end_date:
                filtered_costs = [
                    c for c in filtered_costs
                    if datetime.fromisoformat(c["timestamp"]) <= end_date
                ]

            return sum(c["cost_usd"] for c in filtered_costs)

    def get_cost_by_model(self) -> Dict[str, float]:
        """Get total cost broken down by model."""
        with self._lock:
            model_costs: Dict[str, float] = {}
            for entry in self._costs:
                model = entry["model"]
                model_costs[model] = model_costs.get(model, 0.0) + entry["cost_usd"]
            return model_costs

    def get_stats(self, days: int = 30) -> Dict:
        """
        Get cost statistics.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with cost statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        with self._lock:
            recent_costs = [
                c for c in self._costs
                if datetime.fromisoformat(c["timestamp"]) >= start_date
            ]

            if not recent_costs:
                return {
                    "total_cost_usd": 0.0,
                    "total_requests": 0,
                    "total_tokens": 0,
                    "average_cost_per_request": 0.0,
                    "cost_by_model": {},
                    "days_analyzed": days
                }

            total_cost = sum(c["cost_usd"] for c in recent_costs)
            total_tokens = sum(c["total_tokens"] for c in recent_costs)

            model_costs: Dict[str, float] = {}
            for entry in recent_costs:
                model = entry["model"]
                model_costs[model] = model_costs.get(model, 0.0) + entry["cost_usd"]

            return {
                "total_cost_usd": total_cost,
                "total_requests": len(recent_costs),
                "total_tokens": total_tokens,
                "average_cost_per_request": total_cost / len(recent_costs),
                "cost_by_model": model_costs,
                "days_analyzed": days
            }

    def reset(self, confirm: bool = False) -> None:
        """
        Reset all cost data.

        Args:
            confirm: Must be True to actually reset
        """
        if not confirm:
            raise ValueError("Must confirm reset by passing confirm=True")

        with self._lock:
            self._costs = []
            self._save_costs()
