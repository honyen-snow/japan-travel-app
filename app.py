import streamlit as st
import google.generativeai as genai
from PIL import Image
import streamlit.components.v1 as components

# --- 1. 網頁設定 (必須在最前面) ---
st.set_page_config(page_title="日本旅遊指揮中心", layout="wide", page_icon="🎌")

# --- 🔒 親友通關密碼鎖 ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 日本 AI 導遊")
    password = st.text_input("請輸入通關密碼：", type="password")
    if st.button("登入"):
        if password == "japan2026":  # 設定你的密碼
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("密碼錯誤")
    st.stop()

# --- 2. API 設定 ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("找不到 API Key")

model = genai.GenerativeModel('gemini-2.0-flash-lite-001')

# --- 3. 定義全日本資料庫 (城市 + 天氣代碼 + 對應的鐵路公司) ---
# 這是 V7.0 的核心大腦
city_db = {
    "新潟 (Niigata)": {
        "weather_url": "https://forecast7.com/zh-tw/37d92139d04/niigata/",
        "rail_name": "🚄 JR 東日本訂票 (新潟/東京)",
        "rail_url": "https://www.eki-net.com/jreast-train-reservation/Top/Index"
    },
    "東京 (Tokyo)": {
        "weather_url": "https://forecast7.com/zh-tw/35d69139d69/tokyo/",
        "rail_name": "🚄 JR 東日本訂票 (成田/東京)",
        "rail_url": "https://www.eki-net.com/jreast-train-reservation/Top/Index"
    },
    "大阪 (Osaka)": {
        "weather_url": "https://forecast7.com/zh-tw/34d69135d50/osaka/",
        "rail_name": "🚄 JR 西日本訂票 (關西機場/大阪)",
        "rail_url": "https://www.westjr.co.jp/global/tc/ticket/"
    },
    "京都 (Kyoto)": {
        "weather_url": "https://forecast7.com/zh-tw/35d01135d76/kyoto/",
        "rail_name": "🚄 JR 西日本訂票 (京都/大阪)",
        "rail_url": "https://www.westjr.co.jp/global/tc/ticket/"
    },
    "北海道-札幌": {
        "weather_url": "https://forecast7.com/zh-tw/43d06141d35/sapporo/",
        "rail_name": "🚄 JR 北海道訂票",
        "rail_url": "https://www.jrhokkaido.co.jp/global/chinese/index.html"
    },
    "福岡 (Fukuoka)": {
        "weather_url": "https://forecast7.com/zh-tw/33d59130d40/fukuoka/",
        "rail_name": "🚄 JR 九州訂票",
        "rail_url": "https://www.jrkyushu.co.jp/chinese/"
    },
    "沖繩-那霸": {
        "weather_url": "https://forecast7.com/zh-tw/26d21127d68/naha/",
        "rail_name": "🚝 沖繩單軌電車",
        "rail_url": "https://www.yui-rail.co.jp/tc/"
    }
}

# --- 側邊欄：動態情報局 ---
with st.sidebar:
    st.header("📍 設定您的位置")
    
    # A. 城市選擇器
    selected_city = st.selectbox("目前在哪裡旅遊？", list(city_db.keys()))
    
    # 根據選擇，抓出資料
    current_info = city_db[selected_city]
    
    # B. 顯示動態天氣
    st.caption(f"🌤️ {selected_city} 天氣")
    weather_html = f"""
    <a class="weatherwidget-io" href="{current_info['weather_url']}" data-label_1="{selected_city}" data-label_2="天氣預報" data-theme="pure" >天氣預報</a>
    <script>
    !function(d,s,id){{var js,fjs=d.getElementsByTagName(s)[0];if(!d.getElementById(id)){{js=d.createElement(s);js.id=id;js.src='https://weatherwidget.io/js/widget.min.js';fjs.parentNode.insertBefore(js,fjs);}}}}(document,'script','weatherwidget-io-js');
    </script>
    """
    components.html(weather_html, height=110)
    
    st.divider()
    
    st.header("🚦 交通與入境")
    
    # C. 智慧鐵路連結 (會根據城市自動變！)
    st.link_button(current_info['rail_name'], current_info['rail_url'])
    st.link_button("📝 Visit Japan Web (入境填寫)", "https://vjw-lp.digital.go.jp/zh-hant/")
    
    st.divider()
    
    # D. 機場切換器 (桃園 vs 松山)
    st.header("✈️ 航班查詢")
    airport_choice = st.radio("出發/抵達機場", ["🛫 桃園 (TPE)", "🛫 松山 (TSA)"], horizontal=True)
    
    col_air1, col_air2 = st.columns(2)
    
    if "桃園" in airport_choice:
        with col_air1:
            st.link_button("桃機出發", "https://www.taoyuan-airport.com/flight_depart")
        with col_air2:
            st.link_button("桃機抵達", "https://www.taoyuan-airport.com/flight_arrival")
    else:
        # 松山機場連結
        with col_air1:
            st.link_button("松山出發", "https://www.tsa.gov.tw/flight/index/zh-tw?type=departure")
        with col_air2:
            st.link_button("松山抵達", "https://www.tsa.gov.tw/flight/index/zh-tw?type=arrival")

# --- 主畫面 (維持原樣) ---
st.title(f"🎌 AI 日之旅導遊 - {selected_city}篇") # 標題也會跟著變喔！

# 建立分頁
tab1, tab2, tab3 = st.tabs(["💬 AI 導遊", "🗣️ 翻譯蒟蒻", "💰 敗家計算機"])

# === 分頁 1: AI 導遊 ===
with tab1:
    with st.expander("📸 上傳照片問問題"):
        uploaded_file = st.file_uploader("請選擇照片...", type=["jpg", "jpeg", "png"])
        image = None
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, width=300)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 這裡把 sys_prompt 改成更通用的版本
    sys_prompt = f"""
    你是一位精通日本全境旅遊的台灣導遊 Honyen。
    目前使用者正在「{selected_city}」旅遊。
    1. 請優先提供該城市的旅遊資訊，但若使用者問其他地方也能回答。
    2. 用繁體中文回答，語氣熱情。
    3. 遇到專有名詞請標註日文。
    4. 導航請提供 Google Maps 連結。
    """

    if user_input := st.chat_input("請輸入問題..."):
        st.chat_message("user").markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        full_prompt = sys_prompt + "\n歷史對話:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[:-1]]) + "\n使用者問題：" + user_input

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

# === 分頁 2 & 3 (翻譯與計算機，邏輯不變，直接保留即可) ===
with tab2:
    st.header("🗣️ 雙向溝通板")
    trans_mode = st.radio("模式", ["中翻日 (我問店員)", "日翻中 (店員說什麼)"], horizontal=True)
    trans_input = st.text_area("輸入文字：", height=100)
    if st.button("✨ 翻譯", use_container_width=True):
        if trans_input:
            with st.spinner("翻譯中..."):
                if "中翻日" in trans_mode:
                    res = model.generate_content(f"把這句中文翻成禮貌日文，附羅馬拼音：{trans_input}")
                    st.success(res.text)
                else:
                    res = model.generate_content(f"把這句日文翻成繁體中文：{trans_input}")
                    st.info(res.text)

with tab3:
    st.header("💰 匯率換算")
    col1, col2 = st.columns(2)
    with col1:
        jpy = st.number_input("日幣 (¥)", step=100)
    with col2:
        rate = st.number_input("匯率", value=0.22)
    st.metric("台幣 (TWD)", f"${int(jpy*rate)}")
    
    st.divider()
    item_name = st.text_input("商品名稱 (分析 CP 值用)")
    if st.button("分析 CP 值"):
        if item_name and jpy > 0:
            with st.spinner("分析中..."):
                res = model.generate_content(f"在日本買{item_name}價格日幣{jpy}，匯率{rate}，請問划算嗎？給建議。")
                st.write(res.text)