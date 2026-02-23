import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
import streamlit.components.v1 as components
import json
import os
from datetime import datetime
import uuid
import pandas as pd
import gspread

# ==========================================
# 🗂️ 雲端永動資料庫設定 (Google Sheets)
# ==========================================
# 👇 務必把下方雙引號內的網址，換成您真正的試算表網址！
SHEET_URL = "https://docs.google.com/spreadsheets/d/1R8ZORgO0htQtmrb2PVb7AtpP6PdiVZDiHe0JZYZlnwY/edit?gid=0#gid=0"

sa_info = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
gc = gspread.service_account_from_dict(sa_info)
sh = gc.open_by_url(SHEET_URL)
worksheet = sh.get_worksheet(0)

IMAGE_DIR = "japan_images"
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# --- CRUD: [R] 讀取 ---
def load_memories():
    try:
        records = worksheet.get_all_records()
        if not records:
            return []
        df = pd.DataFrame(records)
        memories = []
        for _, row in df.iterrows():
            collabs_str = str(row.get("collaborations", "[]"))
            try:
                collabs = json.loads(collabs_str) if collabs_str != "nan" and collabs_str else []
            except:
                collabs = []
            
            memories.append({
                "id": str(row.get("id", "")),
                "time": str(row.get("time", "")),
                "original": str(row.get("original", "")),
                "generated": str(row.get("generated", "")),
                "image": str(row.get("image", "")),
                "collaborations": collabs
            })
        return memories
    except Exception as e:
        st.error(f"連線 Google 試算表失敗：{e}")
        return []

# --- CRUD: [C] 新增 ---
def save_memory(original_text, generated_text, img_path=""):
    memories = load_memories()
    new_story = {
        "id": str(uuid.uuid4()),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "original": original_text,
        "generated": generated_text,
        "image": img_path,
        "collaborations": [] 
    }
    memories.append(new_story)
    
    df_to_save = pd.DataFrame(memories)
    df_to_save["collaborations"] = df_to_save["collaborations"].apply(json.dumps)
    
    data = [df_to_save.columns.values.tolist()] + df_to_save.values.tolist()
    worksheet.clear()
    worksheet.update(data)

# --- CRUD: [U] 更新 (補圖) ---
def update_memory_image(story_id, img_path):
    memories = load_memories()
    for memory in memories:
        if memory["id"] == story_id:
            memory["image"] = img_path
            break
            
    df_to_save = pd.DataFrame(memories)
    df_to_save["collaborations"] = df_to_save["collaborations"].apply(json.dumps)
    
    data = [df_to_save.columns.values.tolist()] + df_to_save.values.tolist()
    worksheet.clear()
    worksheet.update(data)

# --- CRUD: [U] 更新 (留言) ---
def add_collaboration(story_id, author_name, collaboration_text):
    memories = load_memories()
    for memory in memories:
        if memory["id"] == story_id:
            new_collab = {
                "author": author_name,
                "text": collaboration_text,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            memory["collaborations"].append(new_collab)
            break
            
    df_to_save = pd.DataFrame(memories)
    df_to_save["collaborations"] = df_to_save["collaborations"].apply(json.dumps)
    
    data = [df_to_save.columns.values.tolist()] + df_to_save.values.tolist()
    worksheet.clear()
    worksheet.update(data)

# 🌟 拼圖的最後一塊：CRUD: [D] 刪除
def delete_memory(story_id):
    memories = load_memories()
    updated_memories = []
    
    for m in memories:
        if m["id"] == story_id:
            # 如果這篇文章有照片，順便把硬碟裡的實體照片刪掉，節省空間！
            img_path = m.get("image", "")
            if img_path and os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except:
                    pass
        else:
            updated_memories.append(m)
            
    # 如果刪到一篇都不剩，要給個空表頭，不然會出錯
    if not updated_memories:
        worksheet.clear()
        worksheet.update([["id", "time", "original", "generated", "image", "collaborations"]])
        return

    df_to_save = pd.DataFrame(updated_memories)
    df_to_save["collaborations"] = df_to_save["collaborations"].apply(json.dumps)
    
    data = [df_to_save.columns.values.tolist()] + df_to_save.values.tolist()
    worksheet.clear()
    worksheet.update(data)

if 'draft_text' not in st.session_state: st.session_state.draft_text = None
if 'original_text' not in st.session_state: st.session_state.original_text = None
if 'diary_key' not in st.session_state: st.session_state.diary_key = 0 

# ==========================================
# --- 1. 網頁設定 ---
# ==========================================
st.set_page_config(page_title="Honyen 的日本指揮中心", layout="wide", page_icon="🎌")

# --- 🔒 密碼鎖 ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Honyen 的日本 AI 導遊")
    password = st.text_input("請輸入通關密碼：", type="password")
    if st.button("登入"):
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

model = genai.GenerativeModel('gemini-2.5-flash')

# --- 3. 定義全日本資料庫 ---
city_db = {
    "新潟 (Niigata)": {"weather_url": "https://forecast7.com/zh-tw/37d92139d04/niigata/", "rail_name": "🚄 JR 東日本訂票", "rail_url": "https://www.eki-net.com/"},
    "東京 (Tokyo)": {"weather_url": "https://forecast7.com/zh-tw/35d69139d69/tokyo/", "rail_name": "🚄 JR 東日本訂票", "rail_url": "https://www.eki-net.com/"},
    "大阪 (Osaka)": {"weather_url": "https://forecast7.com/zh-tw/34d69135d50/osaka/", "rail_name": "🚄 JR 西日本訂票", "rail_url": "https://www.westjr.co.jp/global/tc/ticket/"},
    "京都 (Kyoto)": {"weather_url": "https://forecast7.com/zh-tw/35d01135d76/kyoto/", "rail_name": "🚄 JR 西日本訂票", "rail_url": "https://www.westjr.co.jp/global/tc/ticket/"},
    "北海道-札幌": {"weather_url": "https://forecast7.com/zh-tw/43d06141d35/sapporo/", "rail_name": "🚄 JR 北海道訂票", "rail_url": "https://www.jrhokkaido.co.jp/"},
    "福岡 (Fukuoka)": {"weather_url": "https://forecast7.com/zh-tw/33d59130d40/fukuoka/", "rail_name": "🚄 JR 九州訂票", "rail_url": "https://www.jrkyushu.co.jp/chinese/"},
    "沖繩-那霸": {"weather_url": "https://forecast7.com/zh-tw/26d21127d68/naha/", "rail_name": "🚝 沖繩單軌電車", "rail_url": "https://www.yui-rail.co.jp/tc/"}
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

# ==========================================
# --- 主畫面區塊 ---
# ==========================================
st.title(f"🎌 Honyen 的 AI 導遊 - {selected_city}篇")

tab1, tab2, tab3, tab4 = st.tabs(["💬 AI 導遊", "🗣️ 翻譯蒟蒻", "💰 敗家計算機", "📖 旅程共筆"])

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

    sys_prompt = f"""你是一位精通日本全境旅遊的台灣導遊。目前在「{selected_city}」。請真實回答並附上Google地圖連結。"""

    if user_input := st.chat_input("例：附近有什麼必吃拉麵？(附地圖)"):
        st.chat_message("user").markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})
        full_prompt = sys_prompt + "\n歷史對話:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[:-1]]) + "\n問題：" + user_input

        with st.chat_message("assistant"):
            with st.spinner("導遊查詢中..."):
                try:
                    res = model.generate_content([full_prompt, image]) if image else model.generate_content(full_prompt)
                    st.markdown(res.text)
                    st.session_state.messages.append({"role": "assistant", "content": res.text})
                except Exception as e:
                    st.error(f"錯誤：{e}")

with tab2:
    st.header("🗣️ 雙向溝通板")
    if "trans_history" not in st.session_state: st.session_state.trans_history = ""
    trans_mode = st.radio("模式", ["中翻日 (我問店員)", "日翻中 (店員說什麼)"], horizontal=True)
    trans_input = st.text_area("輸入文字：", height=100)
    if st.button("✨ 翻譯", type="primary") and trans_input:
        with st.spinner("翻譯中..."):
            prompt = f"把這句中文翻成禮貌日文附羅馬拼音：{trans_input}" if "中翻日" in trans_mode else f"把這句日文翻成繁體中文：{trans_input}"
            st.session_state.trans_history = model.generate_content(prompt).text 
    if st.session_state.trans_history: st.info(st.session_state.trans_history)

with tab3:
    st.header("💰 匯率換算")
    rate = st.number_input("目前匯率", value=0.22, format="%.3f")
    jpy = st.number_input("日幣金額 (¥)", min_value=0.0, step=100.0, value=None)
    st.metric("約合台幣 (TWD)", f"${int(jpy * rate) if jpy else 0}")
    
    item_name = st.text_input("商品名稱 (分析 CP 值用)")
    if st.button("分析 CP 值") and item_name and jpy:
        with st.spinner("分析中..."):
            st.write(model.generate_content(f"在日本買{item_name}價格日幣{jpy}，匯率{rate}，用台灣人角度分析划算嗎？").text)

with tab4:
    st.header("📖 旅程共筆書房")
    
    with st.expander("✍️ 寫下今天的新遊記 (點擊展開)", expanded=True):
        current_diary = st.text_area("今天去了哪裡？發生了什麼有趣或好笑的事？", height=100, key=f"diary_input_{st.session_state.diary_key}")
        diary_prompt = f"你是一位幽默的旅遊作家。目前在日本{selected_city}。請務必以「繁體中文」將草稿潤飾成生動日誌散文（可適當夾雜幾個日文名詞增加氛圍）：{current_diary}"

        if st.button("✨ 第 1 步：AI 幫我寫遊記", type="primary"):
            if current_diary.strip():
                with st.spinner("撰寫中..."):
                    st.session_state.draft_text = model.generate_content(diary_prompt).text
                    st.session_state.original_text = current_diary
            else:
                st.warning("請先寫點東西喔！")

        if st.session_state.draft_text:
            st.markdown("---")
            st.info("👇 預覽遊記草稿")
            st.markdown(st.session_state.draft_text)
            uploaded_file = st.file_uploader("🖼️ 第 2 步：上傳照片 (可先跳過，事後再補)", type=["png", "jpg", "jpeg"])
            
            if st.button("💾 確認存檔，發布！", type="secondary"):
                saved_image_path = ""
                if uploaded_file:
                    saved_image_path = os.path.join(IMAGE_DIR, f"japan_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
                    img = Image.open(uploaded_file)
                    img = ImageOps.exif_transpose(img)
                    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                    img.save(saved_image_path, "JPEG")
                
                save_memory(st.session_state.original_text, st.session_state.draft_text, saved_image_path)
                
                st.session_state.diary_key += 1
                st.session_state.draft_text = None
                st.session_state.original_text = None
                st.success("✅ 發布成功！")
                st.rerun()

    st.divider()
    st.subheader("📚 我們的旅程動態")
    all_memories = load_memories()
    
    if not all_memories:
        st.caption("目前還沒有遊記，快去寫下第一篇吧！")
    else:
        for memory in reversed(all_memories):
            with st.container(border=True):
                st.caption(f"🗓️ 發布時間：{memory['time']}")
                col1, col2 = st.columns([1, 2])
                with col1:
                    has_image = memory.get("image") and os.path.exists(memory.get("image"))
                    if has_image:
                        st.image(memory.get("image"), use_container_width=True)
                    else:
                        st.info("🖼️ 這篇遊記還沒放照片喔！")
                        with st.form(key=f"img_form_{memory['id']}", clear_on_submit=True):
                            new_img_file = st.file_uploader("現在補傳照片", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
                            if st.form_submit_button("💾 確認補圖", use_container_width=True):
                                if new_img_file:
                                    saved_path = os.path.join(IMAGE_DIR, f"japan_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
                                    img = Image.open(new_img_file)
                                    img = ImageOps.exif_transpose(img)
                                    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                                    img.save(saved_path, "JPEG")
                                    
                                    update_memory_image(memory['id'], saved_path)
                                    st.success("✅ 補圖成功！")
                                    st.rerun()
                                else:
                                    st.warning("請先選擇照片再按確認喔！")
                                    
                with col2:
                    st.markdown(memory['generated'])
                
                st.markdown("---")
                st.markdown("#### 💬 旅伴吐槽與補充")
                for collab in memory.get("collaborations", []):
                    st.info(f"**{collab['author']}** ({collab['time']})：{collab['text']}")
                
                with st.form(key=f"form_{memory['id']}", clear_on_submit=True):
                    c1, c2 = st.columns([1, 3])
                    author = c1.text_input("你是誰？(如: 妹妹)")
                    collab_text = c2.text_input("想補充什麼？")
                    if st.form_submit_button("送出留言"):
                        if author and collab_text:
                            add_collaboration(memory['id'], author, collab_text)
                            st.success("✅ 留言成功！")
                            st.rerun()
                            
                # 🌟 刪除功能的 UI 介面
                with st.expander("⚙️ 管理選項"):
                    if st.button("🗑️ 刪除此篇遊記", key=f"del_{memory['id']}", type="primary"):
                        delete_memory(memory['id'])
                        st.success("✅ 遊記已刪除！")
                        st.rerun()
