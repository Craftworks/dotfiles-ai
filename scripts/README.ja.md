# scripts ディレクトリ仕様

この README は scripts ディレクトリの仕様書である。

`rules/` の正本を処理するスクリプトを置く。現在はどちらも未実装（設計のみ）。

| スクリプト | 仕事 |
|---|---|
| `build-rules` | 正本から配布物（Cursor 版／Claude 版）を決定的に生成する |
| `translate-rules` | 正本から公開用英語版 `rules.en/` を生成する |

## build-rules

目的：`rules/<名前>/` の `body.md` と `meta.json` から、`.cursor/rules/<名前>.mdc` と `.claude/rules/<名前>.md` を生成する。

入出力の契約：

- 入力は正本のみ。出力は入力の純粋な関数であり、同じ入力からは常に同じバイト列が出る（冪等）
- 生成物には目印のヘッダを付けない。正本とのズレはファイル内の文言ではなく `--check` で検出する
- `--check` は書き込まず、生成物と正本の一致だけを検査し、ズレたファイル名を示して異常終了する

非目標：翻訳、ホームへの配置、git 操作、監視モード、増分処理。

変換表（正本の `meta.json` は `description` と `cursor` 名前空間を持つ）：

| meta.json | Cursor 版（.mdc） | Claude 版（.md） |
|---|---|---|
| `cursor.alwaysApply: true` | frontmatterに `alwaysApply: true` | frontmatterなし |
| `cursor.globs` あり | frontmatterに `globs` | frontmatterに `paths` として出力 |
| それ以外（description のみ） | frontmatterに description のみ | frontmatterなし |

注：Claude Code のルール読み込みはfrontmatterの `paths` のみを見て、`alwaysApply` は読まない。`~/.claude/rules/` に置かれたファイルは常駐ロードされる。auto（description のみ）のルールをホーム側でどう扱うかは install 設計の未決事項（実測による確認待ち）。

検証とエラー：

- 全ルールの検証（meta.json の必須キー・型・未知キー、body.md の存在）を終えてから書き始める。不正が1件でもあれば異常終了し、出力ファイルは書かれない
- エラー表示はルール名・原因・次のアクションの形。終了コードで成否を返す

実装：Python 3、標準ライブラリのみ、単一ファイル（拡張子なし）。JSON は標準の `json` で読み、frontmatterの文字列は JSON 式クォートで YAML のダブルクォートスカラとして出力する。Mac／Windows の両方で動くことを前提とする。

テスト：テストファーストで作る。フィクスチャ3ケース（alwaysApply／globs／description のみ）のゴールデン比較、実物11ルールの回帰（生成結果が現行の `.mdc` とバイト単位で一致すること）、異常系（欠落・不正・未知キーで出力が書かれないこと）。

完了条件：

1. 実リポジトリで実行すると、生成された `.cursor/rules/*.mdc` が現行の実ファイルとバイト単位で一致する
2. 2回連続実行で2回目の差分がゼロ
3. `--check` が、正本と一致する状態で正常終了し、生成物を手で書き換えると該当ファイル名を示して異常終了する
4. 不正な入力で異常終了し、出力ファイルを一切書かない
5. globs を持つフィクスチャで、Claude 版に `paths` frontmatterが正しく出る

## translate-rules

目的：`rules/`（日本語正本）から公開用英語版 `rules.en/` を生成する。このリポジトリは一般公開するため英語版を用意するが、正本は承認者が直接検証できる日本語に固定し、英語版は生成物とする。

- 対象は `body.md` と `meta.json` の `description`。`basis.md`（根拠）は承認者が読む文書であり対象外
- 出力は `rules.en/` のみ。配布は日本語正本から build-rules が行う
- 正本を更新したときに実行する。対象は `git diff` で `rules/` の変更ファイルから特定し、ルール名の明示指定もできる
- 翻訳は非決定的であり、変更ファイルの中では未変更段落の訳文も揺れうる。レビューは変更ファイル単位で行う

## この仕様書の持ち方

書くのは「なぜ」と「契約」。振る舞いの細部はテストが、実装方法はコードが正本である。
