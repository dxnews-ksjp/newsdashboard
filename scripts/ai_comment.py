"""キャラクターの吹き出しに入れる「今朝のニュースまとめ」を Claude に書いてもらう。

・環境変数 ANTHROPIC_API_KEY（GitHub の Secrets に登録）があるときだけ Claude を呼び出します。
・キーがない／エラーが起きたときは、決まったあいさつ文を返します（ページの作成は止めません）。
"""

import os
import sys

MODEL = "claude-opus-5-5"

# キーが未設定・AIの呼び出しに失敗したときに表示する文
FALLBACK_COMMENT = "おはよう！今朝のニュースを届けに来たよ！気になる記事をチェックしてね！"

SYSTEM_PROMPT = """\
あなたはニュースサイト「今朝のニュース」のマスコットキャラクターです。
帽子をかぶった白い鳥の配達員で、毎朝ニュースを届けています。
読者は倉庫・港湾運送・国際輸送・不動産などを手がける会社で働く人です。

渡されたニュース見出しの一覧をもとに、今朝のニュースのまとめを書いてください。
（見出しは「## タブ名」「### トピック名」の下に並んでいます）

書き方のルール：
・2〜3文、合計120文字程度の日本語で書く
・「〜だよ！」「〜みたい！」のような、くだけた親しみやすい口調にする
・見出しにない事実や数字を付け足さない。見出しから読み取れることだけを書く
・特に目立つ話題を2〜3個選んで触れる（全部を紹介しなくてよい）
・マークダウン、箇条書き、絵文字、見出しは使わない
・まとめの本文だけを出力する（前置きや「まとめ：」などのラベルは付けない）
"""


def build_headline_text(headlines_by_tab):
    """{タブ名: {トピック名: [見出し, ...]}} を、Claude に渡す文章にする。"""
    lines = []
    for tab, topics in headlines_by_tab.items():
        lines.append(f"## {tab}")
        for topic, titles in topics.items():
            lines.append(f"### {topic}")
            lines.extend(f"- {t}" for t in titles)
    return "\n".join(lines)


def generate_comment(headlines_by_tab):
    if not any(headlines_by_tab.values()):
        print("[AI] まとめる見出しがないため、決まったあいさつ文を表示します")
        return FALLBACK_COMMENT, False
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[AI] ANTHROPIC_API_KEY が未設定のため、決まったあいさつ文を表示します")
        return FALLBACK_COMMENT, False

    try:
        import anthropic
    except ImportError:
        print("[AI] anthropic パッケージが見つからないため、決まったあいさつ文を表示します", file=sys.stderr)
        return FALLBACK_COMMENT, False

    client = anthropic.Anthropic()
    try:
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            output_config={"effort": "low"},
            # 安全上の理由で断られた場合は、サーバー側で別のモデルが代わりに答える
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{
                "role": "user",
                "content": "今朝のニュース見出しです。\n\n" + build_headline_text(headlines_by_tab),
            }],
        )
    except anthropic.AuthenticationError:
        print("[AI] APIキーが正しくありません（Secrets の ANTHROPIC_API_KEY を確認してください）", file=sys.stderr)
        return FALLBACK_COMMENT, False
    except anthropic.PermissionDeniedError:
        print("[AI] APIキーにこのモデルを使う権限がありません", file=sys.stderr)
        return FALLBACK_COMMENT, False
    except anthropic.RateLimitError:
        print("[AI] 利用上限に達しました（クレジット残高や利用制限を確認してください）", file=sys.stderr)
        return FALLBACK_COMMENT, False
    except anthropic.APIStatusError as e:
        print(f"[AI] APIエラー ({e.status_code}): {e.message}", file=sys.stderr)
        return FALLBACK_COMMENT, False
    except anthropic.APIConnectionError:
        print("[AI] Claude に接続できませんでした", file=sys.stderr)
        return FALLBACK_COMMENT, False

    if response.stop_reason == "refusal":
        print("[AI] コメントの作成を断られたため、決まったあいさつ文を表示します", file=sys.stderr)
        return FALLBACK_COMMENT, False

    text = "".join(b.text for b in response.content if b.type == "text").strip()
    if not text:
        print("[AI] コメントが空だったため、決まったあいさつ文を表示します", file=sys.stderr)
        return FALLBACK_COMMENT, False

    print(f"[AI] コメントを作成しました（{len(text)}文字）")
    return text, True
