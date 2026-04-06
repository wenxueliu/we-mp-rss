"""推荐引擎模块"""
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session


@dataclass
class RecommendationResult:
    """推荐结果"""
    content_id: int
    title: str
    url: str
    score: float
    freshness: float
    preference_match: float
    quality: float
    timeliness: float
    reason: str

    @property
    def status(self) -> str:
        """根据分数判断推荐状态"""
        if self.score >= 60:
            return "recommended"
        elif self.score < 40:
            return "not_recommended"
        else:
            return "pending"


def calculate_content_status(score: float) -> str:
    """根据分数计算内容状态"""
    if score >= 60:
        return "recommended"
    elif score < 40:
        return "not_recommended"
    else:
        return "pending"


class RecommenderEngine:
    """推荐引擎"""

    def __init__(
        self,
        freshness_weight: float = 0.4,
        preference_weight: float = 0.3,
        quality_weight: float = 0.2,
        timeliness_weight: float = 0.1,
    ):
        self.freshness_weight = freshness_weight
        self.preference_weight = preference_weight
        self.quality_weight = quality_weight
        self.timeliness_weight = timeliness_weight

    def calculate_score(
        self,
        content: Any,
        user_preferences: Dict[str, Any] = None,
        similarity_scores: List[float] = None,
    ) -> RecommendationResult:
        """计算单个内容的推荐分数"""
        if user_preferences is None:
            user_preferences = {}
        """计算单个内容的推荐分数"""
        # 计算新鲜度
        freshness = self._calculate_freshness(content, similarity_scores or [])
        # 计算偏好匹配
        preference_match = self._calculate_preference_match(content, user_preferences)
        # 计算质量
        quality = self._calculate_quality(content)
        # 计算时效性
        timeliness = self._calculate_timeliness(content)
        # 综合分数
        score = (
            freshness * self.freshness_weight
            + preference_match * self.preference_weight
            + quality * self.quality_weight
            + timeliness * self.timeliness_weight
        )
        # 生成推荐理由
        reason = self._generate_reason(freshness, preference_match, quality, timeliness, content)

        return RecommendationResult(
            content_id=content.id if hasattr(content, "id") else 0,
            title=content.title if hasattr(content, "title") else "",
            url=content.url if hasattr(content, "url") else "",
            score=round(score, 2),
            freshness=round(freshness, 2),
            preference_match=round(preference_match, 2),
            quality=round(quality, 2),
            timeliness=round(timeliness, 2),
            reason=reason,
        )

    def _calculate_freshness(self, content: Any, similarity_scores: List[float] = None) -> float:
        """计算新鲜度分数"""
        freshness = 50.0
        if similarity_scores:
            max_similarity = max(similarity_scores) if similarity_scores else 0
            freshness = freshness - (max_similarity * 30)
        created_at = getattr(content, "published_at", None) or getattr(content, "created_at", None)
        if created_at:
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at)
                except:
                    created_at = None
            if created_at:
                now = datetime.utcnow()
                if created_at.tzinfo:
                    now = now.replace(tzinfo=created_at.tzinfo)
                days_old = (now - created_at).days
                if days_old <= 7:
                    freshness += 40
                elif days_old <= 30:
                    freshness += 20
                elif days_old <= 90:
                    freshness -= 10
                else:
                    freshness -= 30
        return max(0.0, min(100.0, freshness))

    def _calculate_preference_match(self, content: Any, user_preferences: Dict[str, Any]) -> float:
        """计算偏好匹配分数"""
        score = 50.0
        topic_weights = user_preferences.get("topic_weights", {})
        if topic_weights and hasattr(content, "tags"):
            tags = content.tags
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except:
                    tags = []
            for tag in tags:
                if tag in topic_weights:
                    score += topic_weights[tag] * 0.5
        blocked_topics = user_preferences.get("blocked_topics", [])
        if blocked_topics and hasattr(content, "tags"):
            tags = content.tags
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except:
                    tags = []
            for tag in tags:
                if tag in blocked_topics:
                    return 0.0
        return max(0.0, min(100.0, score))

    def _calculate_quality(self, content: Any) -> float:
        """计算内容质量分数"""
        score = 50.0
        title = getattr(content, "title", "")
        if title:
            title_len = len(title)
            if 20 <= title_len <= 100:
                score += 15
            elif 10 <= title_len <= 150:
                score += 10
        description = getattr(content, "description", "")
        if description and len(description) > 50:
            score += 15
        author = getattr(content, "author", "")
        if author:
            score += 10
        thumbnail = getattr(content, "thumbnail", "")
        if thumbnail:
            score += 10
        return max(0.0, min(100.0, score))

    def _calculate_timeliness(self, content: Any) -> float:
        """计算时效性分数"""
        published_at = getattr(content, "published_at", None)
        if not published_at:
            return 50.0
        if isinstance(published_at, str):
            try:
                published_at = datetime.fromisoformat(published_at)
            except:
                return 50.0
        now = datetime.utcnow()
        if published_at.tzinfo:
            now = now.replace(tzinfo=published_at.tzinfo)
        days_old = (now - published_at).days
        if days_old <= 0:
            return 100.0
        elif days_old <= 7:
            return 100.0 - (days_old * 5)
        elif days_old <= 30:
            return 65.0 - ((days_old - 7) * 1.5)
        else:
            return max(0.0, 30.0 - ((days_old - 30) * 0.5))

    def _generate_reason(self, freshness: float, preference_match: float, quality: float, timeliness: float, content: Any) -> str:
        """生成推荐理由"""
        reasons = []
        if freshness >= 80:
            reasons.append("高度新鲜的内容")
        elif freshness >= 60:
            reasons.append("较为新颖")
        if preference_match >= 70:
            reasons.append("符合您的兴趣")
        elif preference_match >= 50:
            reasons.append("可能感兴趣")
        if quality >= 70:
            reasons.append("内容质量高")
        if timeliness >= 80:
            reasons.append("最新发布")
        elif timeliness >= 60:
            reasons.append("时效性好")
        if not reasons:
            reasons.append("推荐给您")
        return " | ".join(reasons)

    def update_user_preferences(
        self,
        current_preferences: Dict[str, Any],
        content: Any,
        action: str,
        learning_rate: float = 0.1,
    ) -> Dict[str, Any]:
        """根据用户行为更新偏好"""
        preferences = current_preferences.copy()
        tags = []
        if hasattr(content, "tags") and content.tags:
            tags = content.tags
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except:
                    tags = []
            if not isinstance(tags, list):
                tags = []
        if "topic_weights" not in preferences:
            preferences["topic_weights"] = {}
        topic_weights = preferences["topic_weights"]
        if action == "like":
            for tag in tags:
                current = topic_weights.get(tag, 50.0)
                topic_weights[tag] = current * (1 - learning_rate) + 100 * learning_rate
        elif action == "dislike":
            for tag in tags:
                current = topic_weights.get(tag, 50.0)
                topic_weights[tag] = current * (1 - learning_rate) + 0 * learning_rate
        elif action == "skip":
            for tag in tags:
                current = topic_weights.get(tag, 50.0)
                topic_weights[tag] = current * (1 - learning_rate * 0.5) + 25 * learning_rate * 0.5
        preferences["topic_weights"] = topic_weights
        return preferences

    def batch_calculate(
        self,
        contents: List[Any],
        user_preferences: Dict[str, Any],
        similarity_scores: List[List[float]] = None,
    ) -> List[RecommendationResult]:
        """批量计算推荐分数"""
        results = []
        for i, content in enumerate(contents):
            scores = similarity_scores[i] if similarity_scores and i < len(similarity_scores) else None
            results.append(self.calculate_score(content, user_preferences, scores))
        return sorted(results, key=lambda x: x.score, reverse=True)