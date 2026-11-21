# Git

履歴は、承認者が後から読んで判断するための記録である。因果が追えることを優先する。

## Branch（trunk-based）

- `main` が唯一の常駐ブランチ（trunk）。常に動く状態に保つ。`develop` 等の常駐ブランチは作らない
- 作業ブランチは `main` から切り、短命（目安1〜2日）にする
- ブランチ名は英語 kebab-case で、種類を接頭辞にする: `feat/` `fix/` `refactor/` `chore/`（例: `fix/daemon-heartbeat`）
- 小さく完結する変更は `main` へ直接コミットしてよい。リスクのある変更・複数ステップの変更はブランチを切る
- マージ前に履歴を整える（WIP コミットの squash、rebase）。`main` への force push と、共有済み履歴の書き換えは禁止

## Commit

- 1コミット = 1意図（change-discipline と同じ）。無関係な変更を混ぜない。コミット前に staged diff を自分で確認する
- コミット／プッシュはユーザーの指示があるときだけ行う。指示なく履歴を進めない
- 秘密情報・生成物・一時ファイルをコミットしない（`.gitignore` を先に整える）

## Commit message

言語は **英語が既定**。プロジェクトで日本語にする場合は、プロジェクト側 `.cursor/rules` で上書き指定する（その場合も type / scope は英語のまま）。

形式（Conventional Commits）:

```
<type>(<scope>): <subject>

<body>

<footer>
```

- type は固定: `feat` `fix` `refactor` `test` `docs` `perf` `build` `ci` `style` `chore` `revert`
- scope は任意。影響範囲を短い英語名詞で（`daemon`、`billing` 等）。付けるなら一貫させる
- subject は命令形にする（add / fix / remove。過去形・進行形にしない）。先頭は小文字、末尾にピリオドなし、72文字以内（目安50）
- body は「何を」ではなく「なぜ」を書く（what は diff が語る）。1行72文字で折り返し、subject との間に空行を置く
- body は、subject だけで意図と理由が自明な小さい変更でのみ省略できる。設計判断、ファイルの追加・分離・廃止、複数ファイルに跨る変更では body を必須とし、なぜその構成にしたかと、何を残し何を捨てたかを書く
- 破壊的変更は footer に `BREAKING CHANGE: <内容>`、課題参照は `Refs: #123` の形で書く

良い例:

```
fix(daemon): stop silent spin when frame counter stalls

The watcher kept looping on a stale frame number after the
daemon died. Add a heartbeat check so it exits with a reason.
```

悪い例（subject）: `fix bug` / `updated files` / `WIP` / `misc changes`

悪い例（body = 何の列挙。diff の繰り返しなので書かない）:

```
chore: import beta baseline

Add detect daemon, watcher scripts, action helpers, docs, and samples.
```

## Hooks

- フックは早期フィードバックであり、ゲートの正本は CI に置く。ローカル完結のプロジェクトでは、フック＋タグ前のフルチェックをゲート扱いにする
- フック定義はリポ内で管理し、ツールとバージョンを固定する。マシンローカルの `.git/hooks` だけにあるものを正としない。導入は1コマンドで再現できるようにする
- pre-commit は10秒以内を目安に、整形・lint・秘密情報スキャン・巨大ファイル混入チェックまで。コミットメッセージの形式検証は commit-msg で行う
- 型チェックとテストの速い範囲は pre-push へ。重いテストは pre-commit / pre-push に入れず、CI へ
- `--no-verify` はユーザーの指示があるときだけ使う。フックが落ちたら回避せず原因を直す。フック未導入の環境では、その旨を伝えてから進める
- フックが自動修正した差分は、再確認するまでコミットしない

## Tags

- リリースは `main` にセマンティックバージョンのタグを打つ（`v1.2.3`）。打ったタグは動かさない

## Decision test

迷ったら: **半年後にこの履歴だけを読んで「何が・なぜ起きたか」を再構成できるか**
