import streamlit as st
import zipfile
import io
import re
import os

# 1. 網頁基礎設定
st.set_page_config(page_title="ThermalTune - 專業製程版", layout="wide")

st.title("🔥 ThermalTune: 爐溫專案一鍵生成工具")
st.markdown("本版本採用「Callback 事件觸發」邏輯，確保修改上溫區時，下溫區能即時同步。")

# --- 初始化記憶體 (Session State) ---
# 預設溫度邏輯
def get_default_temp(i):
    return 180 if i <= 3 else 200 + (i-4)*20 if i <= 8 else 260

for i in range(1, 11):
    t_key = f"t{i}"
    b_key = f"b{i}"
    if t_key not in st.session_state:
        st.session_state[t_key] = get_default_temp(i)
    if b_key not in st.session_state:
        st.session_state[b_key] = get_default_temp(i)

# --- 第一區：側邊欄設定 ---
with st.sidebar:
    st.header("基礎設定")
    speed_option = st.selectbox("選擇基準速度", options=["85", "90"])
    st.divider()
    
    new_client = st.text_input("1. 新公司代號", value="BBB")
    new_part = st.text_input("2. 新產品編號", value="31BBB002-002BFA")
    
    st.divider()
    sync_mode = st.checkbox("同步上下溫區設定", value=True)

# --- 核心連動函式 ---
def sync_t_to_b(index):
    # 當上溫區改變時，如果同步開啟，手動強迫下溫區數值等於上溫區
    if sync_mode:
        st.session_state[f"b{index}"] = st.session_state[f"t{index}"]

# --- 第二區：爐溫設定區 ---
st.header("🌡️ 爐溫同步設定 (Zone 1 - 10)")

# A. 建立 Top 溫區輸入
st.subheader("⬆️ Top (上溫區)")
t_cols = st.columns(10)
for i in range(1, 11):
    with t_cols[i-1]:
        st.number_input(
            f"T{i}", 
            step=1,
            key=f"t{i}", 
            on_change=sync_t_to_b, # 只要一改，立刻觸發同步
            args=(i,),
            label_visibility="collapsed"
        )
        st.caption(f"Z{i} Top")

st.divider()

# B. 建立 Bottom 溫區輸入
st.subheader("⬇️ Bottom (下溫區)")
b_cols = st.columns(10)
for i in range(1, 11):
    with b_cols[i-1]:
        # 下溫區的數值與狀態
        st.number_input(
            f"B{i}", 
            step=1,
            key=f"b{i}", 
            disabled=sync_mode, # 同步時鎖定輸入
            label_visibility="collapsed"
        )
        st.caption(f"Z{i} Bot")

# 整合寫入字串 (從 session_state 抓取最終值)
final_zone_strings = [f"{st.session_state[f't{i}']};{st.session_state[f'b{i}']}" for i in range(1, 11)]

# --- 第三區：核心結構定位取代邏輯 ---
def process_content_by_structure(raw_data, n_client, n_part, z_str_list):
    try:
        text = raw_data.decode('utf-8', errors='ignore')
        text = text.replace("ABC", n_client)
        
        tags_to_fix = ["Name", "ProductName", "RecipeName", "ProductPath", "RecipePath"]
        for tag in tags_to_fix:
            pattern = f"<{tag}>.*?</{tag}>"
            text = re.sub(pattern, f"<{tag}>{n_part}</{tag}>", text)
            
        text = re.sub(r'ReflowFiles\\.*?\\', f'ReflowFiles\\\\{n_part}\\\\', text)
        text = re.sub(r'ReflowFiles\\.*?#', f'ReflowFiles\\\\{n_part}#', text)

        for i in range(1, 11):
            tag = f"Zone{i}_SetPoint"
            pattern = f"<{tag}>.*?</{tag}>"
            replacement = f"<{tag}>{z_str_list[i-1]}</{tag}>"
            text = re.sub(pattern, replacement, text)
            
        return text.encode('utf-8')
    except:
        return raw_data

# --- 第四區：打包輸出 ---
if st.button("🚀 執行結構化同步並下載", type="primary"):
    template_path = f"template_{speed_option}.zip"
    if not os.path.exists(template_path):
        st.error(f"❌ 找不到母本檔案: {template_path}")
    else:
        output_buffer = io.BytesIO()
        try:
            with zipfile.ZipFile(template_path, 'r') as zip_ref:
                with zipfile.ZipFile(output_buffer, 'w') as new_zip:
                    for file_info in zip_ref.infolist():
                        with zip_ref.open(file_info.filename) as f:
                            data = f.read()
                        
                        processed_data = process_content_by_structure(data, new_client, new_part, final_zone_strings)
                        
                        # 處理檔名
                        old_filename = file_info.filename
                        path_parts = old_filename.split('/')
                        last_part = path_parts[-1]
                        if "#" in last_part:
                            new_last_part = re.sub(r'^.*?#', f"{new_part}#", last_part)
                            path_parts[-1] = new_last_part
                            new_name = "/".join(path_parts)
                        else:
                            new_name = old_filename.replace("31ABC001-001AFA", new_part)
                        
                        new_zip.writestr(new_name, processed_data)
        
            st.success("✅ 專案生成完成！")
            st.download_button("📥 下載結果壓縮檔", data=output_buffer.getvalue(), file_name=f"{new_part}_Result.zip")
        except Exception as e:
            st.error(f"發生錯誤: {e}")
