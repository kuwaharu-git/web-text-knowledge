#!/usr/bin/env python3
"""
Difyナレッジファイル生成システム
指定されたWebサイトURLから自動的にテキストコンテンツを収集し、
Difyのナレッジベースに最適化されたファイルを生成します。
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional

from src.config.settings import Settings
from src.scraper.web_scraper import WebScraper
from src.parser.text_parser import TextParser
from src.dify_generator.file_generator import DifyFileGenerator
from src.utils.logger import setup_logger


def parse_arguments() -> argparse.Namespace:
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(
        description="Difyナレッジファイル生成システム",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # 必須パラメータ
    parser.add_argument(
        "--url", 
        required=True, 
        help="開始URL"
    )
    parser.add_argument(
        "--depth", 
        type=int, 
        required=True, 
        metavar="N",
        help="クロール深度（1-10）"
    )
    parser.add_argument(
        "--max-pages", 
        type=int, 
        required=True, 
        metavar="N",
        help="最大取得ページ数（1-1000）"
    )
    
    # オプションパラメータ
    parser.add_argument(
        "--output-format", 
        choices=["txt", "md", "docx", "all"], 
        default="all",
        help="出力形式（txt/md/docx/all）"
    )
    parser.add_argument(
        "--output-dir", 
        type=Path, 
        default=Path("output"),
        help="出力ディレクトリ"
    )
    parser.add_argument(
        "--config", 
        type=Path,
        help="設定ファイルパス"
    )
    parser.add_argument(
        "--delay", 
        type=float, 
        default=1.0,
        help="リクエスト間隔（秒）"
    )
    parser.add_argument(
        "--concurrent", 
        type=int, 
        default=3,
        help="同時リクエスト数"
    )
    parser.add_argument(
        "--max-file-size", 
        type=int, 
        default=15,
        help="ファイル最大サイズ（MB）"
    )
    parser.add_argument(
        "--chunk-size", 
        type=int, 
        default=2000,
        help="チャンクサイズ（文字数）"
    )
    parser.add_argument(
        "--verbose", 
        "-v", 
        action="store_true",
        help="詳細ログ出力"
    )
    
    return parser.parse_args()


async def main():
    """メイン処理"""
    args = parse_arguments()
    
    # ログ設定
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger(log_level)
    
    try:
        # 引数の検証
        if not (1 <= args.depth <= 10):
            parser.error("--depth は 1 から 10 の間で指定してください")
        
        if not (1 <= args.max_pages <= 1000):
            parser.error("--max-pages は 1 から 1000 の間で指定してください")
        
        # 設定読み込み
        settings = Settings(
            config_path=args.config,
            url=args.url,
            depth=args.depth,
            max_pages=args.max_pages,
            output_format=args.output_format,
            output_dir=args.output_dir,
            delay=args.delay,
            concurrent=args.concurrent,
            max_file_size=args.max_file_size,
            chunk_size=args.chunk_size
        )
        
        logger.info(f"Difyナレッジファイル生成システム開始")
        logger.info(f"対象URL: {settings.url}")
        logger.info(f"クロール深度: {settings.depth}")
        logger.info(f"最大ページ数: {settings.max_pages}")
        
        # 出力ディレクトリ作成
        settings.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Webスクレイピング実行
        scraper = WebScraper(settings)
        scraped_data = await scraper.scrape()
        
        if not scraped_data:
            logger.error("スクレイピングでデータを取得できませんでした")
            return 1
        
        logger.info(f"スクレイピング完了: {len(scraped_data)} ページ取得")
        
        # テキスト解析
        parser = TextParser(settings)
        parsed_data = parser.parse(scraped_data)
        
        logger.info(f"テキスト解析完了: {len(parsed_data)} ページ処理")
        
        # Difyファイル生成
        generator = DifyFileGenerator(settings)
        generated_files = generator.generate(parsed_data)
        
        logger.info(f"ファイル生成完了:")
        for file_path in generated_files:
            logger.info(f"  - {file_path}")
        
        logger.info("処理が正常に完了しました")
        return 0
        
    except KeyboardInterrupt:
        logger.info("処理が中断されました")
        return 1
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        if args.verbose:
            logger.exception("詳細エラー情報:")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
