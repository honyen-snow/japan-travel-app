import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. 設定網頁設定 (這行要放最上面) - 讓網頁變成寬螢幕模式
st.set_page_config(page_title="Honyen 的日本導遊", layout="wide")

# 2. 設定 API Key
genai.configure(api_key="AIzaSyAShdl2lc8v7P8v1MfqYBcLnzovp3Sdi2Q")

# 3. 定義大腦與人設 (修正了地圖連結格式)
sys_prompt = """
你是一位精通日本旅遊的台灣籍導遊 Honyen。
1. 你的任務是介紹日本景點、美食，並解決交通問題。
2. 【重要】無論使用者問什麼，或者參考資料是什麼語言，你一律必須使用「繁體中文 (Traditional Chinese)」回答。
3. 如果遇到專有名詞（如地名、菜名），請用「繁體中文 (日文)」的格式呈現。
4. 語氣要熱情、專業，對長輩友善。

5. 【導航專家模式】當使用者詢問「怎麼去...」或「導航到...」時：
   - 請幫他規劃簡單的交通建議。
   - 【關鍵】最後一定要提供一個 Google Maps 連結，格式如下(請完全照抄，不要自己發明)：
     https://www.google.com/maps/dir/?api=1&destination={目的地}&travelmode=transit
   - 如果使用者有指定「起點」，請在網址加上 &origin={起點}。
   - 如果使用者是說「從這裡」、「我現在位置」，則網址【不要】加 origin 參數 (這樣地圖會自動抓 GPS)。
   - 請將連結包裝成 Markdown，例如： 🗺️ [點擊這裡開啟 Google Maps 導航](網址)
"""

model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=sys_prompt)

# --- 介面設計開始 ---

# 4. 側邊欄 (Sidebar)
with st.sidebar:
    st.header("📸 隨身翻譯機")
    st.write("上傳菜單、路標或景點照片")
    uploaded_file = st.file_uploader("選擇照片...", type=["jpg", "jpeg", "png"])
    
    image = None
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='已上傳', use_container_width=True)

# 5. 主畫面 (Main)
st.title("🇯🇵 Honyen 的日本旅遊 AI 助理")
st.caption("我是你的專屬導遊，不管是問路、翻譯菜單還是排行程，問我就對了！")

# 建立對話框
user_input = st.text_input("請問你有什麼日本旅遊的問題？")

# 按鈕邏輯
if user_input:
    with st.spinner("導遊正在思考中..."):
        try:
            if image:
                response = model.generate_content([user_input, image])
            else:
                response = model.generate_content(user_input)
            
            st.markdown("### 🤖 導遊建議：")
            st.write(response.text)
            
        except Exception as e:
            st.error(f"發生錯誤：{e}")