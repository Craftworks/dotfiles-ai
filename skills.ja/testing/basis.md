# 出典と統合の経緯

このスキルは2つの出自を統合したもの（2026-11-22）。

- 自前の `testing` ルール（旧 `rules.ja/testing/`、同日スキル化のため廃止）：方針の正本。公開面の振る舞い検証、配分は複雑さとリスクの所在、実サンプルの回帰資産化、エラー文面の固定、混在ケース、Decision test
- Matt Pocock の `tdd` スキル：seam の事前合意、ループの作法（red before green、垂直スライス）、同語反復・水平スライスの反パターン、同梱の tests.md／mocking.md
  - 上流: https://github.com/mattpocock/skills の `skills/engineering/tdd/`
  - 取り込み時点の上流 commit: abeeaf9（2026-11-19）
  - 上流の版: plugin version 1.3.2（`.claude-plugin/plugin.json`）
  - ライセンス: MIT（Copyright (c) 2026 Matt Pocock）

統合の方針：方針は旧ルール、作法は tdd。重なっていた反パターン（実装結合と内部呼び出しの検証）は1項目に統合した
