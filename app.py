import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. 網頁設定 (加入 layout="centered" 讓手機版更好看)
st.set_page_config(page_title="Honyen 的新潟之旅", layout="centered", page_icon="🇯🇵")

# 2. 設定 API Key (從 Secrets 拿鑰匙，安全！)
# 如果在本機執行沒設 secrets，請暫時換回 genai.configure(api_key="你的KEY")
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("找不到 API Key，請檢查 Secrets 設定。")

# 3. 初始化模型
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 介面設計 ---
st.title("🇯🇵 Honyen 的隨身翻譯導遊")

# 4. 建立分頁 (Tabs) - 這是 V4.0 的核心設計
tab1, tab2 = st.tabs(["💬 旅遊諮詢", "🗣️ 中日翻譯 (給對方看)"])

# --- 分頁 1: 原本的導遊功能 ---
with tab1:
    st.caption("拍這什麼？怎麼去？行程怎麼排？問我就對了！")
    
    # 照片上傳區
    with st.expander("📸 上傳照片 (菜單/景點/商品)"):
        uploaded_file = st.file_uploader("請選擇照片...", type=["jpg", "jpeg", "png"], key="guide_upload")
        image = None
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption='已上傳', width=300)

    # 聊天紀錄初始化
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 顯示歷史訊息
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 導遊的 System Prompt
    guide_prompt = """
    你是一位精通日本新潟旅遊的台灣導遊 Honyen。
    1. 用繁體中文回答，語氣熱情。
    2. 遇到專有名詞請標註日文。
    3. 導航請提供 Google Maps 連結。
    4. 搜尋請提供 Google Search 連結。
    """

    # 導遊輸入框
    if user_input := st.chat_input("請輸入問題 (例如：新潟有什麼伴手禮？)"):
        st.chat_message("user").markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # 組合歷史對話
        history_context = "歷史對話：\n" + "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[:-1]])
        full_prompt = guide_prompt + "\n" + history_context + "\n使用者問題：" + user_input

        with st.chat_message("assistant"):
            with st.spinner("導遊查詢中..."):
                try:
                    if image:
                        response = model.generate_content([full_prompt, image])
                    else:
                        response = model.generate_content(full_prompt)
                    
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"發生錯誤：{e}")


# --- 分頁 2: 翻譯蒟蒻 (新功能！) ---
with tab2:
    st.header("🗣️ 雙向溝通板")
    st.info("輸入中文，我會變出超大日文給店員看！")

    # 翻譯模式選擇
    trans_mode = st.radio("模式", ["中翻日 (我問店員)", "日翻中 (店員說什麼)"], horizontal=True)

    # 翻譯輸入框 (使用 text_area 比較好輸入長句)
    trans_input = st.text_area("請輸入文字：", height=100, placeholder="例如：我想買去佐渡島的船票，兩張大人。")

    if st.button("✨ 開始翻譯", use_container_width=True):
        if trans_input:
            with st.spinner("翻譯中..."):
                try:
                    if trans_mode == "中翻日 (我問店員)":
                        # 這是給店員看的 Prompt
                        t_prompt = f"""
                        請將以下中文翻譯成自然、有禮貌的日文（適合對店員或路人說）。
                        1. 【重要】請直接輸出日文，不要有任何解釋。
                        2. 在日文下方，提供羅馬拼音 (Romaji)，讓使用者可以試著唸出來。
                        3. 中文原文：{trans_input}
                        """
                        res = model.generate_content(t_prompt)
                        
                        # 顯示結果：用超大字體顯示日文
                        st.markdown("### 🇯🇵 請拿給對方看：")
                        st.success(res.text) # 綠色框框醒目顯示
                        
                    else: # 日翻中
                        # 這是店員回覆的 Prompt
                        t_prompt = f"""
                        請將以下日文翻譯成繁體中文。
                        日文原文：{trans_input}
                        """
                        res = model.generate_content(t_prompt)
                        st.markdown("### 🇹🇼 對方的意思是：")
                        st.info(res.text)

                except Exception as e:
                    st.error("翻譯失敗，請稍後再試。")

    st.markdown("---")
    # 緊急備案：Google 翻譯傳送門
    st.markdown("🚨 如果真的溝通不良，請按這裡開啟 Google 翻譯：")
    st.markdown("[Google 翻譯 (語音對話模式)](https://translate.google.com/?sl=ja&tl=zh-TW&op=translate)", unsafe_allow_html=True)