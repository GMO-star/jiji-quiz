#!/usr/bin/env python3
"""
時事クイズ自動生成スクリプト
- 無料のRSSフィードからニュースを収集
- Google Gemini API（無料枠）でクイズ問題を生成
- JSONファイルに保存 → GitHub Gist / ローカルで配信
"""

import os
import json
import time
import datetime
import hashlib
import requests
import feedparser
from pathlib import Path

# ===================== 設定 =====================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_KEY_HERE")
OUTPUT_DIR = Path("./quiz_data")
MAX_QUESTIONS_PER_RUN = 10   # 1回の実行で生成する問題数
MAX_NEWS_PER_FEED = 5         # 各RSSから取得するニュース数上限

# GitHub Gist への保存（任意）
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GIST_ID = os.environ.get("GIST_ID", "")   # 既存GistのIDを指定

# ===============================================

# 無料で利用できる日本語RSSフィード一覧
RSS_FEEDS = [
    {
        "name": "NHKニュース",
        "url": "https://www.nhk.or.jp/rss/news/cat0.xml",
        "category": "総合"
    },
    {
        "name": "NHKニュース 政治",
        "url": "https://www.nhk.or.jp/rss/news/cat4.xml",
        "category": "政治・外交"
    },
    {
        "name": "NHKニュース 経済",
        "url": "https://www.nhk.or.jp/rss/news/cat5.xml",
        "category": "経済・ビジネス"
    },
    {
        "name": "NHKニュース 科学・文化",
        "url": "https://www.nhk.or.jp/rss/news/cat3.xml",
        "category": "科学・技術"
    },
    {
        "name": "NHKニュース 国際",
        "url": "https://www.nhk.or.jp/rss/news/cat6.xml",
        "category": "国際情勢"
    },
]

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


def collect_news() -> list[dict]:
    """RSSフィードからニュースを収集する"""
    all_news = []
    print("[1/3] ニュース収集中...")

    for feed_info in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"])
            count = 0
            for entry in feed.entries:
                if count >= MAX_NEWS_PER_FEED:
                    break
                title = entry.get("title", "").strip()
                summary = entry.get("summary", entry.get("description", "")).strip()
                if not title:
                    continue
                # HTMLタグを簡易除去
                import re
                summary = re.sub(r"<[^>]+>", "", summary)[:300]

                all_news.append({
                    "source": feed_info["name"],
                    "category": feed_info["category"],
                    "title": title,
                    "summary": summary,
                    "url": entry.get("link", ""),
                    "published": entry.get("published", "")
                })
                count += 1
            print(f"  ✓ {feed_info['name']}: {count}件取得")
        except Exception as e:
            print(f"  ✗ {feed_info['name']}: {e}")

    print(f"  → 合計 {len(all_news)} 件のニュースを収集")
    return all_news


def generate_quiz_with_gemini(news_items: list[dict]) -> list[dict]:
    """Gemini APIを使ってクイズ問題を生成する"""
    print("[2/3] Gemini APIでクイズ生成中...")

    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_KEY_HERE":
        print("  ⚠ GEMINI_API_KEY が未設定です。サンプル問題を返します。")
        return generate_sample_questions()

    # ニュースをまとめてプロンプトに変換
    news_text = ""
    for i, news in enumerate(news_items[:20]):  # 最大20件送る
        news_text += f"[{i+1}] ({news['category']}) {news['title']}\n"
        if news.get("summary"):
            news_text += f"   概要: {news['summary'][:150]}\n"

    prompt = f"""以下の最新ニュース情報を参考に、時事クイズを{MAX_QUESTIONS_PER_RUN}問作成してください。

=== 最新ニュース ===
{news_text}
==================

各問題をJSONのみで出力してください（マークダウンのコードブロックは不要）。

{{
  "questions": [
    {{
      "category": "カテゴリ名",
      "question": "問題文（具体的な人名・数字・地名を含む、答えが明確な短文）",
      "choices": ["選択肢A", "選択肢B", "選択肢C", "選択肢D"],
      "answer": 0,
      "explanation": "正解の解説（2〜3文）",
      "source": "参考ニュースのタイトル",
      "created_at": "{datetime.datetime.now().strftime('%Y-%m-%d')}"
    }}
  ]
}}

条件:
- answerは0〜3のインデックス（正解の選択肢の番号）
- 選択肢は4つ必ず用意し、紛らわしいものを含める
- 上記ニュースに基づいた問題を優先し、足りない場合は2024〜2025年の時事問題で補う
- カテゴリは「政治・外交」「経済・ビジネス」「科学・技術」「国際情勢」「社会・環境」「スポーツ」から選ぶ
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096}
    }

    try:
        resp = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]

        # JSONを抽出
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if not json_match:
            raise ValueError("JSONが見つかりませんでした")

        parsed = json.loads(json_match.group())
        questions = parsed["questions"]
        print(f"  ✓ {len(questions)}問を生成")
        return questions

    except Exception as e:
        print(f"  ✗ Gemini APIエラー: {e}")
        print("  → サンプル問題を使用します")
        return generate_sample_questions()


def generate_sample_questions() -> list[dict]:
    """APIキー未設定時のサンプル問題"""
    return [
        {
            "category": "経済・ビジネス",
            "question": "2025年4月、米国が日本に課した相互関税の税率は？",
            "choices": ["10%", "24%", "46%", "50%"],
            "answer": 1,
            "explanation": "トランプ政権は2025年4月に日本製品に24%の相互関税を発動。90日の猶予後も交渉が続いています。",
            "source": "サンプル",
            "created_at": datetime.date.today().isoformat()
        }
    ]


def deduplicate_questions(existing: list[dict], new_qs: list[dict]) -> list[dict]:
    """重複する問題を除去する（問題文のハッシュで判定）"""
    existing_hashes = {
        hashlib.md5(q["question"].encode()).hexdigest()
        for q in existing
    }
    unique = []
    for q in new_qs:
        h = hashlib.md5(q["question"].encode()).hexdigest()
        if h not in existing_hashes:
            unique.append(q)
            existing_hashes.add(h)
    return unique


def save_questions(questions: list[dict]):
    """問題をJSONファイルに保存する"""
    print("[3/3] 問題を保存中...")
    OUTPUT_DIR.mkdir(exist_ok=True)

    today = datetime.date.today().isoformat()
    daily_file = OUTPUT_DIR / f"quiz_{today}.json"
    all_file = OUTPUT_DIR / "quiz_all.json"

    # 今日の問題を保存
    daily_data = {
        "date": today,
        "generated_at": datetime.datetime.now().isoformat(),
        "count": len(questions),
        "questions": questions
    }
    daily_file.write_text(json.dumps(daily_data, ensure_ascii=False, indent=2))
    print(f"  ✓ 今日の問題: {daily_file}")

    # 全問題に追記（重複除外）
    if all_file.exists():
        all_data = json.loads(all_file.read_text())
        existing_qs = all_data.get("questions", [])
    else:
        existing_qs = []

    new_unique = deduplicate_questions(existing_qs, questions)
    all_qs = existing_qs + new_unique
    all_data = {
        "last_updated": datetime.datetime.now().isoformat(),
        "total_count": len(all_qs),
        "questions": all_qs
    }
    all_file.write_text(json.dumps(all_data, ensure_ascii=False, indent=2))
    print(f"  ✓ 全問題DB: {all_file} (合計{len(all_qs)}問, 今日{len(new_unique)}問追加)")

    # GitHub Gistに保存（任意）
    if GITHUB_TOKEN and GIST_ID:
        save_to_gist(all_data)


def save_to_gist(data: dict):
    """GitHub Gistにデータを保存する（オプション）"""
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "files": {
            "quiz_all.json": {"content": json.dumps(data, ensure_ascii=False, indent=2)}
        }
    }
    try:
        resp = requests.patch(
            f"https://api.github.com/gists/{GIST_ID}",
            headers=headers,
            json=payload,
            timeout=30
        )
        resp.raise_for_status()
        print(f"  ✓ GitHub Gistに保存: https://gist.github.com/{GIST_ID}")
    except Exception as e:
        print(f"  ✗ Gist保存エラー: {e}")


def main():
    print("=" * 50)
    print(f"🗞️ 時事クイズ自動生成 — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    # ステップ1: ニュース収集
    news = collect_news()

    # ステップ2: クイズ生成
    questions = generate_quiz_with_gemini(news)

    # ステップ3: 保存
    if questions:
        save_questions(questions)
        print("\n✅ 完了！")
    else:
        print("\n⚠️ 問題が生成されませんでした。")

    print("=" * 50)


if __name__ == "__main__":
    main()
