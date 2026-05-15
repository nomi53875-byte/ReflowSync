import streamlit as st
import zipfile
import io
import re
import os

# 1. 網頁基礎設定
st.set_page_config(page_title="ThermalTune - 標準化母檔版", layout="wide")

st.title("🔥 ThermalTune: 爐溫專案一鍵生成工具")
st.markdown("本版本專為「標準化母檔」設計，透過精確標記確保 100% 同步成功率。")

# --- 初始化記憶體 (Session State) ---
def get_default_temp(i):
    return 180 if i <= 3 else 200 + (i-4)*20 if i <= 8 else 260

for i in range(1, 11):
    t_key, b_key = f"t{i}", f"b{i}"
    if t_key not in st.session_state:
        st.session_state[t_key] = get_default_temp(i)
    if b_key not in st.session_state:
        st.session_state[b_key] = st.session_state[t_key]

# --- 第一區：側邊欄設定 ---
with st.sidebar:
    st.header("基礎設定")
    speed_option = st.selectbox("選擇基準速度母本", options=["85", "90"])
    st.divider()
    
    # 標準化母檔使用的預留標籤
    MARK_CLIENT = "TEMPLATE_CLIENT"
    MARK_PART = "TEMPLATE_PART_ID"
    
    new_client = st.text_input("1. 新公司代號 (取代 TEMPLATE_CLIENT)", value="BBB")
    new_part = st.text_input("2. 新產品編號 (取代 TEMPLATE_PART_ID)", value="31BBB002-002BFA")
    st.divider()
    sync_mode = st.checkbox("同步上下溫區設定", value=True)

# 核心連動函式
def sync_t_to_b(index):
    if sync_mode:
        st.session_state[f"b{index}"] = st.session_state[f"t{index}"]

# --- 第二區：爐溫設定區 ---
st.header("🌡️ 爐溫同步設定 (Zone 1 - 10)")
st.subheader("⬆️ Top (上溫區)")
t_cols = st.columns(10)
for i in range(1, 11):
    with t_cols[i-1]:
        st.number_input(f"T{i}", step=1, key=f"t{i}", on_change=sync_t_to_b, args=(i,), label_visibility="collapsed")
        st.caption(f"Z{i} Top")

st.subheader("⬇️ Bottom (下溫區)")
b_cols = st.columns(10)
for i in range(1, 11):
    with b_cols[i-1]:
        st.number_input(f"B{i}", step=1, key=f"b{i}", disabled=sync_mode, label_visibility="collapsed")
        st.caption(f"Z{i} Bot")

# 整合寫入字串
final_zone_strings = [f"{st.session_state[f't{i}']};{st.session_state[f'b{i}']}" for i in range(1, 11)]

# --- 第三區：核心精確取代邏輯 ---
def process_standard_template(raw_data, n_client, n_part, z_str_list):
    try:
        # 解碼並進行精確標籤替換
        text = raw_data.decode('utf-8', errors='ignore')
        
        # 1. 替換預留標記 (檔名、ID、公司代號)
        text = text.replace(MARK_CLIENT, n_client)
        text = text.replace(MARK_PART, n_part)
        
        # 2. 替換溫區 (鎖定 ZoneX_SetPoint 標籤)
        for i in range(1, 11):
            tag = f"Zone{i}_SetPoint"
            # 使用 Regex 確保只換掉標籤內的內容
            pattern = f"<{tag}>.*?</{tag}>"
            replacement = f"<{tag}>{z_str_list[i-1]}</{tag}>"
            text = re.sub(pattern, replacement, text)
            
        return text.encode('utf-8')
    except:
        return raw_data

# --- 第四區：打包輸出 ---
if st.button("🚀 執行精確同步並下載專案", type="primary"):
    template_path = f"template_{speed_option}.zip"
    if not os.path.exists(template_path):
        st.error(f"❌ 找不到母本檔案: {template_path}。請確認已將 ZIP 檔上傳至 GitHub。")
    else:
        output_buffer = io.BytesIO()
        try:
            with zipfile.ZipFile(template_path, 'r') as zip_ref:
                with zipfile.ZipFile(output_buffer, 'w') as new_zip:
                    for file_info in zip_ref.infolist():
                        with zip_ref.open(file_info.filename) as f:
                            data = f.read()
                        
                        # 內容處理
                        processed_data = process_standard_template(data, new_client, new_part, final_zone_strings)
                        
                        # 檔名與資料夾路徑處理 (同樣執行精確替換)
                        new_name = file_info.filename.replace(MARK_PART, n_part) if 'n_part' in locals() else file_info.filename.replace(MARK_PART, new_part)
                        
                        new_zip.writestr(new_name, processed_data)
        
            st.success("✅ 專案已根據標準化母檔生成！")
            st.download_button("📥 下載結果壓縮檔", data=output_buffer.getvalue(), file_name=f"{new_part}_Result.zip")
        except Exception as e:
            st.error(f"發生錯誤: {e}")
