# 共通 Cursor Rules

OS ユーザー単位のマシンローカルルール（`~/.cursor/rules/`、Windows は `%USERPROFILE%\.cursor\rules\`）。  
Cursor アカウントには紐づかない。モデルへの指示は各 `.mdc` の本文のみ。この README は人間向けの来歴。

## 適用方針

| ファイル | 適用 |
|---|---|
| `change-discipline.mdc` | Always（ゲート） |
| 他 10 本 | Intelligent（description で判断） |

`.md` はこのフォルダではルールとして読まれない。来歴は README に置く。

## 来歴（採用 / 不採用）

| ファイル | 出典 | 採用した具体策 | 採用しなかったもの |
|---|---|---|---|
| `change-discipline` | Google Eng Practices / Amazon | 1変更=1意図、最小差分、完了条件を先に決める、推測で埋めない、失敗を黙殺しないゲート、秘密情報・最小権限・依存確認 | Working Backwards の PR/FAQ・6ページャー等の文書プロセス、厳密な行数/CLサイズ制限、正式なオーナー承認フロー |
| `architecture` | Amazon / Google / Meta / A Philosophy of Software Design | 依存の一方通行、公開面先行、失敗・運用を設計に含める、過剰抽象禁止、Decision test（削除＞既存＞薄いアダプタ＞新抽象）、Deep Modules（インターフェースの単純さに対して隠す知識の大きさで評価）、Shallow／中継層の禁止 | サービス分割の強制、イベント駆動の既定化、DIコンテナ前提、Meta 流の「合成可能性」を抽象スローガンとして要求すること、モジュールの大きさそのものを深さの代替指標にすること |
| `robustness` | Google / Amazon / A Philosophy of Software Design | 境界検証、サイレント失敗禁止、cause+文脈、冪等、I/O・並行のチェックリスト、エラーを定義から消す検討を例外処理の前に置く | 全エラーの型付き Result 強制、サーキットブレーカ必須化、組織的インシデントプロセス |
| `performance` | Meta / Google / Amazon | 計測先行、ホットパス意識、N+1等の除去、キャッシュに寿命と無効化、正しさ→明瞭さ→計測後最適化 | 金銭コスト/キャパシティ計画の必須化、常時プロファイリング、特定ランタイムの最適化技法の押し込み |
| `maintainability` | Google / Amazon / A Philosophy of Software Design / Clean Code（軽く採用） | 命名、局所性、単一の変更理由、なぜコメント、ネスト平坦化、公開面の契約・不変条件コメント必須、長さで割らない抽出基準（テストは testing ルールへ分離） | CODEOWNERS 的な「誰が所有するか」の必須記述、強制的なレイヤ数、カバレッジ％目標、Clean Code の関数行数基準・小ささの絶対視、コメント全面否定 |
| `ui-ux` | Meta / Google | UI/UXを目的側の上位、操作フィードバック、状態表示、体感性能、空/エラー状態、最低限 a11y、一貫した操作言語 | デザインシステム強制、特定コンポーネントライブラリ、アニメーション必須、WCAG の全項目監査 |
| `product-spine` | Amazon の逆算思想を薄い形に / 現代の JTBD | ジョブ一文、非目標、ロール命名、未知は既定動作（多くは無操作）、SPEC↔実装の差分を隠さない | Working Backwards 文書一式、正式なプレスリリース／FAQ、OKR プロセス |
| `ssot-contracts` | Amazon のインターフェース先行 / Google の単一情報源 | 変わりやすい値はデータ、文書は正本にしない、段の明示契約、最新1件・状態の所在、運行の真実は一つ | 特定の IPC（gRPC等）強制、スキーマレジストリ、ホットリロード必須、汎用ルール言語 |
| `operator-ux` | SRE の可観測性を OX に落とした形 / 良い CLI の慣習 | 状態・今の仕事・停止理由、起動経路の一本化、片肺運転禁止、証拠で成功を示す、待機と詰まりの区別、停止完了の確認、フォアグラウンド実行のリアルタイム進捗表示 | フルダッシュボード必須、OpenTelemetry 強制、特定ログ基盤、GUI コントロールプレーン必須 |
| `testing` | Google / 現代の振る舞い中心テスト思想（学派名では採用しない） | 公開面の振る舞い検証、配分は複雑さとリスクの所在、実サンプル・実障害の回帰資産化、再現テスト先行、決定的な実行、カバレッジは目標にしない | TDD の全面強制、Pact 等の契約テストツール、Mutation Testing の必須化、Testing Trophy／Pyramid の名前での配分指定、プロダクトの大きさによる戦略切替 |
| `git` | Trunk-Based Development / Conventional Commits | main のみ常駐、短命ブランチ、1コミット1意図、メッセージ規約（英語既定、type／scope は常に英語）、コミットはユーザー指示時のみ、フックは早期フィードバックでゲートの正本は CI、秘密情報スキャンを pre-commit に含める、body は設計判断・ファイルの追加/分離/廃止・複数ファイル変更では必須（省略は意図と理由が自明な小変更のみ） | gitflow（develop 常駐、release／hotfix ブランチ）、フックを唯一のゲートにすること、`--no-verify` の常用、言語のプロジェクト横断の固定（プロジェクト側で日本語へ上書き可能） |

## ズレ防止の原則

- モデルは **`.mdc` 本文に書いた指示だけ** に従う
- 出典名や社名から手法を補完しない（とくに Working Backwards 文書、所有プロセス、コスト会計）
- ルールを足す・削るときは、この表の「採用した具体策 / 採用しなかったもの」を先に更新する
- `ui-ux` は画面・フロント、`operator-ux` は daemon/CLI/運用の制御面。混ぜない
