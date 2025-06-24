"""
テキスト解析モジュール
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..scraper.web_scraper import WebPage
from ..config.settings import Settings
from ..utils.logger import estimate_tokens


class ParsedPage:
    """解析済みページデータクラス"""
    
    def __init__(
        self,
        url: str,
        title: str,
        content: str,
        metadata: Dict[str, Any],
        tokens: int = 0,
        keywords: Optional[List[str]] = None
    ):
        self.url = url
        self.title = title
        self.content = content
        self.metadata = metadata
        self.tokens = tokens
        self.keywords = keywords or []
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で返す"""
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "metadata": self.metadata,
            "tokens": self.tokens,
            "keywords": self.keywords
        }


class TextParser:
    """テキスト解析クラス"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # 統計情報
        self.stats = {
            "total_pages": 0,
            "processed_pages": 0,
            "skipped_pages": 0,
            "total_characters": 0,
            "total_tokens": 0
        }
    
    def parse(self, pages: List[WebPage]) -> List[ParsedPage]:
        """ページリストを解析"""
        self.logger.info(f"テキスト解析開始: {len(pages)} ページ")
        
        parsed_pages = []
        
        for page in pages:
            try:
                parsed_page = self._parse_page(page)
                if parsed_page:
                    parsed_pages.append(parsed_page)
                    self.stats["processed_pages"] += 1
                    self.stats["total_characters"] += len(parsed_page.content)
                    self.stats["total_tokens"] += parsed_page.tokens
                else:
                    self.stats["skipped_pages"] += 1
            except Exception as e:
                self.logger.error(f"ページ解析エラー {page.url}: {e}")
                self.stats["skipped_pages"] += 1
        
        self.stats["total_pages"] = len(pages)
        self._log_stats()
        
        return parsed_pages
    
    def _parse_page(self, page: WebPage) -> Optional[ParsedPage]:
        """単一ページを解析"""
        # 最小文字数チェック
        if len(page.content) < self.settings.parsing.min_text_length:
            self.logger.debug(f"文字数不足によりスキップ: {page.url}")
            return None
        
        # コンテンツをクリーンアップ
        cleaned_content = self._clean_content(page.content)
        
        if not cleaned_content.strip():
            self.logger.debug(f"コンテンツが空のためスキップ: {page.url}")
            return None
        
        # メタデータ作成
        metadata = self._create_metadata(page)
        
        # トークン数計算
        tokens = estimate_tokens(cleaned_content)
        
        # キーワード抽出
        keywords = self._extract_keywords(cleaned_content, page.title)
        
        parsed_page = ParsedPage(
            url=page.url,
            title=page.title,
            content=cleaned_content,
            metadata=metadata,
            tokens=tokens,
            keywords=keywords
        )
        
        return parsed_page
    
    def _clean_content(self, content: str) -> str:
        """コンテンツをクリーンアップ"""
        # 基本的なクリーンアップ
        text = content.strip()
        
        # 複数の空白を1つに
        text = re.sub(r'[ \t]+', ' ', text)
        
        # 複数の改行を最大2つに
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # 行頭・行末の空白を除去
        lines = []
        for line in text.split('\n'):
            cleaned_line = line.strip()
            if cleaned_line:
                lines.append(cleaned_line)
            else:
                # 空行は保持するが、連続する空行は1つに
                if lines and lines[-1] != '':
                    lines.append('')
        
        text = '\n'.join(lines)
        
        # 特殊文字の正規化
        text = self._normalize_special_chars(text)
        
        return text
    
    def _normalize_special_chars(self, text: str) -> str:
        """特殊文字を正規化"""
        # Unicode正規化
        import unicodedata
        text = unicodedata.normalize('NFKC', text)
        
        # 特殊な空白文字を通常の空白に
        text = re.sub(r'[\u00A0\u2000-\u200B\u2028\u2029]', ' ', text)
        
        # 制御文字を除去（改行とタブは保持）
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        return text
    
    def _create_metadata(self, page: WebPage) -> Dict[str, Any]:
        """メタデータを作成"""
        metadata = {
            "url": page.url,
            "title": page.title,
            "fetch_time": datetime.fromtimestamp(page.fetch_time).isoformat(),
            "depth": page.depth,
            "character_count": len(page.content),
            "status_code": page.status_code
        }
        
        if self.settings.parsing.extract_metadata:
            # 追加のメタデータ
            metadata.update({
                "word_count": len(page.content.split()),
                "paragraph_count": len([p for p in page.content.split('\n\n') if p.strip()]),
                "link_count": len(page.links)
            })
        
        return metadata
    
    def _extract_keywords(self, content: str, title: str) -> List[str]:
        """キーワードを抽出"""
        keywords = []
        
        # タイトルから重要語を抽出
        if title:
            title_words = self._extract_important_words(title)
            keywords.extend(title_words)
        
        # コンテンツから重要語を抽出（最初の500文字から）
        content_sample = content[:500]
        content_words = self._extract_important_words(content_sample)
        keywords.extend(content_words)
        
        # 重複除去と制限
        unique_keywords = []
        for keyword in keywords:
            if keyword not in unique_keywords and len(unique_keywords) < 10:
                unique_keywords.append(keyword)
        
        return unique_keywords
    
    def _extract_important_words(self, text: str) -> List[str]:
        """重要語を抽出（簡易版）"""
        import re
        
        # 基本的な単語抽出
        words = []
        
        # 日本語の場合（簡易的な処理）
        if self.settings.parsing.language == 'ja':
            # カタカナ語を抽出
            katakana_words = re.findall(r'[ァ-ヶー]{2,}', text)
            words.extend(katakana_words)
            
            # アルファベット語を抽出
            alpha_words = re.findall(r'[A-Za-z]{3,}', text)
            words.extend(alpha_words)
        
        else:
            # 英語の場合
            alpha_words = re.findall(r'\b[A-Za-z]{3,}\b', text)
            words.extend(alpha_words)
        
        # 頻度でフィルタリング（簡易版）
        word_freq = {}
        for word in words:
            word_lower = word.lower()
            word_freq[word_lower] = word_freq.get(word_lower, 0) + 1
        
        # 頻度が高く、一般的でない語を選出
        common_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use',
            'この', 'その', 'あの', 'これ', 'それ', 'あれ', 'ここ', 'そこ', 'あそこ', 'です', 'ます', 'した', 'して', 'する', 'される', 'なる', 'ある', 'いる', 'から', 'まで', 'より', 'では', 'でも', 'など', 'として', 'について', 'により', 'による'
        }
        
        important_words = []
        for word, freq in sorted(word_freq.items(), key=lambda x: x[1], reverse=True):
            if word not in common_words and len(word) >= 2:
                important_words.append(word)
                if len(important_words) >= 5:
                    break
        
        return important_words
    
    def _log_stats(self):
        """統計情報をログ出力"""
        self.logger.info("=== テキスト解析統計 ===")
        self.logger.info(f"処理ページ数: {self.stats['processed_pages']}")
        self.logger.info(f"スキップページ数: {self.stats['skipped_pages']}")
        self.logger.info(f"総文字数: {self.stats['total_characters']:,}")
        self.logger.info(f"総トークン数: {self.stats['total_tokens']:,}")
        
        if self.stats["processed_pages"] > 0:
            avg_chars = self.stats["total_characters"] / self.stats["processed_pages"]
            avg_tokens = self.stats["total_tokens"] / self.stats["processed_pages"]
            self.logger.info(f"平均文字数: {avg_chars:.0f}")
            self.logger.info(f"平均トークン数: {avg_tokens:.0f}")
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return self.stats.copy()
