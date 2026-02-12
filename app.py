import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. 網頁設定
st.set_page_config(page_title="Honyen 的日本導遊", layout="wide")

# 2. 設定 API Key
genai.configure(api_key="AIzaSyAShdl2lc8v7P8v1MfqYBcLnzovp3Sdi2Q")

# 3. 定義導遊大腦 (包含 Google 搜尋與導航功能)
sys_prompt = """
你是一位精通日本旅遊的台灣籍導遊 Honyen。
1. 你的任務是介紹日本景點、美食，並解決交通問題。
2. 【重要】一律使用「繁體中文」回答。
3. 遇到專有名詞請標註日文，例如：越光米 (コシヒカリ)。
4. 語氣熱情、專業。

5. 【導航專家模式】當使用者問路時：
   - 提供 Google Maps 連結：http://googleusercontent.com/maps.google.com/maps?daddr={目的地}&travelmode=transit
   - 包裝成 Markdown：🗺️ [點擊這裡開啟 Google Maps 導航](網址)

6. 【搜尋小幫手】當需要時刻表或官網時：
   - 請提供 Google 搜尋連結：https://www.google.com/search?q={關鍵字}
   - 包裝成 Markdown：🔍 [點擊搜尋相關資訊](網址)
"""

model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=sys_prompt)

# --- 介面設計開始 ---

st.title("🇯🇵 Honyen 的日本旅遊 AI 助理")
st.caption("我是你的專屬導遊，請直接在下方輸入問題，或是按手機鍵盤麥克風語音輸入！")

# 4. 【改良】照片上傳區移到主畫面 (手機更容易按)
with st.expander("📸 上傳照片 (點擊這裡展開/收合)"):
    uploaded_file = st.file_uploader("請選擇照片...", type=["jpg", "jpeg", "png"])
    image = None
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='已上傳的照片', width=300) # 手機版限制寬度比較好看

# 5. 初始化聊天紀錄
if "messages" not in st.session_state:
    st.session_state.messages = []

# 6. 顯示過去的對話紀錄
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. 聊天輸入框邏輯
if user_input := st.chat_input("請輸入問題..."):
    
    # 步驟 A: 顯示使用者的話
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 步驟 B: 【關鍵修復】把過去的對話組裝成「記憶包裹」
    # 我們把之前的對話串成一個長字串，讓 AI 讀過再回答
    history_context = "這是我們之前的對話紀錄，請參考上下文回答：\n"
    for msg in st.session_state.messages[:-1]: # 排除最新的一句，避免重複
        role_name = "使用者" if msg["role"] == "user" else "導遊"
        history_context += f"{role_name}: {msg['content']}\n"
    
    # 組合最終的提示詞 (Prompt)
    full_prompt = history_context + "\n使用者現在的問題：" + user_input

    # 步驟 C: 呼叫 AI 回答
    with st.chat_message("assistant"):
        with st.spinner("導遊正在回憶並思考中..."):
            try:
                # 判斷有沒有照片 (有照片時，同時傳送照片 + 附帶記憶的文字)
                if image:
                    response = model.generate_content([full_prompt, image])
                else:
                    response = model.generate_content(full_prompt)
                
                st.markdown(response.text)
                
                # 步驟 D: 把 AI 的話存進記憶
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"發生錯誤：{e}")