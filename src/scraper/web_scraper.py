"""
Webスクレイピングモジュール
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import aiohttp
from bs4 import BeautifulSoup

from ..config.settings import Settings
from ..utils.logger import create_progress_bar, validate_url


class WebPage:
    """Webページデータクラス"""
    
    def __init__(
        self,
        url: str,
        title: str = "",
        content: str = "",
        status_code: int = 200,
        fetch_time: Optional[float] = None,
        depth: int = 0,
        links: Optional[List[str]] = None
    ):
        self.url = url
        self.title = title
        self.content = content
        self.status_code = status_code
        self.fetch_time = fetch_time or time.time()
        self.depth = depth
        self.links = links or []
        self.error = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で返す"""
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "status_code": self.status_code,
            "fetch_time": self.fetch_time,
            "depth": self.depth,
            "links": self.links,
            "error": self.error
        }


class WebScraper:
    """Webスクレイパークラス"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        self.visited_urls: Set[str] = set()
        self.robots_cache: Dict[str, RobotFileParser] = {}
        
        # 統計情報
        self.stats = {
            "total_pages": 0,
            "successful_pages": 0,
            "failed_pages": 0,
            "skipped_pages": 0,
            "start_time": 0,
            "end_time": 0
        }
    
    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""
        await self._create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        await self._close_session()
    
    async def _create_session(self):
        """HTTPセッションを作成"""
        timeout = aiohttp.ClientTimeout(total=self.settings.scraping.timeout)
        headers = {
            'User-Agent': self.settings.scraping.user_agent
        }
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers,
            connector=aiohttp.TCPConnector(limit=self.settings.concurrent)
        )
    
    async def _close_session(self):
        """HTTPセッションを閉じる"""
        if self.session:
            await self.session.close()
    
    async def scrape(self) -> List[WebPage]:
        """スクレイピングを実行"""
        self.stats["start_time"] = time.time()
        
        if not validate_url(self.settings.url):
            raise ValueError(f"無効なURL: {self.settings.url}")
        
        async with self:
            pages = await self._scrape_recursive(
                self.settings.url, 
                max_depth=self.settings.depth,
                max_pages=self.settings.max_pages
            )
        
        self.stats["end_time"] = time.time()
        self._log_stats()
        
        return pages
    
    async def _scrape_recursive(
        self, 
        start_url: str, 
        max_depth: int, 
        max_pages: int
    ) -> List[WebPage]:
        """再帰的にページを取得"""
        pages = []
        url_queue = [(start_url, 0)]  # (URL, depth)
        
        progress_bar = create_progress_bar(max_pages, "スクレイピング中")
        
        try:
            while url_queue and len(pages) < max_pages:
                # 並列処理用のバッチを作成
                batch_size = min(self.settings.concurrent, len(url_queue), max_pages - len(pages))
                batch = []
                
                for _ in range(batch_size):
                    if url_queue:
                        batch.append(url_queue.pop(0))
                
                # バッチ処理
                batch_pages = await self._process_batch(batch)
                
                for page in batch_pages:
                    if page and len(pages) < max_pages:
                        pages.append(page)
                        progress_bar.update(1)
                        
                        # 新しいリンクを追加
                        if page.depth < max_depth:
                            for link in page.links:
                                if (link not in self.visited_urls and 
                                    len(url_queue) + len(pages) < max_pages * 2):  # キューが大きくなりすぎないように制限
                                    url_queue.append((link, page.depth + 1))
                
                # 遅延
                if self.settings.delay > 0:
                    await asyncio.sleep(self.settings.delay)
        
        finally:
            progress_bar.close()
        
        return pages
    
    async def _process_batch(self, batch: List[tuple]) -> List[Optional[WebPage]]:
        """バッチ処理"""
        tasks = []
        for url, depth in batch:
            if url not in self.visited_urls:
                self.visited_urls.add(url)
                tasks.append(self._fetch_page(url, depth))
        
        if not tasks:
            return []
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _fetch_page(self, url: str, depth: int) -> Optional[WebPage]:
        """単一ページを取得"""
        try:
            # robots.txtチェック
            if self.settings.scraping.respect_robots_txt:
                if not await self._is_allowed_by_robots(url):
                    self.logger.debug(f"robots.txtによりスキップ: {url}")
                    self.stats["skipped_pages"] += 1
                    return None
            
            # URLフィルタリング
            if not self.settings.is_url_allowed(url):
                self.logger.debug(f"除外パターンによりスキップ: {url}")
                self.stats["skipped_pages"] += 1
                return None
            
            # HTTPリクエスト
            async with self.session.get(url) as response:
                if response.status != 200:
                    self.logger.warning(f"HTTP {response.status}: {url}")
                    self.stats["failed_pages"] += 1
                    return None
                
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    self.logger.debug(f"HTMLでないためスキップ: {url}")
                    self.stats["skipped_pages"] += 1
                    return None
                
                html_content = await response.text()
                
                # HTMLを解析
                soup = BeautifulSoup(html_content, 'lxml')
                
                # タイトル取得
                title_tag = soup.find('title')
                title = title_tag.get_text().strip() if title_tag else ""
                
                # 本文取得
                content = self._extract_text_content(soup)
                
                # リンク取得
                links = self._extract_links(soup, url)
                
                page = WebPage(
                    url=url,
                    title=title,
                    content=content,
                    status_code=response.status,
                    fetch_time=time.time(),
                    depth=depth,
                    links=links
                )
                
                self.stats["successful_pages"] += 1
                self.logger.debug(f"取得成功: {url}")
                
                return page
        
        except Exception as e:
            self.logger.error(f"ページ取得エラー {url}: {e}")
            self.stats["failed_pages"] += 1
            return None
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """HTMLからテキストコンテンツを抽出"""
        # 不要な要素を除去
        for element in self.settings.parsing.remove_elements:
            for tag in soup.select(element):
                tag.decompose()
        
        # テキストを抽出
        text = soup.get_text()
        
        # 正規化
        if self.settings.parsing.clean_whitespace:
            import re
            # 複数の空白を1つに
            text = re.sub(r'\s+', ' ', text)
            # 複数の改行を2つに
            text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
            text = text.strip()
        
        return text
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """リンクを抽出"""
        links = []
        base_domain = urlparse(base_url).netloc
        
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']
            full_url = urljoin(base_url, href)
            
            # 同一ドメインのみ
            if urlparse(full_url).netloc == base_domain:
                # フラグメントを除去
                parsed = urlparse(full_url)
                clean_url = urlunparse((
                    parsed.scheme, parsed.netloc, parsed.path,
                    parsed.params, parsed.query, ''
                ))
                
                if clean_url not in links:
                    links.append(clean_url)
        
        return links
    
    async def _is_allowed_by_robots(self, url: str) -> bool:
        """robots.txtでアクセスが許可されているかチェック"""
        try:
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            if base_url not in self.robots_cache:
                robots_url = urljoin(base_url, '/robots.txt')
                
                try:
                    async with self.session.get(robots_url) as response:
                        if response.status == 200:
                            robots_content = await response.text()
                            rp = RobotFileParser()
                            rp.set_url(robots_url)
                            rp.read_content(robots_content)
                            self.robots_cache[base_url] = rp
                        else:
                            # robots.txtが存在しない場合は許可
                            return True
                except:
                    # robots.txtの取得に失敗した場合は許可
                    return True
            
            rp = self.robots_cache.get(base_url)
            if rp:
                user_agent = self.settings.scraping.user_agent
                return rp.can_fetch(user_agent, url)
            
            return True
        
        except:
            # エラーの場合は許可
            return True
    
    def _log_stats(self):
        """統計情報をログ出力"""
        duration = self.stats["end_time"] - self.stats["start_time"]
        
        self.logger.info("=== スクレイピング統計 ===")
        self.logger.info(f"実行時間: {duration:.1f}秒")
        self.logger.info(f"成功ページ数: {self.stats['successful_pages']}")
        self.logger.info(f"失敗ページ数: {self.stats['failed_pages']}")
        self.logger.info(f"スキップページ数: {self.stats['skipped_pages']}")
        
        if self.stats["successful_pages"] > 0:
            avg_time = duration / self.stats["successful_pages"]
            self.logger.info(f"平均取得時間: {avg_time:.2f}秒/ページ")
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return self.stats.copy()
