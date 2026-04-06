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
    create_recommend_tables,
)
from .engine import RecommenderEngine, RecommendationResult
from .collectors import BaseCollector, RSSCollector, OpenCLICollector, ContentItem