# Difyナレッジファイル生成システム

Webサイトから自動的にテキストコンテンツを収集し、Difyのナレッジベースに最適化されたファイル（.txt、.md、.docx形式）を生成するシステムです。

## 特徴

- 🌐 **Webスクレイピング**: 指定されたURLから関連ページを自動取得
- 📝 **Dify最適化**: Difyのナレッジベースに最適化されたファイル形式で出力
- 🎯 **複数形式対応**: テキスト（.txt）、Markdown（.md）、Word文書（.docx）形式で出力
- ⚡ **高性能**: 並列処理による高速スクレイピング
- 🛡️ **安全性**: robots.txt遵守、リクエスト制限による礼儀正しいクロール
- 📊 **詳細レポート**: スクレイピング結果の統計情報とエラーレポート

## インストール

### 前提条件
- Python 3.8以上
- pip

### インストール手順

1. リポジトリをクローン
```bash
git clone <repository-url>
cd web-text-knowledge
```

2. 仮想環境を作成（推奨）
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 依存関係をインストール
```bash
pip install -r requirements.txt
```

## 使用方法

### 基本的な使用方法

```bash
python main.py --url https://example.com --depth 2 --max-pages 50
```

### パラメータ説明

#### 必須パラメータ
- `--url`: 開始URL
- `--depth`: クロール深度（1-10）
- `--max-pages`: 最大取得ページ数（1-1000）

#### オプションパラメータ
- `--output-format`: 出力形式（txt/md/docx/all）デフォルト: all
- `--output-dir`: 出力ディレクトリ デフォルト: output
- `--config`: 設定ファイルパス
- `--delay`: リクエスト間隔（秒）デフォルト: 1.0
- `--concurrent`: 同時リクエスト数 デフォルト: 3
- `--max-file-size`: ファイル最大サイズ（MB）デフォルト: 15
- `--chunk-size`: チャンクサイズ（文字数）デフォルト: 2000
- `--verbose, -v`: 詳細ログ出力

### 使用例

#### 基本的なスクレイピング
```bash
python main.py --url https://docs.example.com --depth 3 --max-pages 100
```

#### Markdown形式のみで出力
```bash
python main.py --url https://blog.example.com --depth 2 --max-pages 50 --output-format md
```

#### 詳細ログ付きで実行
```bash
python main.py --url https://example.com --depth 1 --max-pages 10 --verbose
```

#### カスタム設定で実行
```bash
python main.py --url https://example.com --depth 2 --max-pages 100 --config config/custom.json --delay 2.0 --concurrent 5
```

## 設定ファイル

`config.json`で詳細な設定をカスタマイズできます：

```json
{
  "scraping": {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "timeout": 30,
    "retry_count": 3,
    "exclude_patterns": [
      "/admin/",
      "/login/",
      "*.pdf",
      "*.jpg",
      "*.png"
    ]
  },
  "parsing": {
    "remove_elements": ["nav", "footer", "aside", ".advertisement"],
    "min_text_length": 100,
    "language": "ja"
  },
  "output": {
    "filename_template": "{site_name}_{timestamp}",
    "split_large_files": true,
    "include_metadata": true
  }
}
```

## 出力形式

### テキストファイル（.txt）
```
サイト名: https://example.com
取得日時: 2024-06-24 10:30:00
総ページ数: 85
=================================

【ページタイトル1】
URL: https://example.com/page1
取得日時: 2024-06-24 10:30:15

本文内容...
```

### Markdown形式（.md）
```markdown
# サイト名: https://example.com

**取得日時**: 2024-06-24 10:30:00  
**総ページ数**: 85

---

## ページタイトル1

**URL**: https://example.com/page1  
**取得日時**: 2024-06-24 10:30:15

本文内容...
```

### Word文書形式（.docx）
- 構造化された見出し
- 適切なフォーマット（太字、リンク等）
- 目次の自動生成
- ページ区切りの適切な配置

## Difyとの連携

生成されたファイルをDifyのナレッジベースに追加する方法：

1. Difyのダッシュボードにログイン
2. 「ナレッジベース」セクションに移動
3. 「新しいナレッジベース」を作成または既存のものを選択
4. 「ファイルをアップロード」をクリック
5. 生成された`.txt`、`.md`、または`.docx`ファイルを選択してアップロード

### Dify用最適化機能
- ファイルサイズ制限（15MB以下）の自動遵守
- 適切なチャンク分割によるベクトル化の最適化
- 検索精度向上のためのキーワード埋め込み
- Difyでの読み込み品質検証

## トラブルシューティング

### よくある問題

#### スクレイピングが失敗する
- robots.txtでアクセスが禁止されている可能性があります
- `--delay`を大きくしてリクエスト間隔を調整してください
- サイトの利用規約を確認してください

#### メモリ不足エラー
- `--max-pages`を小さくしてください
- `--concurrent`を小さくして同時処理数を減らしてください

#### ファイルが大きすぎる
- `--max-file-size`を調整してください
- `--chunk-size`を小さくしてファイル分割を促してください

## 開発

### 開発環境のセットアップ
```bash
# 開発用依存関係をインストール
pip install -r requirements-dev.txt

# テスト実行
pytest

# コード品質チェック
flake8 src/
black src/
```

### プロジェクト構造
```
web-text-knowledge/
├── main.py                    # メインプログラム
├── requirements.txt          # 依存関係
├── README.md                # このファイル
├── src/
│   ├── config/              # 設定管理
│   ├── scraper/             # スクレイピング機能
│   ├── parser/              # テキスト解析
│   ├── dify_generator/      # Difyファイル生成
│   ├── file_formatter/      # ファイル形式変換
│   └── utils/               # ユーティリティ
└── tests/                   # テストコード
```

## ライセンス

MIT License

## 貢献

バグ報告や機能要望は、GitHubのIssueでお願いします。

## 変更履歴

### v2.0.0 (2024-06-24)
- Difyナレッジベース対応への全面改訂
- 複数ファイル形式対応（.txt、.md、.docx）
- 非同期処理による性能向上
- Dify最適化機能の追加
webサイトのURLからテキストナレッジを生成

# 開発経緯
Difyで学校のwebサイトからチャットbotを作成したかったのですが、フリープランだと複数ページをまとめてナレッジの作成ができなかったため代替として開発をはじまました。
できればすぐに使いたかったため、要件定義から開発からテストまですべてGitHub Copilotに任せました。一応、私の通っている学校のwebサイトではうまくナレッジのためのファイルを作成することができ、チャットボットも作成できました。