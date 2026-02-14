import streamlit as st
import google.generativeai as genai
from PIL import Image
import streamlit.components.v1 as components # 引入新元件，用來嵌入 HTML

# 1. 網頁設定
st.set_page_config(page_title="Honyen 的新潟指揮中心", layout="wide", page_icon="🎌")

# 2. 設定 API Key
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("找不到 API Key，請檢查 Secrets 設定。")

model = genai.GenerativeModel('gemini-2.5-flash')

# --- 側邊欄：旅遊情報局 (V5.2: 全新天氣小工具) ---
with st.sidebar:
    st.header("🌦️ 新潟天氣現況")
    
    # 【V5.2 新功能】嵌入 WeatherWidget.io 的 HTML 程式碼
    # 這會顯示一個漂亮、白底、有圖示和溫度的天氣小卡片
    weather_widget_html = """
    <a class="weatherwidget-io" href="https://forecast7.com/zh-tw/37d92139d04/niigata/" data-label_1="NIIGATA" data-label_2="天氣預報" data-theme="pure" >NIIGATA 天氣預報</a>
    <script>
    !function(d,s,id){var js,fjs=d.getElementsByTagName(s)[0];if(!d.getElementById(id)){js=d.createElement(s);js.id=id;js.src='https://weatherwidget.io/js/widget.min.js';fjs.parentNode.insertBefore(js,fjs);}}(document,'script','weatherwidget-io-js');
    </script>
    """
    # 使用 components.html 來渲染這段 HTML，設定高度為 110px
    components.html(weather_widget_html, height=110)
    
    st.divider()
    
    st.header("✈️ 必備傳送門")
    st.link_button("📝 Visit Japan Web (入境填寫)", "https://vjw-lp.digital.go.jp/zh-hant/")
    st.link_button("🚄 JR 東日本訂票 (Global)", "https://www.eki-net.com/jreast-train-reservation/Top/Index")
    
    col_air1, col_air2 = st.columns(2)
    with col_air1:
        st.link_button("🛫 桃機出發", "https://www.taoyuan-airport.com/flight_depart")
    with col_air2:
        st.link_button("🛬 桃機抵達", "https://www.taoyuan-airport.com/flight_arrival")

# --- 主畫面 ---
st.title("🎌 Honyen 的全能領隊")

# 建立三個分頁
tab1, tab2, tab3 = st.tabs(["💬 AI 導遊", "🗣️ 翻譯蒟蒻", "💰 敗家計算機"])

# === 分頁 1: AI 導遊 (維持原樣) ===
with tab1:
    st.caption("行程規劃、景點介紹、交通查詢")
    
    with st.expander("📸 上傳照片問問題"):
        uploaded_file = st.file_uploader("請選擇照片...", type=["jpg", "jpeg", "png"], key="guide_upload")
        image = None
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, width=300)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 導遊 Prompt
    guide_prompt = """
    你是一位精通日本新潟旅遊的台灣導遊 Honyen。
    1. 用繁體中文回答，語氣熱情。
    2. 遇到專有名詞請標註日文。
    3. 導航請提供 Google Maps 連結。
    4. 搜尋請提供 Google Search 連結。
    5. 若使用者詢問入境規定，請提醒他們去側邊欄使用 Visit Japan Web。
    """

    if user_input := st.chat_input("請輸入問題..."):
        st.chat_message("user").markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        history_context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[:-1]])
        full_prompt = guide_prompt + "\n歷史對話:\n" + history_context + "\n使用者問題：" + user_input

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

# === 分頁 2: 翻譯蒟蒻 (維持原樣) ===
with tab2:
    st.header("🗣️ 雙向溝通板")
    trans_mode = st.radio("模式", ["中翻日 (我問店員)", "日翻中 (店員說什麼)"], horizontal=True)
    trans_input = st.text_area("輸入文字：", height=100)
    
    if st.button("✨ 翻譯", use_container_width=True):
        if trans_input:
            with st.spinner("翻譯中..."):
                if trans_mode == "中翻日 (我問店員)":
                    prompt = f"把這句中文翻成禮貌日文，並附上羅馬拼音，只給結果：{trans_input}"
                    res = model.generate_content(prompt)
                    st.success(res.text)
                else:
                    prompt = f"把這句日文翻成繁體中文：{trans_input}"
                    res = model.generate_content(prompt)
                    st.info(res.text)

# === 分頁 3: 敗家計算機 (維持原樣) ===
with tab3:
    st.header("💰 匯率換算 & 購物分析")
    
    col1, col2 = st.columns(2)
    with col1:
        jpy_amount = st.number_input("日幣金額 (¥)", min_value=0, step=100)
    with col2:
        rate = st.number_input("目前匯率", value=0.22, format="%.3f")
    
    twd_amount = int(jpy_amount * rate)
    
    st.metric(label="約合台幣 (TWD)", value=f"${twd_amount}")
    
    st.markdown("---")
    st.subheader("🤔 這樣買划算嗎？")
    item_name = st.text_input("商品名稱 (例如：Dyson 吹風機、越光米 5kg)", placeholder="輸入商品名稱問 AI...")
    
    if st.button("幫我分析 CP 值", type="primary"):
        if item_name and jpy_amount > 0:
            with st.spinner("AI 正在比價分析中..."):
                price_prompt = f"""
                使用者想在新潟買「{item_name}」，價格是日幣 {jpy_amount} 円。
                請幫忙分析：
                1. 換算台幣約 {twd_amount} 元。
                2. 這個價格跟台灣大概的售價比起來，有便宜嗎？(請根據你的知識庫預估)
                3. 值不值得在日本買？(考量電壓、保固或攜帶方便性)
                4. 給出一個簡短的購買建議（買爆 / 再考慮 / 台灣買就好）。
                """
                analysis = model.generate_content(price_prompt)
                st.write(analysis.text)
        else:
            st.warning("請輸入金額和商品名稱喔！")