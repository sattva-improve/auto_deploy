# フェーズ実行コマンド

Phase $ARGUMENTS を実行してください。

## フェーズ別処理

### Phase 1: 要件定義
- 入力: ユーザーからの自然言語要求
- テンプレート: `requirements/_template.md`
- プロンプト: `ai/prompts/requirements.md`
- 出力: `requirements/projects/{project}/requirements.md`

### Phase 2: 基本設計
- 入力: 承認済み要件定義書
- テンプレート: `design/basic/_template.md`
- プロンプト: `ai/prompts/basic_design.md`
- 出力: `design/basic/projects/{project}/basic_design.md`

### Phase 3: 詳細設計
- 入力: 承認済み基本設計書
- テンプレート: `design/detailed/_template.md`
- プロンプト: `ai/prompts/detailed_design.md`
- 出力: `design/detailed/projects/{project}/detailed_design.md`

### Phase 4: OpenAPI生成
- 入力: 承認済み詳細設計書
- テンプレート: `specs/openapi/_template.yaml`
- プロンプト: `ai/prompts/openapi_gen.md`
- 出力: `specs/openapi/projects/{project}/openapi.yaml`

## 実行前チェック

- [ ] 前フェーズが完了・承認されているか確認
- [ ] 対象プロジェクトのディレクトリが存在するか確認
- [ ] 必要なテンプレートが利用可能か確認

## 品質チェック

`ai/instructions/workflow.md` の品質チェックリストを参照して、
生成物が基準を満たしていることを確認すること。

## 注意事項

- 各フェーズは必ず順番に実行すること
- フェーズをスキップしないこと
- レビュー・承認なしに次フェーズに進まないこと
