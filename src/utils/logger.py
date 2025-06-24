"""
ユーティリティモジュール
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """ロガーを設定"""
    
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # ルートロガーを取得
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # 既存のハンドラーをクリア
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(format_string)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # ファイルハンドラー（オプション）
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(format_string)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def format_bytes(bytes_count: int) -> str:
    """バイト数を人間が読みやすい形式でフォーマット"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} TB"


def sanitize_filename(filename: str) -> str:
    """ファイル名に使用できない文字を除去"""
    import re
    
    # 使用できない文字を除去
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # 連続するアンダースコアを1つに
    filename = re.sub(r'_+', '_', filename)
    
    # 先頭・末尾のアンダースコアを除去
    filename = filename.strip('_')
    
    # 空の場合はデフォルト名
    if not filename:
        filename = "untitled"
    
    # 長すぎる場合は切り詰め
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename


def estimate_tokens(text: str) -> int:
    """テキストのトークン数を推定（簡易版）"""
    # 日本語テキストの場合、文字数の約0.7倍がトークン数の目安
    # 英語の場合は単語数の約1.3倍
    
    import re
    
    # 日本語文字の割合を計算
    japanese_chars = len(re.findall(r'[ひらがなカタカナ漢字]', text))
    total_chars = len(text)
    
    if total_chars == 0:
        return 0
    
    japanese_ratio = japanese_chars / total_chars
    
    if japanese_ratio > 0.3:
        # 日本語が多い場合
        return int(total_chars * 0.7)
    else:
        # 英語が多い場合
        words = len(text.split())
        return int(words * 1.3)


def validate_url(url: str) -> bool:
    """URLの妥当性を検証"""
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(url)
        return all([parsed.scheme, parsed.netloc])
    except:
        return False


def create_progress_bar(total: int, desc: str = "Processing"):
    """プログレスバーを作成"""
    try:
        from tqdm import tqdm
        return tqdm(total=total, desc=desc, unit="page")
    except ImportError:
        # tqdmが利用できない場合の簡易版
        class SimpleProgressBar:
            def __init__(self, total, desc):
                self.total = total
                self.desc = desc
                self.current = 0
            
            def update(self, n=1):
                self.current += n
                percent = (self.current / self.total) * 100
                print(f"\r{self.desc}: {self.current}/{self.total} ({percent:.1f}%)", end="")
            
            def close(self):
                print()
        
        return SimpleProgressBar(total, desc)
