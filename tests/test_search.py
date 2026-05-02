"""搜索 API 单元测试"""
import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from web import app
from apis.search import get_session

client = TestClient(app)


def create_mock_query(total=0, items=None):
    """创建 mock 查询对象"""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.count.return_value = total
    mock_query.all.return_value = items or []
    return mock_query


def create_mock_item(id=1, title="", description="", url="", author="", source_type="", source_name="", published_at=None):
    """创建 mock 内容项"""
    item = MagicMock()
    item.id = id
    item.title = title
    item.description = description
    item.url = url
    item.author = author
    item.source_type = source_type
    item.source_name = source_name
    item.published_at = published_at
    return item


class TestSearchAPI(unittest.TestCase):
    """搜索接口单元测试 — UT-API-1 至 UT-API-9"""

    def setUp(self):
        self.base_url = "/api/v1/wx/search"
        self.mock_session = MagicMock()

    def _override_session(self):
        return self.mock_session

    # ── UT-API-1: 正常搜索 ──
    def test_search_normal(self):
        """UT-API-1: 正常搜索 — q=Python 应返回匹配结果"""
        item = create_mock_item(
            id=1, title="Python 异步编程指南", description="深入理解 asyncio",
            url="https://example.com/python-async", author="test_author",
            source_type="rss", source_name="test_source"
        )
        mock_query = create_mock_query(total=1, items=[item])
        self.mock_session.query.return_value = mock_query

        app.dependency_overrides[get_session] = self._override_session
        response = client.get(self.base_url, params={"q": "Python"})
        app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["data"]["total"], 1)
        items = data["data"]["items"]
        self.assertEqual(len(items), 1)
        self.assertIn("Python", items[0]["title"])

    # ── UT-API-2: 大小写不敏感 ──
    def test_search_case_insensitive(self):
        """UT-API-2: 大小写不敏感 — q=PYTHON 应同样匹配"""
        item = create_mock_item(
            id=1, title="Python 异步编程指南", description="深入理解 asyncio"
        )
        mock_query = create_mock_query(total=1, items=[item])
        self.mock_session.query.return_value = mock_query

        app.dependency_overrides[get_session] = self._override_session
        response = client.get(self.base_url, params={"q": "PYTHON"})
        app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], 0)

    # ── UT-API-3: 匹配摘要 ──
    def test_search_match_summary(self):
        """UT-API-3: 匹配摘要 — 应通过 description 字段匹配"""
        item = create_mock_item(
            id=2, title="Rust 入门", description="Rust 是一门系统编程语言"
        )
        mock_query = create_mock_query(total=1, items=[item])
        self.mock_session.query.return_value = mock_query

        app.dependency_overrides[get_session] = self._override_session
        response = client.get(self.base_url, params={"q": "系统编程"})
        app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data"]["total"], 1)
        self.assertEqual(len(data["data"]["items"]), 1)
        self.assertIn("Rust", data["data"]["items"][0]["title"])

    # ── UT-API-4: 无匹配 ──
    def test_search_no_match(self):
        """UT-API-4: 无匹配 — q=zzz123 应返回空列表"""
        mock_query = create_mock_query(total=0, items=[])
        self.mock_session.query.return_value = mock_query

        app.dependency_overrides[get_session] = self._override_session
        response = client.get(self.base_url, params={"q": "zzz123"})
        app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["data"]["total"], 0)
        self.assertEqual(data["data"]["items"], [])

    # ── UT-API-5: 空关键词 ──
    def test_search_empty_keyword(self):
        """UT-API-5: 空关键词 — q= 应返回 400"""
        response = client.get(self.base_url, params={"q": ""})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], 400)
        self.assertIn("关键词不能为空", data["message"])

    # ── UT-API-6: 缺少参数 ──
    def test_search_missing_param(self):
        """UT-API-6: 缺少参数 — 不传 q 应返回 422"""
        response = client.get(self.base_url)

        self.assertEqual(response.status_code, 422)

    # ── UT-API-7: 特殊字符 ──
    def test_search_special_chars(self):
        """UT-API-7: 特殊字符 — q=<script> 应正常工作不报错"""
        mock_query = create_mock_query(total=0, items=[])
        self.mock_session.query.return_value = mock_query

        app.dependency_overrides[get_session] = self._override_session
        response = client.get(self.base_url, params={"q": "<script>"})
        app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], 0)

    # ── UT-API-8: 超长关键词 ──
    def test_search_long_keyword(self):
        """UT-API-8: 超长关键词 — 超过 200 字符应截断"""
        mock_query = create_mock_query(total=0, items=[])
        self.mock_session.query.return_value = mock_query

        app.dependency_overrides[get_session] = self._override_session
        long_keyword = "x" * 500
        response = client.get(self.base_url, params={"q": long_keyword})
        app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], 0)

    # ── UT-API-9: DB 异常 ──
    def test_search_db_error(self):
        """UT-API-9: DB 异常 — 数据库错误应返回 500"""
        self.mock_session.query.side_effect = RuntimeError("database connection lost")

        app.dependency_overrides[get_session] = self._override_session
        response = client.get(self.base_url, params={"q": "test"})
        app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("internal_error", data.get("detail", {}).get("error", ""))


if __name__ == "__main__":
    unittest.main()
