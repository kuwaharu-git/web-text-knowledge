"""
設定管理モジュール
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from urllib.parse import urlparse


@dataclass
class ScrapingConfig:
    """スクレイピング設定"""
    user_agent: str = "Mozilla/5.0 (compatible; DifyKnowledgeBot/1.0)"
    timeout: int = 30
    retry_count: int = 3
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "/admin/", "/login/", "*.pdf", "*.jpg", "*.png", "*.gif", "*.svg"
    ])
    respect_robots_txt: bool = True
    max_redirects: int = 5


@dataclass
class ParsingConfig:
    """テキスト解析設定"""
    remove_elements: List[str] = field(default_factory=lambda: [
        "nav", "footer", "aside", "header", ".advertisement", ".ads", 
        ".sidebar", ".menu", ".navigation", "script", "style"
    ])
    min_text_length: int = 100
    language: str = "ja"
    clean_whitespace: bool = True
    extract_metadata: bool = True


@dataclass
class OutputConfig:
    """出力設定"""
    filename_template: str = "{site_name}_{timestamp}"
    split_large_files: bool = True
    include_metadata: bool = True
    encoding: str = "utf-8"
    add_table_of_contents: bool = True


@dataclass
class DifyConfig:
    """Dify固有設定"""
    max_file_size_mb: int = 15
    max_chunk_size: int = 2000
    overlap_size: int = 200
    enable_chunking: bool = True
    optimize_for_search: bool = True


class Settings:
    """設定管理クラス"""
    
    def __init__(
        self,
        config_path: Optional[Path] = None,
        url: str = "",
        depth: int = 1,
        max_pages: int = 10,
        output_format: str = "all",
        output_dir: Path = Path("output"),
        delay: float = 1.0,
        concurrent: int = 3,
        max_file_size: int = 15,
        chunk_size: int = 2000
    ):
        self.url = url
        self.depth = depth
        self.max_pages = max_pages
        self.output_format = output_format
        self.output_dir = output_dir
        self.delay = delay
        self.concurrent = concurrent
        self.max_file_size = max_file_size
        self.chunk_size = chunk_size
        
        # 設定ファイルから読み込み
        self._load_config(config_path)
        
        # URLからサイト名を取得
        self.site_name = self._extract_site_name(url)
        
        # ロガー設定
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self, config_path: Optional[Path] = None):
        """設定ファイルを読み込み"""
        # デフォルト設定
        self.scraping = ScrapingConfig()
        self.parsing = ParsingConfig()
        self.output = OutputConfig()
        self.dify = DifyConfig()
        
        if config_path and config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 設定を更新
                if 'scraping' in config_data:
                    self._update_dataclass(self.scraping, config_data['scraping'])
                if 'parsing' in config_data:
                    self._update_dataclass(self.parsing, config_data['parsing'])
                if 'output' in config_data:
                    self._update_dataclass(self.output, config_data['output'])
                if 'dify' in config_data:
                    self._update_dataclass(self.dify, config_data['dify'])
                
                self.logger.info(f"設定ファイルを読み込みました: {config_path}")
                
            except Exception as e:
                self.logger.warning(f"設定ファイルの読み込みに失敗: {e}")
    
    def _update_dataclass(self, obj: Any, data: Dict[str, Any]):
        """データクラスを更新"""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
    
    def _extract_site_name(self, url: str) -> str:
        """URLからサイト名を抽出"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # www.を除去
            if domain.startswith('www.'):
                domain = domain[4:]
            # ドメイン名のみを取得（最初の部分）
            return domain.split('.')[0]
        except:
            return "unknown_site"
    
    def get_output_filename(self, format_type: str) -> str:
        """出力ファイル名を生成"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        template = self.output.filename_template
        
        filename = template.format(
            site_name=self.site_name,
            timestamp=timestamp
        )
        
        return f"{filename}.{format_type}"
    
    def is_url_allowed(self, url: str) -> bool:
        """URLが許可されているかチェック"""
        url_lower = url.lower()
        
        for pattern in self.scraping.exclude_patterns:
            if pattern.startswith('*.'):
                # 拡張子パターン
                extension = pattern[2:]
                if url_lower.endswith(f'.{extension}'):
                    return False
            else:
                # パスパターン
                if pattern in url_lower:
                    return False
        
        return True
    
    def get_max_file_size_bytes(self) -> int:
        """最大ファイルサイズをバイト単位で取得"""
        return self.dify.max_file_size_mb * 1024 * 1024
    
    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で返す"""
        return {
            "url": self.url,
            "depth": self.depth,
            "max_pages": self.max_pages,
            "output_format": self.output_format,
            "output_dir": str(self.output_dir),
            "delay": self.delay,
            "concurrent": self.concurrent,
            "max_file_size": self.max_file_size,
            "chunk_size": self.chunk_size,
            "site_name": self.site_name,
            "scraping": self.scraping.__dict__,
            "parsing": self.parsing.__dict__,
            "output": self.output.__dict__,
            "dify": self.dify.__dict__
        }
    
    def save_config(self, config_path: Path):
        """設定をファイルに保存"""
        try:
            config_data = {
                "scraping": self.scraping.__dict__,
                "parsing": self.parsing.__dict__,
                "output": self.output.__dict__,
                "dify": self.dify.__dict__
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"設定ファイルを保存しました: {config_path}")
            
        except Exception as e:
            self.logger.error(f"設定ファイルの保存に失敗: {e}")
            raise
