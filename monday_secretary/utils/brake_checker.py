from __future__ import annotations

from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel


class BrakeResult(BaseModel):
    score: int
    level: int
    should_brake: bool
    why: str
    suggestions: List[str] = []


class BrakeChecker:
    def __init__(self):
        root = Path(__file__).resolve().parents[1]
        with open(root / "thresholds.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.score_weights = data.get("score_weights", {})
        self.judgement_rules = data.get("judgement_rules", {})
        self.periodic_rules = data.get("periodic_rules", {})

    def _calc_score(self, health: dict) -> int:
        score = 0
        for key, weight_map in self.score_weights.items():
            if key == "頻度ボーナス":
                continue
            val = health.get(key)
            if val is None:
                continue
            if isinstance(weight_map, dict):
                weight = weight_map.get(val)
                if weight:
                    score += int(weight)
        return score

    def _judge_level(self, score: int) -> int:
        for level_name, rule in self.judgement_rules.items():
            if eval(rule, {"score": score}):
                return int(level_name.replace("Level", ""))
        return 0

    def check(self, health: dict, work: dict | None = None) -> BrakeResult:
        score = self._calc_score(health)
        level = self._judge_level(score)
        should_brake = level >= 2
        why = f"score={score} level={level}"
        suggestions = []
        if should_brake:
            suggestions.append("Take a break and relax")
        return BrakeResult(
            score=score,
            level=level,
            should_brake=should_brake,
            why=why,
            suggestions=suggestions,
        )
