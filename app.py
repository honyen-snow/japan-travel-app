import streamlit as st
import google.generativeai as genai
from PIL import Image
import streamlit.components.v1 as components

# --- 1. 網頁設定 ---
st.set_page_config(page_title="日本旅遊指揮中心", layout="wide", page_icon="🎌")

# --- 🔒 密碼鎖 ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 日之旅 AI 導遊")
    password = st.text_input("請輸入通關密碼：", type="password")
    if st.button("登入"):
        # 你的密碼
        if password == "japan2026": 
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

# 使用 1.5 Flash (目前額度最穩) 或 2.5-flash
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 3. 定義全日本資料庫 ---
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

# --- 側邊欄 ---
with st.sidebar:
    st.header("📍 設定您的位置")
    selected_city = st.selectbox("目前在哪裡旅遊？", list(city_db.keys()))
    current_info = city_db[selected_city]
    
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
    st.link_button(current_info['rail_name'], current_info['rail_url'])
    st.link_button("📝 Visit Japan Web", "https://vjw-lp.digital.go.jp/zh-hant/")
    st.divider()
    st.header("✈️ 航班查詢")
    airport_choice = st.radio("出發/抵達機場", ["🛫 桃園 (TPE)", "🛫 松山 (TSA)"], horizontal=True)
    col_air1, col_air2 = st.columns(2)
    if "桃園" in airport_choice:
        with col_air1: st.link_button("桃機出發", "https://www.taoyuan-airport.com/flight_depart")
        with col_air2: st.link_button("桃機抵達", "https://www.taoyuan-airport.com/flight_arrival")
    else:
        with col_air1: st.link_button("松山出發", "https://www.tsa.gov.tw/flight/index/zh-tw?type=departure")
        with col_air2: st.link_button("松山抵達", "https://www.tsa.gov.tw/flight/index/zh-tw?type=arrival")

# --- 主畫面 ---
st.title(f"🎌 AI 日之旅導遊 - {selected_city}篇")

tab1, tab2, tab3 = st.tabs(["💬 AI 導遊", "🗣️ 翻譯蒟蒻", "💰 敗家計算機"])

# === 分頁 1: AI 導遊 (腦袋升級，找回地圖) ===
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

    # 【重要修正】把「導航請提供 Google Maps 連結」這句話加回來了！
    sys_prompt = f"""
    你是一位精通日本全境旅遊的台灣導遊 Honyen。
    目前使用者正在「{selected_city}」旅遊。
    1. 用繁體中文回答，語氣熱情。
    2. 遇到專有名詞請標註日文。
    3. 導航請務必提供 Google Maps 連結，方便使用者點擊。
    4. 搜尋請提供 Google Search 連結。
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

# === 分頁 2: 翻譯蒟蒻 (移除清除按鈕，保留切換清空) ===
with tab2:
    st.header("🗣️ 雙向溝通板")
    
    if "trans_history" not in st.session_state:
        st.session_state.trans_history = ""
    if "trans_input_text" not in st.session_state:
        st.session_state.trans_input_text = ""

    # 清空函數
    def clear_text():
        st.session_state.trans_input_text = ""

    # 選擇模式 (切換時自動清空)
    trans_mode = st.radio(
        "模式", 
        ["中翻日 (我問店員)", "日翻中 (店員說什麼)"], 
        horizontal=True,
        on_change=clear_text
    )

    # 輸入框 (移除了右邊的清除按鈕，改為全寬)
    trans_input = st.text_area("輸入文字：", height=100, key="trans_input_text")

    if st.button("✨ 翻譯", use_container_width=True, type="primary"):
        if trans_input:
            with st.spinner("翻譯中..."):
                if "中翻日" in trans_mode:
                    res = model.generate_content(f"把這句中文翻成禮貌日文，附羅馬拼音：{trans_input}")
                    st.session_state.trans_history = res.text 
                else:
                    res = model.generate_content(f"把這句日文翻成繁體中文：{trans_input}")
                    st.session_state.trans_history = res.text 
    
    # 顯示結果
    if st.session_state.trans_history:
        st.info(st.session_state.trans_history)


# === 分頁 3: 敗家計算機 (修正歸零報錯問題) ===
with tab3:
    st.header("💰 匯率換算")
    
    if "price_input" not in st.session_state:
        st.session_state.price_input = 0.0

    # 定義歸零的回調函數 (解決報錯的關鍵！)
    def reset_price():
        st.session_state.price_input = 0.0

    col_rate1, col_rate2 = st.columns([3, 1])
    with col_rate1:
        rate = st.number_input("目前匯率 (可手動調整)", value=0.22, format="%.3f", step=0.001)

    st.divider()

    col_p1, col_p2 = st.columns([4, 1]) 
    with col_p1:
        jpy = st.number_input(
            "日幣金額 (¥)", 
            min_value=0.0, 
            step=100.0, 
            key="price_input"
        )
    with col_p2:
        st.write("") 
        st.write("") 
        # 這裡改成用 on_click 來執行歸零，這樣就不會報錯了！
        st.button("❌ 歸零", on_click=reset_price)

    twd_amount = int(jpy * rate)
    st.metric("約合台幣 (TWD)", f"${twd_amount}")
    
    st.divider()
    item_name = st.text_input("商品名稱 (分析 CP 值用)")
    if st.button("分析 CP 值"):
        if item_name and jpy > 0:
            with st.spinner("AI 分析中..."):
                res = model.generate_content(f"在日本買{item_name}價格日幣{jpy}，匯率{rate}，請問划算嗎？請用台灣人的角度分析 CP 值。")
                st.write(res.text)