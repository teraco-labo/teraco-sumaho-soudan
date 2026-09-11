#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""てらこ先生のスマホ相談室 — 1本を作る道具。

  new    <slug> "<テーマ>"   設計書の枠と作業フォルダを作る
  script <slug>              設計書＋教室の言葉 → 1人語りの台本（ローカルAI・0円）
  voice  <slug>              台本 → Teraco Voice → mp3（このMacだけ・0円）
  feed   <slug>              公開用 mp3 を podcast/ に置き、episodes.json と feed.xml を更新
  cover                      カバー画像（3000x3000 JPEG）

台本は voice にかける前に藤崎さんが目を通す（PROGRAM_SPEC.md）。
"""
import json, os, re, subprocess, sys, shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
EPS = HERE / "episodes"
NEWS_REPO = Path.home() / "Documents/Claude/ai-news-repo"          # 部品の借り元
STUDIO = Path.home() / ".openclaw/workspace/terako-sensei"           # 知識ベース・読み辞書
READINGS = Path.home() / "ai-office/advisors/lecture/readings.json"  # 読み替え辞書（講義用）
JST = timezone(timedelta(hours=9))


def _log(msg):  print(msg, flush=True)
def _ep(slug):  return EPS / slug
def _meta(slug):
    f = _ep(slug) / "meta.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
def _save_meta(slug, m):
    (_ep(slug) / "meta.json").write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


# ─── new ─────────────────────────────────────────────────────────
def cmd_new(slug, theme):
    d = _ep(slug); d.mkdir(parents=True, exist_ok=True)
    brief = d / "brief.json"
    if not brief.exists():
        brief.write_text(json.dumps({
            "theme": theme, "audience": "シニア",
            "conclusion": "", "points": ["", "", ""], "analogy": "",
            "terms": [], "action": "", "cta": "LINE",
            "_note": "Studio の設計書と同じ型。結論・ポイント3つ・やってみることを埋めると台本が良くなる。空でも動く"
        }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    _save_meta(slug, {"slug": slug, "theme": theme, "created": datetime.now(JST).strftime("%Y-%m-%d")})
    _log(f"作りました: {d}\n  設計書: {brief}")


# ─── script ──────────────────────────────────────────────────────
def _classroom_quotes(theme: str, limit_chars: int = 2500) -> str:
    """教室の音声メモ（Studio の知識ベース）から、テーマに関係する本人の言葉を拾う。"""
    kb = STUDIO / "knowledge"
    if not kb.exists():
        return ""
    # テーマ文から検索語を取り出す（漢字・カタカナ・英字のかたまり。「LINEで写真を…」→ LINE／写真／送る）
    raw = re.findall(r"[A-Za-z]+|[ァ-ヶー]{2,}|[一-龥]{1,3}", theme)
    alias = {"LINE": ["ライン"], "PayPay": ["ペイペイ"], "Wi-Fi": ["ワイファイ"]}
    keys = []
    for k in raw:
        keys.append(k); keys += alias.get(k, [])
    keys = [k for k in dict.fromkeys(keys) if k not in ("方法", "やり", "こと", "する")]
    hits = []
    for f in sorted(kb.glob("*.md")):
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            if len(line) < 30 or line.startswith("#"):
                continue
            score = sum(line.count(k) for k in keys)
            if score >= 2:
                hits.append((score, line.strip()))
    hits.sort(key=lambda x: -x[0])
    out, n, seen = [], 0, set()
    for _, line in hits:
        if line in seen:
            continue            # 同じ文字起こしが複数の知識ファイルに入っていることがある
        seen.add(line)
        if n + len(line) > limit_chars:
            break
        out.append("・" + line[:300]); n += len(line)
    return "\n".join(out)


def _ollama(prompt: str) -> str:
    import urllib.request
    body = json.dumps({"model": CFG["ollama_model"], "prompt": prompt, "stream": False,
                       "think": False,  # 推論モデルは think:false が無いと response が空になる
                       "options": {"temperature": 0.6, "num_predict": 4000}}).encode()
    req = urllib.request.Request(f"{CFG['ollama_url']}/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["response"]


SCRIPT_PROMPT = """あなたは「てらこ先生」（藤崎修一・宮崎県西都市のスマホ教室 TERACO.LABO の講師）です。
理念は「難しいことを簡単にする」。ポッドキャスト番組「てらこ先生のスマホ相談室」の台本を書きます。

【聴く人】スマホ教室に通うシニアの生徒さん。スマホは持っているが、操作に自信がない。
【形式】てらこ先生の1人語り。ゆっくり、あたたかく、目の前の生徒さんに話しかけるように。
【長さ】{lo}〜{hi}文字（読み上げて5〜7分）。

【今回のテーマ】{theme}
【設計書】
{brief}

【教室で実際に話した言葉（文字起こし。この言い回し・体験を台本に活かす。丸写しはしない）】
{quotes}

【構成（この順で）】
1. あいさつ。「こんにちは、てらこ先生です」から始め、今日できるようになることを1文で
2. 教室で実際にあった困りごと（生徒さんの言葉を1つ入れる）
3. やり方を順番に。3〜4ステップ。1ステップごとに「ここがコツ」を1つ
4. よくあるつまずきと直し方
5. おまけの豆知識を1つだけ
6. まとめ。教室と公式LINEへの呼びかけで締める（次回の予告は不要）

【言葉の決まり（必ず守る）】
- 1文は40文字まで。長い文は2つに切る
- 人を指す「方」は使わない。「人」「みなさん」「生徒さん」と書く
- 英字は使わない。LINE はライン、Wi-Fi はワイファイ、iPhone はアイフォーン と書く
- 絵文字・記号・箇条書き記号は使わない。見出しも書かない
- 段落ごとに空行を1つ入れる
- 台本の文章だけを出力する。説明や前置き、タイトルは書かない"""


def cmd_script(slug):
    m = _meta(slug); d = _ep(slug)
    brief = json.loads((d / "brief.json").read_text(encoding="utf-8"))
    theme = brief.get("theme") or m.get("theme", slug)
    lo, hi = CFG.get("target_chars", [1500, 1800])
    brief_txt = "\n".join(f"{k}: {v}" for k, v in brief.items()
                          if not k.startswith("_") and v and v != ["", "", ""])
    quotes = _classroom_quotes(theme)
    _log(f"教室の言葉: {len(quotes)}文字ぶん拾いました")
    prompt = SCRIPT_PROMPT.format(lo=lo, hi=hi, theme=theme, brief=brief_txt or "（未記入）",
                                  quotes=quotes or "（該当なし）")
    for attempt in range(1, 4):
        raw = _ollama(prompt).strip()
        raw = re.sub(r"^```.*?\n|```$", "", raw, flags=re.S).strip()
        n = len(raw.replace("\n", ""))
        _log(f"  {attempt}回目: {n}文字")
        if lo * 0.8 <= n <= hi * 1.25:
            break
        prompt_fix = prompt + f"\n\n【修正】前回は{n}文字でした。{lo}〜{hi}文字に収めてください。"
        prompt = prompt_fix
    (d / "script.txt").write_text(raw + "\n", encoding="utf-8")
    m.update({"script_chars": n, "script_made": datetime.now(JST).strftime("%Y-%m-%d %H:%M")})
    _save_meta(slug, m)
    _log(f"台本: {d/'script.txt'}\n→ 目を通してから `voice {slug}`")


# ─── voice ───────────────────────────────────────────────────────
def _readings_apply(text: str) -> str:
    """読み替え辞書（講義用）＋Studio の英字カタカナ化。声に渡す文字だけを変える。"""
    try:
        d = json.loads(READINGS.read_text(encoding="utf-8"))
        for k in sorted((k for k in d if not k.startswith("_")), key=len, reverse=True):
            text = text.replace(k, d[k])
    except Exception:
        pass
    try:
        sys.path.insert(0, str(STUDIO))
        from video_factory import normalize_reading
        text = normalize_reading(text)
    except Exception:
        pass
    return text


def _paragraphs(script: str):
    """台本を「声に出す単位」に切る。段落ごと、ただし120字を超えたら文で分ける。"""
    out = []
    for para in re.split(r"\n\s*\n", script.strip()):
        para = " ".join(l.strip() for l in para.splitlines() if l.strip())
        if not para:
            continue
        if len(para) <= 120:
            out.append(para); continue
        buf = ""
        for s in re.findall(r"[^。！？]+[。！？]?", para):
            if len(buf) + len(s) > 120 and buf:
                out.append(buf); buf = ""
            buf += s
        if buf:
            out.append(buf)
    return out


def cmd_voice(slug):
    sys.path.insert(0, str(NEWS_REPO))
    import podcast_teraco_voice as pv               # Teraco Voice の部品（AIニュースと共用）
    d = _ep(slug); work = d / "work"; work.mkdir(exist_ok=True)
    script = (d / "script.txt").read_text(encoding="utf-8")
    paras = _paragraphs(script)
    _log(f"段落 {len(paras)} 件を Teraco Voice で作ります（0円・このMacの中）")
    jobs = []
    for i, p in enumerate(paras):
        text = pv._tidy_for_teraco(_readings_apply(p))
        jobs.append({"text": text, "out": str(work / f"p_{i:03d}.wav")})
    todo = [j for j in jobs if not (Path(j["out"]).exists() and Path(j["out"]).stat().st_size > 0)]
    log = open(work / "voice.log", "a", encoding="utf-8")
    if todo:
        pv.synth_teraco(todo, log)
        for j in todo:
            pv.trim_pauses(Path(j["out"]))
    # 音量をそろえて結合（1人語りなので相手との差し引きは無し＝0dB）
    entries = []
    sil = work / "sil.wav"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "0.45",
                    "-c:a", "pcm_s16le", str(sil)], capture_output=True, check=True)
    missing = []
    for i, j in enumerate(jobs):
        src = Path(j["out"])
        if not src.exists() or src.stat().st_size == 0:
            missing.append(i); continue
        dst = work / f"n_{i:03d}.wav"
        pv.to_pcm(src, dst, 0.0)
        if entries:
            entries.append(sil)
        entries.append(dst)
    lst = work / "concat.txt"
    lst.write_text("".join(f"file '{e}'\n" for e in entries))
    mp3 = d / "audio.mp3"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "80k",
                    "-write_xing", "1", "-id3v2_version", "3", str(mp3)], capture_output=True, check=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", str(mp3)], capture_output=True, text=True).stdout.strip() or 0)
    m = _meta(slug)
    m.update({"voice": f"Teraco Voice {_teraco_version()}", "duration_sec": round(dur, 1),
              "paragraphs": len(paras), "missing_paragraphs": missing,
              "voice_made": datetime.now(JST).strftime("%Y-%m-%d %H:%M")})
    _save_meta(slug, m)
    _log(f"できました {mp3}  {dur/60:.1f}分" + (f"  ！作れなかった段落 {missing}" if missing else ""))


def _teraco_version() -> str:
    try:
        d = json.loads((Path.home() / "ai-office/products.json").read_text(encoding="utf-8"))
        for p in d.get("products", []):
            if p.get("name") == "Teraco Voice":
                return p.get("version", "")
    except Exception:
        pass
    return ""


# ─── feed ────────────────────────────────────────────────────────
def _rfc2822(date_str, ep_num=0):
    """公開日時。同じ日に2本出しても順番が崩れないよう、回数ぶんの分を足す（第2回=6:02）"""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=6, minute=min(int(ep_num), 59), tzinfo=JST)
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")

def _hms(sec):
    sec = int(sec); return f"{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d}"

def _x(s):  return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def cmd_feed(slug, title=None, date=None):
    d = _ep(slug); m = _meta(slug)
    src = d / "audio.mp3"
    if not src.exists():
        raise SystemExit("audio.mp3 がありません。先に voice を")
    date = date or m.get("published") or datetime.now(JST).strftime("%Y-%m-%d")
    title = title or m.get("title") or m.get("theme", slug)
    pub = HERE / "podcast" / f"{date}_{slug}.mp3"
    shutil.copy2(src, pub)
    base = CFG["base_url"].rstrip("/")
    eps_file = HERE / "episodes.json"
    eps = json.loads(eps_file.read_text(encoding="utf-8")) if eps_file.exists() else []
    existing = next((e for e in eps if e["slug"] == slug), None)
    eps = [e for e in eps if e["slug"] != slug]
    num = existing["episode_num"] if existing else (max([e["episode_num"] for e in eps] or [0]) + 1)
    desc = m.get("description") or f"{title}。教室で実際に聞かれた質問に、てらこ先生がゆっくり答えます。"
    eps.insert(0, {"slug": slug, "date": date, "title": title, "description": desc,
                   "url": f"{base}/podcast/{pub.name}", "size": pub.stat().st_size,
                   "duration": int(m.get("duration_sec", 0)), "episode_num": num,
                   "voice": m.get("voice", "")})
    eps_file.write_text(json.dumps(eps, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    m.update({"published": date, "title": title, "episode_num": num}); _save_meta(slug, m)

    items = ""
    for e in eps:
        tail = (f" ／ 教室と公式LINE → {CFG['line_url']}" if CFG.get("line_url") else "")
        items += f"""
  <item>
    <title>{_x(e['title'])}</title>
    <itunes:title>{_x(e['title'])}</itunes:title>
    <description>{_x(e['description'] + tail)}</description>
    <itunes:summary>{_x(e['description'] + tail)}</itunes:summary>
    <enclosure url="{e['url']}" length="{e['size']}" type="audio/mpeg"/>
    <guid isPermaLink="false">{e['url']}</guid>
    <pubDate>{_rfc2822(e['date'], e['episode_num'])}</pubDate>
    <itunes:author>{_x(CFG['author'])}</itunes:author>
    <itunes:episode>{e['episode_num']}</itunes:episode>
    <itunes:episodeType>full</itunes:episodeType>
    <itunes:duration>{_hms(e['duration'])}</itunes:duration>
    <itunes:explicit>false</itunes:explicit>
  </item>"""
    cat1, cat2 = CFG.get("category", ["Education", "How To"])
    cover_v = datetime.now(JST).strftime("%Y%m%d")
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
  <title>{_x(CFG['show_title'])}</title>
  <itunes:title>{_x(CFG['show_title'])}</itunes:title>
  <link>{base}/</link>
  <atom:link href="{base}/feed.xml" rel="self" type="application/rss+xml"/>
  <language>ja</language>
  <description>{_x(CFG['description'])}</description>
  <itunes:summary>{_x(CFG['description'])}</itunes:summary>
  <itunes:author>{_x(CFG['author'])}</itunes:author>
  <itunes:owner>
    <itunes:name>{_x(CFG['author'])}</itunes:name>
    <itunes:email>{CFG['owner_email']}</itunes:email>
  </itunes:owner>
  <image><url>{base}/cover.jpg?v={cover_v}</url><title>{_x(CFG['show_title'])}</title><link>{base}/</link></image>
  <itunes:image href="{base}/cover.jpg?v={cover_v}"/>
  <itunes:explicit>false</itunes:explicit>
  <itunes:type>episodic</itunes:type>
  <itunes:category text="{cat1}"><itunes:category text="{cat2}"/></itunes:category>
  <lastBuildDate>{datetime.now(JST).strftime("%a, %d %b %Y %H:%M:%S %z")}</lastBuildDate>{items}
</channel>
</rss>
"""
    (HERE / "feed.xml").write_text(feed, encoding="utf-8")
    _log(f"feed.xml を更新（{len(eps)}本）。公開用: {pub}")


# ─── cover ───────────────────────────────────────────────────────
def cmd_cover():
    """カバー画像。リンク集と同じクリーム＋深緑（見やすさの原則5）、キャラはメガネなし。"""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    sys.path.insert(0, str(NEWS_REPO))
    import tools_make_cover as tc
    SIZE = 3000
    CREAM, GREEN, GREEN_DARK = (250, 247, 241), (63, 107, 79), (46, 82, 60)
    canvas = Image.new("RGBA", (SIZE, SIZE), CREAM + (255,))
    # 下半分にやわらかい緑の面（人物の背景）
    band = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(band).ellipse([-400, 1500, SIZE + 400, SIZE + 900], fill=GREEN + (255,))
    canvas = Image.alpha_composite(canvas, band)
    ch = tc.trim(tc.shave_edge(tc.strip_white_background(Image.open(tc.CHAR))))
    w = 1500; ch = ch.resize((w, round(ch.height * w / ch.width)), Image.LANCZOS)
    canvas.alpha_composite(ch, (round((SIZE - w) / 2) + 20, 1330))
    draw = ImageDraw.Draw(canvas)
    fb = Path.home() / "Library/Fonts/ZenKakuGothicNew-Bold.ttf"
    fm = Path.home() / "Library/Fonts/ZenKakuGothicNew-Medium.ttf"
    f1 = ImageFont.truetype(str(fb), 300); f2 = ImageFont.truetype(str(fm), 150); f3 = ImageFont.truetype(str(fm), 105)
    def center(y, text, font, fill):
        tw = draw.textlength(text, font=font); draw.text(((SIZE - tw) / 2, y), text, font=font, fill=fill)
    center(300, "てらこ先生の", f2, GREEN_DARK)
    center(500, "スマホ相談室", f1, GREEN_DARK)
    center(920, "教室で聞かれた「どうやるの？」に、1回1つ5分で", f3, (90, 90, 84))
    # 教室名は右下の緑の面に（中央に置くと服の白と重なって消える）
    tw = draw.textlength("TERACO.LABO", font=f3)
    draw.text((SIZE - 160 - tw, SIZE - 250), "TERACO.LABO", font=f3, fill=(255, 255, 255))
    out = HERE / "cover.jpg"
    canvas.convert("RGB").save(out, "JPEG", quality=92)
    _log(f"カバー: {out}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(0)
    cmd = a[0]
    if cmd == "new":      cmd_new(a[1], a[2])
    elif cmd == "script": cmd_script(a[1])
    elif cmd == "voice":  cmd_voice(a[1])
    elif cmd == "feed":   cmd_feed(a[1], *(a[2:3]), *(a[3:4]))
    elif cmd == "cover":  cmd_cover()
    else: print(__doc__)
