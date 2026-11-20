---
name: commit-command
description: >-
  Draft a git commit command for the currently staged files and, after the
  user's approval, run it. Use when the user says コミット, asks for a commit
  command (コミットコマンド), or asks to commit the staged changes.
---

# Commit command

ステージ済みの変更に対する `git commit` を1つ作る。いきなり実行はしない。プッシュはしない（承認後も含む）。

## 従うルール

- 形式・type・body の必須条件は、共通ルール `git.mdc` に従う
- 言語は、プロジェクト側に言語指定のルール（例: `.cursor/rules/commit-message-language.mdc`）があればそれを優先し、無ければ `git.mdc` の既定に従う

## 見る範囲

次を並行して実行する。

- `git status --short`
- `git diff --cached`
- `git log -8 --oneline`（scope と文体を既存の履歴に揃えるため）

メッセージに入れるのはステージ済みの変更だけ。ステージが空なら、その旨を書いてコマンドは作らない。関連する未ステージや未追跡のファイルがあれば、返信で名前を挙げ、メッセージには入れない。

ステージ内容が複数の意図に分かれる場合は、1つのメッセージにまとめず、分割を提案する。

秘密情報が含まれていたら、コマンドを作らず、そのファイルを示す。

## 作るもの

この形のコマンドを1つ。

```bash
git commit -m "$(cat <<'EOF'
type: subject

body (why)

EOF
)"
```

## 実行の承認

- コマンドを作ったら、提示して **実行してよいかユーザーに確認する**（ターミナルに手で貼らせる前提にしない）
- 承認された場合のみ、そのコマンドをターミナルで実行する。実行したら、コミットハッシュと `git log -1 --oneline` の結果を報告する
- 承認されなかったら、コマンドをテキストとして残して終わる（後から手動で実行できるように）
- 実行が失敗したら、エラー内容をそのまま報告する。再試行やメッセージの書き換えは、ユーザーの指示を待つ
