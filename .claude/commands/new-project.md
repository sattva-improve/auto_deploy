# 新規プロジェクト作成コマンド

プロジェクト「$ARGUMENTS」を新規作成してください。

## 手順

1. プロジェクト名を確認し、ディレクトリ構造を準備
2. ユーザーから追加の要件をヒアリング（必要に応じて質問）
3. Phase 1: 要件定義書を生成
   - テンプレート: `requirements/_template.md`
   - プロンプト: `ai/prompts/requirements.md`
   - 出力: `requirements/projects/$ARGUMENTS/requirements.md`
4. ユーザーレビューを待機
5. Phase 2以降は明示的な指示を待つ

## 必須の確認事項

- システムの主なユーザーは誰か？
- 想定される同時利用者数
- 認証方式の希望
- 既存システムとの連携要否
- 優先度の高い機能

## 生成するファイル

```
requirements/projects/$ARGUMENTS/
└── requirements.md
```

## 注意事項

- `ai/instructions/workflow.md` のワークフローに従うこと
- 各フェーズは順番に実行すること（Phase 1から開始）
- テンプレートの形式を厳守すること
