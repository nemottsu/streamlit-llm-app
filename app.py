from dotenv import load_dotenv

load_dotenv()

# app.py
# ───────────────────────────────────────────────
# OpenAI × LangChain × Streamlit チャットアプリ
# 専門家（野菜 / 果物 / 一般AI）切り替え機能付き
# ───────────────────────────────────────────────

# ── 必要なライブラリのインポート ───────────────────────
import os
# os.system("pip install streamlit==1.41.1 python-dotenv==1.0.0")
# os.system("pip install langchain==0.3.0 openai==1.47.0 langchain-community==0.3.0 langchain-openai==0.2.2 httpx==0.27.2")

from typing import Literal

import streamlit as st
from dotenv import load_dotenv

# LangChain関連
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage


# ── 初期設定 ───────────────────────────────────────
load_dotenv()  # .env から OPENAI_API_KEY を読み込む

st.set_page_config(
    page_title="専門家チャット（野菜 / 果物 / 一般）",
    page_icon="🥦",
    layout="centered"
)

# OpenAI API Key 確認
if not os.getenv("OPENAI_API_KEY"):
    st.error("環境変数 OPENAI_API_KEY が見つかりません。.env に設定してください。")
    st.stop()

# LLM（LangChain経由でOpenAIに接続）
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.5)


# ── 役割ごとのシステムプロンプト定義 ───────────────────────
SYSTEM_PROMPTS = {
    "一般的な質問に回答するAI": (
        "あなたは丁寧で誠実なアシスタントです。未知の点は正直に述べ、"
        "必要に応じて前提や制約を明確化し、簡潔に日本語で回答してください。"
    ),
    "野菜": (
        "あなたは野菜分野の専門家です。栽培・品種・栄養・保存・調理に関する最新知見を踏まえ、"
        "科学的根拠や実務的なコツを交えながら日本語で分かりやすく説明してください。"
    ),
    "果物": (
        "あなたは果物分野の専門家です。品種特性・旬・産地・追熟・保存・栄養・加工に関する知識を用い、"
        "根拠とともに日本語で明快に回答してください。"
    ),
}


# ── 分野関連語による簡易判定（「無関係なら一般AI」対応）──────────
VEG_KEYWORDS = {"野菜", "キャベツ", "にんじん", "トマト", "きゅうり", "ほうれん草", "ブロッコリー", "大根", "玉ねぎ", "レタス", "ナス"}
FRU_KEYWORDS = {"果物", "フルーツ", "リンゴ", "みかん", "オレンジ", "バナナ", "イチゴ", "ぶどう", "桃", "梨", "パイナップル", "マンゴー"}

def _looks_related_to(role: Literal["野菜", "果物"], text: str) -> bool:
    t = text.lower()
    if role == "野菜":
        return any(k in t for k in VEG_KEYWORDS)
    if role == "果物":
        return any(k in t for k in FRU_KEYWORDS)
    return True


# ── LLM応答関数（要件：入力テキストと選択値を引数に取る）────────────
def ask_llm(user_text: str, role: Literal["一般的な質問に回答するAI", "野菜", "果物"]) -> str:
    """
    入力テキストと役割に基づき、LLMからの回答を返す
    """
    # 無関係な質問は自動で「一般AI」に切り替え
    effective_role = role
    if role in ("野菜", "果物") and not _looks_related_to(role, user_text):
        effective_role = "一般的な質問に回答するAI"

    system_prompt = SYSTEM_PROMPTS[effective_role]

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_text),
    ]

    # LangChain サンプル準拠
    result = llm(messages)
    return result.content


# ── Streamlit UI 構築 ───────────────────────────────────────
st.title("🥦 家庭菜園チャット（野菜 / 果物 ）")
st.caption("LangChain × OpenAI × Streamlit / GitHub")

with st.expander("ℹ️ アプリの概要と使い方", expanded=True):
    st.markdown(
        """
### 🧭 このアプリについて
- OpenAIのLLMをLangChain経由で利用するチャットアプリです。
- 「野菜」「果物」の2種類の役割を選べます。
- 入力内容が分野に無関係な場合は、自動的に一般AIが回答します。

### 🧑‍💻 使い方
1. 回答役割をラジオボタンで選択  
2. 下の入力フォームに質問を入力  
3. 「送信」をクリック  
        """
    )

# 回答AIの選択
role = st.radio(
    "回答するAIの種類を選んでください：",
    # options=["一般的な質問に回答するAI", "野菜", "果物"],
    options=["野菜", "果物"],    
    index=0,
    horizontal=True,
)

# 入力フォーム
with st.form(key="chat_form", clear_on_submit=False):
    user_text = st.text_area(
        "質問を入力してください：",
        height=150,
        placeholder="例：キャベツの保存方法は？ / りんごの追熟は必要？ / Pythonのfor文の書き方は？ など",
    )
    submitted = st.form_submit_button("送信")

# 送信ボタン処理
if submitted:
    if not user_text.strip():
        st.warning("質問を入力してください。")
        st.stop()

    with st.spinner("回答を生成中..."):
        try:
            answer = ask_llm(user_text=user_text, role=role)
            st.markdown("---")
            st.markdown(f"**選択された役割：** `{role}`")
            st.markdown("#### 💬 回答")
            st.write(answer)
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

