# このフォルダは何か
**「てらこ先生のスマホ相談室」**（Spotify のポッドキャスト番組・2026-09-11 開始）の実体。
作業前に `PROGRAM_SPEC.md` を全文読む。決定は藤崎さんのもの。品質を下げる変更をしない。

- 台本 → 声 → 配信は `make_episode.py`（使い方は PROGRAM_SPEC.md）
- 声は Teraco Voice（`~/ai-office/products.json`）。**作ったら `meta.json` の `voice` を確認する**
- 音声（mp3/wav）は git に入れない大きさに注意。`work/` は `.gitignore` 済み
- 世界一わかりやすいAIニュース（`~/Documents/Claude/ai-news-repo`）とは**別番組・別RSS**。混ぜない
- 進捗は `~/Documents/GitHub/teraco-hub/projects/sumaho_soudan/STATUS.md`
