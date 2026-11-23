# scripts ディレクトリ仕様

この README は scripts ディレクトリの仕様書である。

`rules.ja/` の正本を処理するスクリプトを置く。`build-rules` は実装済み。`translate-rules` は未実装（設計のみ）。

| スクリプト | 仕事 |
|---|---|
| `build-rules` | 正本から配布物（Cursor 版／Claude 版）を決定的に生成する |
| `translate-rules` | 正本から公開用英語版 `rules.en/` を生成する |

## build-rules

目的：`rules.ja/<名前>/` の `body.md` と `meta.json` から、`.cursor/rules/<名前>.mdc` と `.claude/rules/<名前>.md` を生成する。

入出力の契約：

- 入力は正本のみ。出力は入力の純粋な関数であり、同じ入力からは常に同じバイト列が出る（冪等）
- 生成物には目印のヘッダを付けない。正本とのズレはファイル内の文言ではなく `--check` で検出する
- `--check` は書き込まず、生成物と正本の一致だけを検査し、ズレたファイル名を示して異常終了する
- 報告も契約の一部である。通常実行は、何をしたかを標準出力に出す：要約行（`wrote <件数> files from rules.ja under <ルート>`）に続けて、書き込んだ全ファイルのパスを出す。`--check` の成功時は `checked <件数> files from rules.ja under <ルート>; all match; wrote nothing` に続けて、検査した全パスを出す。無言の成功は欠陥である：何も起きなかったことと区別できない
- `--check` の失敗時は、標準エラーに要約行、問題ごとの行、次のアクション（`run without --check to write them.`）を出す。ズレたファイルと欠けたファイルは個別に名前を出す（`differs: <パス>`、`missing: <パス>`）。出力ディレクトリ自体が無い・空の場合は、配下のファイルを列挙せず、ディレクトリを一度だけ名指す（`missing: <ディレクトリ>`、`empty: <ディレクトリ>`）。問題は、オペレータが操作する単位で報告する

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

実装：Python 3、標準ライブラリのみ、単一ファイル（拡張子なし）。JSON は標準の `json` で読み、frontmatter の値はクォートなしの plain scalar で出力し、キー順は description、globs、alwaysApply として現行の .mdc に合わせる。Mac／Windows の両方で動くことを前提とする。

テスト：テストファーストで作る。フィクスチャ3ケース（alwaysApply／globs／description のみ）のゴールデン比較、実ルールの凍結スナップショットによる回帰（入力と期待出力を 2026-11-21 に `scripts/tests/fixtures/real/` へ凍結したもの。オラクルはスナップショットであり、現行の生成物ではない）、出力報告の検証（実行が何を書いた／検査したかを言うこと）、`--check` のケース（一致、手編集、ファイル欠落、出力ディレクトリの欠落・空）、異常系（欠落・不正・未知キー、および正常と異常の混在で出力が書かれないこと）。

完了条件：

1. 実ルールの凍結スナップショットに対して、生成物が期待出力とバイト単位で一致する
2. 2回連続実行で2回目の差分がゼロ
3. `--check` が、正本と一致する状態で正常終了し、生成物の手編集・ファイル欠落・出力ディレクトリの欠落／空で異常終了する。名前はズレたファイルを示し、ディレクトリ全体が問題のときはディレクトリだけを示す
4. 不正な入力で異常終了し、出力ファイルを一切書かない
5. globs を持つフィクスチャで、Claude 版に `paths` frontmatterが正しく出る

## translate-rules

目的：`rules.ja/`（日本語正本）から公開用英語版 `rules.en/` を生成する。このリポジトリは一般公開するため、リポジトリを読む人向けに英語版を用意する。正本は承認者が直接検証できる日本語に固定する。エージェントが従うのは、build-rules が正本から生成する日本語の配布物である。英語版は生成物とする。

契約：

- 対象は `body.md` と `meta.json` の `description`。`basis.md`（根拠）は承認者が読む文書であり対象外
- 出力は `rules.en/<名前>/body.md` と `rules.en/<名前>/meta.json` のみ。配布は日本語正本から build-rules が行う
- `description` を訳す。`cursor` 名前空間は同じ JSON をコピーする。既に英語の見出しと識別子はそのまま残す
- 翻訳器は Claude Code のコマンド `claude -p` である。スクリプトは日本語の正本と、そのルールが `rules.en/` に既にあるときは前回の英語を渡し、コマンドが標準出力に出した訳文を書く。認証は、そのマシンに既にある Claude Code のログインである
- 正本を更新したときに実行する。対象は `git diff` で `rules.ja/` の変更ファイルから特定し、ルール名の明示指定もできる
- 日本語が変わっていない箇所は、前回の英語を維持する。訳し直すのは、変わった日本語だけである。レビューは `rules.en/` の対象ファイルの差分である
- `claude` が無い、またはコマンドが失敗したときは、その実行は何も書かず、`rules.en/` を実行前のままにする。異常終了し、ルール名・原因・次のアクション（`claude -p` を成功させてから再実行する）を出す

非目標：Google Translate、DeepL、API キーを要する翻訳器。

## この仕様書の持ち方

書くのは「なぜ」と「契約」。振る舞いの細部はテストが、実装方法はコードが正本である。
