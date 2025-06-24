# プロジェクト構造

```
web-text-knowledge/
├── README.md                          # プロジェクト概要・使用方法
├── DIFY_INTEGRATION.md               # Dify連携ガイド
├── requirements_document.md          # 要件定義書
├── main.py                          # メインプログラム
├── requirements.txt                 # 本番用依存関係
├── requirements-dev.txt             # 開発用依存関係
├── .gitignore                       # Git除外設定
├── LICENSE                          # ライセンス
├── config/                          # 設定ファイル
│   └── default.json                 # デフォルト設定
├── src/                             # ソースコード
│   ├── __init__.py                  # パッケージ初期化
│   ├── config/                      # 設定管理モジュール
│   │   ├── __init__.py
│   │   └── settings.py              # 設定クラス
│   ├── scraper/                     # Webスクレイピングモジュール
│   │   ├── __init__.py
│   │   └── web_scraper.py           # スクレイパークラス
│   ├── parser/                      # テキスト解析モジュール
│   │   ├── __init__.py
│   │   └── text_parser.py           # テキスト解析クラス
│   ├── dify_generator/              # Difyファイル生成モジュール
│   │   ├── __init__.py
│   │   └── file_generator.py        # ファイル生成クラス
│   └── utils/                       # ユーティリティモジュール
│       ├── __init__.py
│       └── logger.py                # ログ・ユーティリティ
├── tests/                           # テストコード
│   ├── __init__.py
│   └── test_basic.py                # 基本テスト
├── output/                          # 生成ファイル出力先
│   ├── *.txt                        # テキストファイル
│   ├── *.md                         # Markdownファイル
│   └── *.docx                       # Word文書ファイル
└── .venv/                           # 仮想環境（自動生成）
```

## モジュール詳細

### メインプログラム

#### `main.py`
- アプリケーションのエントリーポイント
- コマンドライン引数の解析
- 各モジュールの統合実行
- エラーハンドリング

### 設定管理 (`src/config/`)

#### `settings.py`
- `Settings`: 設定管理クラス
- `ScrapingConfig`: スクレイピング設定
- `ParsingConfig`: テキスト解析設定
- `OutputConfig`: 出力設定
- `DifyConfig`: Dify固有設定

### Webスクレイピング (`src/scraper/`)

#### `web_scraper.py`
- `WebScraper`: 非同期スクレイピングクラス
- `WebPage`: ページデータクラス
- robots.txt遵守機能
- 並列処理による高速化
- エラーハンドリングとリトライ

### テキスト解析 (`src/parser/`)

#### `text_parser.py`
- `TextParser`: テキスト解析クラス
- `ParsedPage`: 解析済みページデータクラス
- HTMLクリーニング
- キーワード抽出
- トークン数計算

### Difyファイル生成 (`src/dify_generator/`)

#### `file_generator.py`
- `DifyFileGenerator`: ファイル生成クラス
- 複数形式対応（.txt、.md、.docx）
- ファイルサイズ制限対応
- メタデータ埋め込み
- 自動分割機能

### ユーティリティ (`src/utils/`)

#### `logger.py`
- ログ設定関数
- ファイルサイズフォーマット
- プログレスバー作成
- トークン数推定
- ファイル名サニタイズ

### テスト (`tests/`)

#### `test_basic.py`
- 基本機能のユニットテスト
- モック使用の統合テスト
- 設定テスト
- ファイル生成テスト

### 設定ファイル (`config/`)

#### `default.json`
- デフォルト設定値
- スクレイピング、解析、出力設定
- Dify最適化設定

## データフロー

1. **コマンドライン引数解析** → `main.py`
2. **設定読み込み** → `src/config/settings.py`
3. **Webスクレイピング** → `src/scraper/web_scraper.py`
4. **テキスト解析** → `src/parser/text_parser.py`
5. **ファイル生成** → `src/dify_generator/file_generator.py`
6. **出力** → `output/` ディレクトリ

## 拡張ポイント

### 新しい出力形式の追加
`src/dify_generator/file_generator.py` の `DifyFileGenerator` クラスに新しいメソッドを追加

### カスタムテキスト処理
`src/parser/text_parser.py` の `TextParser` クラスを拡張

### 新しいスクレイピング戦略
`src/scraper/web_scraper.py` の `WebScraper` クラスを継承

### 設定項目の追加
`src/config/settings.py` の各設定クラスに新しいフィールドを追加

## 依存関係

### 本番環境 (`requirements.txt`)
- `requests`: HTTP通信
- `beautifulsoup4`: HTML解析
- `python-docx`: Word文書生成
- `markdown`: Markdown処理
- `tiktoken`: トークン数計算
- `lxml`: XML/HTML パーサー
- `tqdm`: プログレスバー
- `aiohttp`: 非同期HTTP通信
- `pydantic`: データバリデーション
- `click`: コマンドラインインターフェース

### 開発環境 (`requirements-dev.txt`)
- `pytest`: テストフレームワーク
- `pytest-asyncio`: 非同期テスト
- `pytest-cov`: カバレッジ測定
- `black`: コードフォーマッター
- `flake8`: リンター
- `mypy`: 型チェッカー

## 設計原則

- **モジュラー設計**: 各機能を独立したモジュールに分離
- **非同期処理**: 高速なWebスクレイピングのためのasync/await
- **設定駆動**: 設定ファイルによる柔軟な動作制御
- **エラーハンドリング**: 堅牢なエラー処理とログ記録
- **テスタビリティ**: ユニットテストと統合テストの実装
- **Dify最適化**: Difyの制限と機能に特化した設計
