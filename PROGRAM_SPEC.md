# てらこ先生のスマホ相談室 — 番組設計書

**決定日 2026-09-11（藤崎さん）。** ここに書いてあることは本人の決定。変えるときは日付と本人の言葉を残す。

## 何のための番組か
- 通いの生徒さん（シニア）が、教室のあとで**「あれ、どうやるんだったっけ」を聴き直せる**場所
- まだ会っていない人が、**てらこ先生の教え方**に触れて教室を知る入口
- 発信の軸を「AI」だけでなく**「スマホの活用」**にも広げる（世界一わかりやすいAIニュースとは別番組）

## 決めたこと

| 項目 | 決定 | 理由 |
|---|---|---|
| 番組名 | **てらこ先生のスマホ相談室** | 藤崎さんの選択 |
| 形式 | **1人語り**（ゆっくり・講座風） | シニアには1人の声・一定の速さが追いやすい |
| 長さ | **4〜7分**（目安。長さより「伝わるか」を優先） | 1本1テーマ。長いと離脱する。1本目4分10秒を聴いて「全然問題ない、大事なのは伝わるかどうか」（藤崎さん 2026-09-11） |
| 頻度 | **週2本**（火・金） | 教室運営と両立でき、番組も育つ |
| 声 | **Teraco Voice**（本人の声・0円） | 製品台帳 `~/ai-office/products.json` |
| ネタ | **候補を並べて藤崎さんが選ぶ**。候補は教室の音声メモ（Studioの知識ベース）から | 実際に出た質問が最良のネタ |
| 配信 | **Spotify**（RSS）＋ **LINE**（生徒さん向け・簡単プレイヤー） | Spotify未導入の生徒さんが多い前提 |
| メール | Substack「てらこ先生｜スマホとAIの実践教室」に**セクション「スマホ相談室」を追加** | 読者が少ないうちはリストを分けない |
| 1本目 | **LINEで写真をまとめて送る** | 動画の見本と同じテーマ。素材あり |
| 費用 | **0円**（台本＝ローカルAI、声＝Teraco Voice、置き場＝GitHub Pages） | 有料APIを既定にしない |

## 1本の構成（4〜7分・1,500〜2,200字。1文字≒0.16秒）
1. **あいさつ＋今日できるようになること**（1文で）
2. **教室で実際にあった困りごと**（藤崎さんの体験。生徒さんの言葉）
3. **やり方を順番に**（3〜4ステップ。1ステップずつ「ここがコツ」）
4. **よくあるつまずきと直し方**（例：真ん中を押すと写真が開いてしまう）
5. **おまけの豆知識**（1つだけ。例：オリジナル画質・グループで送る）
6. **まとめ＋呼びかけ**（教室・LINE・次回）

## 台本の決まり（Teraco Voice で読ませる前提）
- 1文は **40字まで**。長い文は切る（音声認識の検収に通りやすい）
- 人を指す「方」を使わない（「ほう」と誤読する）→「人」「みなさん」
- 英字は必ずカタカナに（LINE→ライン、Wi-Fi→ワイファイ）。読み辞書は
  `~/ai-office/advisors/lecture/readings.json` と Studio の `normalize_reading()` の両方をかける
- 呼びかけの後は「！」（読点だと語尾が伸びる）
- 絵文字・記号は使わない
- **教室の言葉を使う。** Studio の知識ベース（`knowledge/*.md`）にある本人の言い回しを台本に入れる。
  AIの一般論だけの回にしない（AIニュースの記事で決めた方針と同じ）

## 番組の説明（Spotify の番組ページ）
> スマホ教室のてらこ先生が、教室で実際に聞かれた「これ、どうやるの？」に、1回1つ、5分で答えます。
> LINE・写真・PayPay・詐欺メールの見分け方まで。ゆっくり話すので、聴きながら一緒に指を動かせます。
> 宮崎県西都市のスマホ教室 TERACO.LABO から。

## つくり方（`make_episode.py`）
```
python3 make_episode.py new  <スラッグ> "<テーマ>"   # 設計書の枠と作業フォルダを作る
python3 make_episode.py script <スラッグ>            # 設計書＋教室の言葉 → 台本（ローカルAI・0円）
python3 make_episode.py voice  <スラッグ>            # 台本 → Teraco Voice → mp3（このMacだけ・0円）
python3 make_episode.py feed   <スラッグ>            # 公開用 mp3 を podcast/ に置き feed.xml を更新
python3 make_episode.py cover                        # カバー画像（3000x3000）
```
**台本は毎回、藤崎さんが目を通してから voice にかける。**（設計書の「体験」の部分はAIに書かせない）

## 置き場と配信
- 実体: `~/Documents/GitHub/teraco-sumaho-soudan`（GitHub `teraco-labo/teraco-sumaho-soudan`・公開）
- 公開URL: `https://teraco-labo.github.io/teraco-sumaho-soudan/`（GitHub Pages）
- RSS: `.../feed.xml` → Spotify for Creators に登録（藤崎さんのログインが必要・初回のみ）
- **フィードURLを変えると Spotify は再登録になる**（AIニュースで実際に起きた）。URLは動かさない

## 自動化と費用（RULES 5 に従う）
- **AIクレジットはかからない。** 台本はローカルAI（Ollama）、声はTeraco Voice（Mac内）、置き場はGitHub Pages。
  外部の有料APIを1つも呼ばない。かかるのは私（Claude）と会話しているときだけ
- 声づくりは **このMacでしか動かない**。まずは手動（藤崎さんが台本を確認 → voice → feed → push）。
  定時化するなら AIニュースと同じく `~/ai-office/work/` に複製を置く（launchd は ~/Documents を読めない）

## 公開先（2026-09-11 に開設）
| 場所 | URL | 状態 |
|---|---|---|
| 置き場（GitHub Pages） | https://teraco-labo.github.io/teraco-sumaho-soudan/ | 公開済み。生徒さんにはこのURLを LINE で渡す（押すだけプレイヤー） |
| RSS（Spotify に登録するURL） | https://teraco-labo.github.io/teraco-sumaho-soudan/feed.xml | 公開済み |
| Substack セクション | https://teracosensei.substack.com/s/sumaho | 作成済み（新規購読者は自動追加・既存リストもコピー） |
| Spotify 番組 | https://open.spotify.com/show/1yRCTJ5JaeuOf7ZlPftI0R | 2026-09-11 登録済み（Japan／Japanese／Educational・How-to）。公開まで最大24時間 |

## まだ決めていないこと
- LINE への届け方（週1まとめで「今週の2本」か、1本ごとか）
- Substack の「ポッドキャストをインポート」で上の RSS を取り込むか（取り込めば各回が Substack にも音声つきで並ぶ。要検証）
