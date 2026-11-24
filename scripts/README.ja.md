[English](README.md) | 日本語

# scripts

このリポジトリのルールとスキルの言語版を処理するスクリプト群。正本は `rules.ja/` と `skills.ja/` で、他の版（`rules.en/` や `skills.en/` など）は翻訳スクリプトが正本から生成する。実行はすべてリポジトリのルートから行う。

各スクリプトの契約（オプション、エラー文面、報告形式、テスト）の正本は [SPEC.ja.md](SPEC.ja.md)（英語版は [SPEC.md](SPEC.md)）。この README では繰り返さない。

## スクリプト

| スクリプト | 仕事 | 基本の呼び方 |
|---|---|---|
| `build-rules` | 1つのルール版から Cursor 用と Claude 用のルールファイルを生成する | `scripts/build-rules --lang en` |
| `install-rules` | 生成したルールファイルを `~/.cursor/rules/` と `~/.claude/rules/` へリンクする | `scripts/install-rules --lang en` |
| `install-skills` | 1つの版のスキルをホームのスキル置き場へリンクする | `scripts/install-skills --lang en` |
| `translate-rules` | `rules.<from>/` を `rules.<to>/` へ翻訳する（既定は `ja` から `en`） | `scripts/translate-rules` |
| `translate-skills` | `skills.<from>/` を `skills.<to>/` へ翻訳する（既定は `ja` から `en`） | `scripts/translate-skills` |

`build-rules`、`install-rules`、`install-skills` は `--check` を受け付ける。ずれを報告するだけで何も書かない。翻訳スクリプトは `claude -p` を呼ぶので、Claude Code にログインしておく必要がある。

## 典型的な作業の流れ

1. 正本（`rules.ja/` か `skills.ja/`）を編集してコミットする
2. 翻訳する：`scripts/translate-rules` と `scripts/translate-skills`。`rules.en/` と `skills.en/` の変更を確認してコミットする
3. ルールファイルを生成する：`scripts/build-rules --lang en`
4. 配置する：`scripts/install-rules --lang en` と `scripts/install-skills --lang en`
5. 確認する：`build-rules`、`install-rules`、`install-skills` を `--check` 付きでもう一度実行する

ルール版の生成と配置は、同じ `--lang` で続けて行う。

## テストの回し方

```sh
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
```

テストは一時リポジトリと偽の翻訳コマンドを使うので、`claude` は呼ばず、ホームディレクトリにも触れない。
