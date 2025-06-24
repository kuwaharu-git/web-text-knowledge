"""
基本的なテストケース
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch

from src.config.settings import Settings
from src.scraper.web_scraper import WebScraper, WebPage
from src.parser.text_parser import TextParser, ParsedPage
from src.dify_generator.file_generator import DifyFileGenerator


class TestSettings:
    """設定テスト"""
    
    def test_settings_initialization(self):
        """設定の初期化テスト"""
        settings = Settings(
            url="https://example.com",
            depth=2,
            max_pages=10
        )
        
        assert settings.url == "https://example.com"
        assert settings.depth == 2
        assert settings.max_pages == 10
        assert settings.site_name == "example"
    
    def test_url_filtering(self):
        """URL フィルタリングテスト"""
        settings = Settings(url="https://example.com")
        
        assert settings.is_url_allowed("https://example.com/page1")
        assert not settings.is_url_allowed("https://example.com/admin/")
        assert not settings.is_url_allowed("https://example.com/image.jpg")


class TestTextParser:
    """テキスト解析テスト"""
    
    def test_parse_page(self):
        """ページ解析テスト"""
        settings = Settings(url="https://example.com")
        parser = TextParser(settings)
        
        # テスト用のWebページ
        web_page = WebPage(
            url="https://example.com/test",
            title="テストページ",
            content="これはテスト用のコンテンツです。" * 20,  # 最小文字数を満たすように
            depth=1
        )
        
        parsed_pages = parser.parse([web_page])
        
        assert len(parsed_pages) == 1
        assert parsed_pages[0].title == "テストページ"
        assert "テスト用のコンテンツ" in parsed_pages[0].content
        assert parsed_pages[0].tokens > 0
    
    def test_content_cleaning(self):
        """コンテンツクリーニングテスト"""
        settings = Settings(url="https://example.com")
        parser = TextParser(settings)
        
        # 不正なスペースや改行を含むコンテンツ
        dirty_content = "  テスト  \n\n\n  コンテンツ  \n\n\n  です  "
        cleaned = parser._clean_content(dirty_content)
        
        assert "テスト\n\nコンテンツ\n\nです" in cleaned


class TestDifyFileGenerator:
    """Difyファイル生成テスト"""
    
    def test_file_generation(self, tmp_path):
        """ファイル生成テスト"""
        # 一時ディレクトリを設定
        settings = Settings(
            url="https://example.com",
            output_dir=tmp_path,
            output_format="txt"
        )
        
        generator = DifyFileGenerator(settings)
        
        # テスト用の解析済みページ
        parsed_page = ParsedPage(
            url="https://example.com/test",
            title="テストページ",
            content="これはテスト用のコンテンツです。" * 50,
            metadata={
                "fetch_time": "2024-06-24T10:30:00",
                "character_count": 100,
                "depth": 1
            },
            tokens=100
        )
        
        generated_files = generator.generate([parsed_page])
        
        assert len(generated_files) > 0
        assert generated_files[0].exists()
        
        # ファイル内容の確認
        content = generated_files[0].read_text(encoding='utf-8')
        assert "テストページ" in content
        assert "テスト用のコンテンツ" in content


@pytest.mark.asyncio
class TestWebScraper:
    """Webスクレイパーテスト"""
    
    async def test_page_fetch_mock(self):
        """モックを使ったページ取得テスト"""
        settings = Settings(
            url="https://example.com",
            depth=1,
            max_pages=1
        )
        
        # モックHTMLレスポンス
        mock_html = """
        <html>
            <head><title>テストページ</title></head>
            <body>
                <h1>メインコンテンツ</h1>
                <p>これはテスト用のコンテンツです。</p>
                <a href="/page2">関連ページ</a>
            </body>
        </html>
        """
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # モックレスポンスの設定
            mock_response = Mock()
            mock_response.status = 200
            mock_response.headers = {'content-type': 'text/html'}
            mock_response.text = Mock(return_value=mock_html)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            scraper = WebScraper(settings)
            page = await scraper._fetch_page("https://example.com", 0)
            
            assert page is not None
            assert page.title == "テストページ"
            assert "メインコンテンツ" in page.content
            assert "テスト用のコンテンツ" in page.content


if __name__ == "__main__":
    pytest.main([__file__])
