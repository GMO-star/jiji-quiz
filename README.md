# 📰 時事早押しクイズ 自動生成システム

完全無料のサービスのみで構築する、時事クイズ自動生成・配信システムです。

---

## 🗂️ ファイル構成

```
your-repo/
├── jiji_quiz_app.html          # 早押しクイズWebアプリ（ブラウザで動く）
├── generate_quiz.py            # ニュース収集 + クイズ生成スクリプト
├── quiz_data/                  # 生成された問題JSON（自動生成）
│   ├── quiz_2025-05-14.json
│   └── quiz_all.json
└── .github/
    └── workflows/
        └── generate_quiz.yml   # GitHub Actions スケジューラ
```

---

## 🛠️ セットアップ手順

### ステップ 1 — 必要なアカウントを作成（全て無料）

| サービス | 用途 | 無料枠 |
|---|---|---|
| [GitHub](https://github.com) | コード管理 + 静的ホスティング + Actions | 2,000分/月のCI |
| [Google AI Studio](https://aistudio.google.com) | Gemini API（問題生成AI） | 15req/分、100万トークン/日 |
| （任意）[NewsAPI](https://newsapi.org) | 英語ニュース収集 | 100件/日 |

---

### ステップ 2 — Gemini API キーを取得

1. [aistudio.google.com](https://aistudio.google.com/app/apikey) にアクセス
2. 「APIキーを作成」をクリック
3. 表示されたキー（`AIza...`）をコピーして安全な場所に保存

---

### ステップ 3 — GitHub リポジトリを作成

```bash
# リポジトリを作成してファイルを配置
git init jiji-quiz
cd jiji-quiz
# ダウンロードしたファイルをすべてここにコピー
git add .
git commit -m "初期設定"
git remote add origin https://github.com/あなたのID/jiji-quiz.git
git push -u origin main
```

---

### ステップ 4 — GitHub Secrets にAPIキーを登録

リポジトリの **Settings → Secrets and variables → Actions → New repository secret**

| 名前 | 値 |
|---|---|
| `GEMINI_API_KEY` | Google AI Studioで取得したキー |
| `GIST_ID` | （任意）GitHub GistのID |

---

### ステップ 5 — GitHub Pages を有効化

リポジトリの **Settings → Pages**  
→ Source: `main` ブランチ、ルートディレクトリ (`/`)  
→ 保存すると `https://あなたのID.github.io/jiji-quiz/jiji_quiz_app.html` で公開

---

### ステップ 6 — スケジュール確認

`.github/workflows/generate_quiz.yml` の cron 設定：

```yaml
# 毎朝7時（JST）に自動実行
- cron: '0 22 * * *'   # UTC 22:00 = JST 07:00
```

変更したい場合は cron 式を書き換えてください：
- 毎朝6時: `0 21 * * *`
- 毎日12時と18時: `0 3,9 * * *`

---

## 💻 ローカルで実行する場合

```bash
# 依存パッケージをインストール
pip install feedparser requests

# APIキーを環境変数に設定
export GEMINI_API_KEY="AIza..."

# 実行
python generate_quiz.py

# cron で毎朝7時に自動実行（Macの場合）
# crontab -e で以下を追記：
# 0 7 * * * cd /path/to/jiji-quiz && python generate_quiz.py >> logs/quiz.log 2>&1
```

---

## 🎮 Webアプリの使い方

`jiji_quiz_app.html` をブラウザで開くと：

1. **APIキー入力**（任意）— Gemini APIキーを入力するとリアルタイム生成。未入力でもサンプル問題で動作確認できます
2. **カテゴリ選択** — 複数選択可
3. **スタート** — 10秒タイマーの早押しクイズ開始
4. **結果表示** — 正解数・スコア・解説を確認

### アプリをカスタマイズして問題DBを読み込む場合

`jiji_quiz_app.html` の `SAMPLE_QUESTIONS` の下に以下を追加：

```javascript
// generate_quiz.py で生成した問題DBを読み込む例
async function loadQuestionsFromDB() {
  const resp = await fetch('./quiz_data/quiz_all.json');
  const data = await resp.json();
  // ランダムに5問選ぶ
  const shuffled = data.questions.sort(() => Math.random() - 0.5);
  return shuffled.slice(0, 5);
}
```

---

## 📊 コスト試算（全て無料）

| サービス | 使用量（毎日1回実行時） | 無料枠 |
|---|---|---|
| Gemini 1.5 Flash | 約10,000トークン/日 | 100万トークン/日 |
| GitHub Actions | 約2分/日 = 60分/月 | 2,000分/月 |
| GitHub Pages | 静的ファイル配信 | 1GB/月 |

→ **全て無料枠内で運用可能**

---

## 🔧 トラブルシューティング

**Q: Gemini APIが429エラーになる**  
A: 無料枠のレート制限（15req/分）に当たっています。スクリプト内の `time.sleep(5)` を長くしてください。

**Q: RSSが取得できない**  
A: NHKのRSSは時々URL変更があります。`feedparser.parse(url)` でテストして確認してください。

**Q: GitHub Actionsが動かない**  
A: リポジトリの Settings → Actions → General → Workflow permissions で「Read and write permissions」を有効化してください。
