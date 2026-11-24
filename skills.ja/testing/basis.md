# 出典と統合の経緯

このスキルは2つの出自を統合したもの（2026-11-22）。

- 自前の `testing` ルール（旧 `rules.ja/testing/`、同日スキル化のため廃止）：方針の正本。公開面の振る舞い検証、配分は複雑さとリスクの所在、実サンプルの回帰資産化、エラー文面の固定、混在ケース、Decision test
- Matt Pocock の `tdd` スキル：seam の事前合意、ループの作法（red before green、垂直スライス）、同語反復・水平スライスの反パターン、同梱の tests.md／mocking.md
  - 上流: https://github.com/mattpocock/skills の `skills/engineering/tdd/`
  - 取り込み時点の上流 commit: abeeaf9（2026-11-19）
  - 上流の版: plugin version 1.3.2（`.claude-plugin/plugin.json`）
  - ライセンス: MIT（Copyright (c) 2026 Matt Pocock）

統合の方針：方針は旧ルール、作法は tdd。重なっていた反パターン（実装結合と内部呼び出しの検証）は1項目に統合した

## 改訂（2026-11-24）：仕様と検証の観点

一次情報の調査をもとに、方針へ次の行を足した。出典の文面は取り込んでいない（考え方だけを採った）。

- 「テストを弱めない」「期待値の変更は承認者に示す」：Anthropic の Claude Code ベストプラクティス（実装フェーズでテストを変更しない）。Adzic のパターン5（仕様を変えずに検証を自動化する）
- 「スイート全体を回す」「失敗はテストの名前で報告する」：公開されている実践者の AI スキル群に共通していた義務。Martraire の Reliable（同期を機構で保証する）

保留：

- ループの作法「red は実行して確かめる」：観測した失敗がまだないため

取り込まなかったもの：

- red／green の節目でのコミット（t_wada）：`git` スキル（コミットは指示があるときだけ、マージ前に WIP を squash する）と矛盾するため。監査の証拠は完了時の報告で残す
- テストを全部先にコミットする手順：垂直スライスの作法と矛盾するため
- living documentation という位置づけを冒頭に置くこと：細部の正本の置き場所は change-discipline が持つため。置くと同じ取り決めが2か所になる
- テストの範囲をゴールから導くこと（Adzic のパターン1・2）：seam の事前合意と change-discipline の完了条件が担っているため
- Adzic の完全形（仕様＝テスト＝生成される文書）：SPEC は契約となぜを持ち、テストからは生成しないため

出典：

- Gojko Adzic『Specification by Example』（Manning, 2011）
- Cyrille Martraire『Living Documentation』（Addison-Wesley, 2019）
- Anthropic, Claude Code best practices: https://www.anthropic.com/research/claude-code-best-practices
- t_wada『AI時代のTDD』（講演スライド、2026-04-20 版）: https://files.speakerdeck.com/presentations/5570d7aff96e4cbbbff1076108585202/tdd-in-ai-era-20260420-recruit-edition.pdf
- 実践者の公開 AI スキル: obra/superpowers の test-driven-development スキル https://github.com/obra/superpowers/blob/main/skills/test-driven-development/SKILL.md （2026-11-24 に main で参照。commit は固定していない）
