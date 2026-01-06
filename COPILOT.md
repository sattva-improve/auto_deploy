# GitHub Copilot / AI アシスタント向け指示書

> **ドキュメントバージョン**: 1.0.0  
> **最終更新日**: 2026-01-06  
> **ステータス**: Active

---

## プロジェクト概要

このリポジトリは、AI駆動開発によるRESTful API自動生成システムです。
ユーザーからの自然言語入力を元に、ウォーターフォール開発のベストプラクティスに従い、
要件定義からOpenAPI仕様書の生成、さらにAWSへのデプロイまでを自動化します。

---

## よく使うコマンド

### 開発環境

```bash
# Python仮想環境の作成
python -m venv venv
source venv/bin/activate

# 依存関係のインストール
pip install -r backend/requirements.txt

# OpenAPI仕様書のバリデーション
npx @redocly/cli lint specs/openapi/projects/*/openapi.yaml
```

### Git操作

```bash
# ブランチ命名規則
git checkout -b feature/{機能名}
git checkout -b fix/{修正内容}
git checkout -b docs/{ドキュメント内容}

# コミットメッセージ形式
# type(scope): description
# 例: feat(api): add user authentication endpoint
# 例: docs(readme): update installation guide
```

---

## コードスタイル

### Python

- **スタイルガイド**: PEP 8
- **フォーマッター**: Black（最大行長: 88文字）
- **インデント**: スペース4つ
- **命名規則**:
  - クラス: `PascalCase`
  - 関数/変数: `snake_case`
  - 定数: `UPPER_SNAKE_CASE`
- **型ヒント**: 積極的に使用すること

### YAML (OpenAPI)

- **インデント**: スペース2つ
- **文字列**: 必要な場合のみクォート使用
- **コメント**: セクションの先頭に概要を記載

### Markdown

- **見出し**: 階層を正しく使用（#, ##, ###）
- **コードブロック**: 言語を必ず指定
- **図表**: Mermaid記法を使用

---

## ワークフロー

### 新規プロジェクト作成

1. ユーザーからの要求を受け取る
2. Phase 1: 要件定義書を生成 (`requirements/projects/{project}/`)
3. Phase 2: 基本設計書を生成 (`design/basic/projects/{project}/`)
4. Phase 3: 詳細設計書を生成 (`design/detailed/projects/{project}/`)
5. Phase 4: OpenAPI仕様書を生成 (`specs/openapi/projects/{project}/`)

### 各フェーズで使用するテンプレート

| フェーズ | テンプレート | プロンプト |
|---------|-------------|-----------|
| 要件定義 | `requirements/_template.md` | `ai/prompts/requirements.md` |
| 基本設計 | `design/basic/_template.md` | `ai/prompts/basic_design.md` |
| 詳細設計 | `design/detailed/_template.md` | `ai/prompts/detailed_design.md` |
| OpenAPI | `specs/openapi/_template.yaml` | `ai/prompts/openapi_gen.md` |

---

## ファイル構造

```
auto_deploy/
├── ai/
│   ├── instructions/        # AI指示ファイル
│   │   └── workflow.md      # ワークフロー定義
│   └── prompts/             # プロンプトテンプレート
├── design/
│   ├── basic/projects/      # 基本設計書
│   └── detailed/projects/   # 詳細設計書
├── docs/
│   ├── guidelines/          # 開発ガイドライン
│   └── guides/              # 実装・デプロイガイド
├── requirements/projects/   # 要件定義書
├── specs/openapi/projects/  # OpenAPI仕様書
├── backend/                 # バックエンド実装
└── aws/                     # AWS関連リソース
```

---

## 品質チェックリスト

### 要件定義

- [ ] 機能要件が明確に定義されている
- [ ] 非機能要件が定義されている
- [ ] ユースケースが網羅されている
- [ ] 用語が統一されている

### 基本設計

- [ ] RESTful設計原則に準拠している
- [ ] リソースが適切に設計されている
- [ ] HTTPメソッドが適切に選択されている

### 詳細設計

- [ ] 全エンドポイントが詳細定義されている
- [ ] スキーマが完全に定義されている
- [ ] バリデーションルールが定義されている

### OpenAPI

- [ ] OpenAPI 3.0/3.1 仕様に準拠している
- [ ] バリデーションエラーがない
- [ ] セキュリティ定義が含まれている

---

## 重要な注意事項

### IMPORTANT

- 各フェーズは必ず順番に実行すること
- テンプレートの形式を厳守すること
- 機密情報（APIキー、認証情報等）をコミットしないこと
- プロジェクト固有のファイルは必ず `projects/` ディレクトリ配下に配置

### 禁止事項

- 本番環境の認証情報のハードコーディング
- テストなしでの本番デプロイ
- 既存のテンプレートファイルの直接編集

---

## 関連ドキュメント

- [システム概要](docs/overview.md)
- [開発ガイドライン](docs/guidelines/index.md)
- [実装・デプロイガイド](docs/guides/index.md)
- [AI駆動開発ワークフロー](ai/instructions/workflow.md)
- [AI駆動開発ベストプラクティス](docs/guides/ai-driven-development.md)
