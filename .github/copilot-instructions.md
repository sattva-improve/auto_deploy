# GitHub Copilot カスタム指示

## プロジェクト概要

このリポジトリは、AI駆動開発によるRESTful API自動生成システムです。
ユーザーからの自然言語入力を元に、ウォーターフォール開発のベストプラクティスに従い、
要件定義からOpenAPI仕様書の生成、さらにAWSへのデプロイまでを自動化します。

## コーディング規約

### Python
- PEP 8 準拠
- Black フォーマッター使用（最大行長: 88文字）
- 型ヒントを必ず使用
- docstring は Google スタイル

### 命名規則
- クラス: PascalCase
- 関数/変数: snake_case
- 定数: UPPER_SNAKE_CASE

### YAML (OpenAPI)
- インデント: スペース2つ
- OpenAPI 3.1 仕様に準拠

### Markdown
- 見出しの階層を正しく使用
- コードブロックには言語を指定
- 図表は Mermaid 記法を使用

## ワークフロー

新規API開発時は以下の順序で進める:
1. 要件定義 → requirements/projects/{project}/
2. 基本設計 → design/basic/projects/{project}/
3. 詳細設計 → design/detailed/projects/{project}/
4. OpenAPI生成 → specs/openapi/projects/{project}/

## 禁止事項

- 認証情報のハードコーディング
- テンプレートファイルの直接編集
- テストなしでの本番デプロイ
- フェーズのスキップ

## 参照ドキュメント

- ワークフロー: ai/instructions/workflow.md
- テンプレート: requirements/_template.md, design/**/_template.md
- プロンプト: ai/prompts/
