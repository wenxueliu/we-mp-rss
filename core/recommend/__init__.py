"""
Recommend module for content recommendation.
"""
from .models import (
    RecommendSource,
    RecommendContent,
    RecommendInteraction,
    RecommendPreference,
    RecommendKnowledge,
    RecommendSourcePreset,
    init_recommend_db,
)
from .engine import RecommenderEngine, RecommendationResult
from .collectors import BaseCollector, RSSCollector, OpenCLICollector, ContentItem