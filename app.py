import streamlit as st
import zipfile
import io
import re
import os

# 1. 網頁基礎設定
st.set_page_config(page_title="ThermalTune - 專業製程版", layout="wide")

st.title("🔥 ThermalTune: 爐溫專案一鍵生成工具")
st.markdown("本版本已修正「上下連動」邏輯，開啟同步時，修改上溫區會即時更新下溫區。")

# --- 第一區：側邊欄設定 ---
with st.sidebar:
    st.header("基礎設定")
    speed_option = st.selectbox("選擇基準速度", options=["85", "90"])
    st.divider()
    
    new_client = st.text_input("1. 新公司代號", value="BBB")
    new_part = st.text_input("2. 新產品編號", value="31BBB002-002BFA")
    
    st.divider()
    # 同步開關
    sync_mode = st.checkbox("同步上下溫區設定", value=True)

# --- 第二區：爐溫設定區 (上下分離排列) ---
st.header("🌡️ 爐溫同步設定 (Zone 1 - 10)")

top_vals = []
bottom_vals = []

# 建立 Top 溫區輸入
st.subheader("⬆️ Top (上溫區)")
t_cols = st.columns(10)
for i in range(1, 11):
    with t_cols[i-1]:
        default_t = 180 if i <= 3 else 200 + (i-4)*20 if i <= 8 else 260
        t_val = st.number_input(f"Zone {i}", value=int(default_t), key=f"top_{i}", label_visibility="collapsed")
        st.caption(f"Z{i} Top")
        top_vals.append(t_val)

# 建立 Bottom 溫區輸入
st.subheader("⬇️ Bottom (下溫區)")
b_cols = st.columns(10)
for i in range(1, 11):
    with b_cols[i-1]:
        # 【核心修正】：如果同步模式開啟，Bottom 的 value 直接鎖定為 Top 的數值
        b_default = top_vals[i-1] if sync_mode else top_vals[i-1]
        
        # 使用 disabled 屬性：如果開啟同步，則下溫區變為「唯讀」狀態以確保同步
        b_val = st.number_input(
            f"Z{i} Bot", 
            value=int(b_default), 
            key=f"bot_{i}", 
            label_visibility="collapsed",
            disabled=sync_mode 
        )
        st.caption(f"Z{i} Bot")
        bottom_vals.append(b_val)

# 整合為寫入格式 "Top;Bottom"
final_zone_strings = [f"{top_vals[i]};{bottom_vals[i]}" for i in range(10)]

# --- 第三區：核心結構定位取代邏輯 ---
def process_content_by_structure(raw_data, n_client, n_part, z_str_list):
    try:
        text = raw_data.decode('utf-8', errors='ignore')
        
        # 1. 基礎取代 (公司代號)
        text = text.replace("ABC", n_client)
        
        # 2. 強制位置取代 (XML 標籤)
        tags_to_fix = ["Name", "ProductName", "RecipeName", "ProductPath", "RecipePath"]
        for tag in tags_to_fix:
            pattern = f"<{tag}>.*?</{tag}>"
            text = re.sub(pattern, f"<{tag}>{n_part}</{tag}>", text)
            
        # 3. 處理特殊路徑定位 (ReflowFiles 資料夾路徑)
        text = re.sub(r'ReflowFiles\\.*?\\', f'ReflowFiles\\\\{n_part}\\\\', text)
        text = re.sub(r'ReflowFiles\\.*?#', f'ReflowFiles\\\\{n_part}#', text)

        # 4. 爐溫取代 (格式：Top;Bottom)
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
                        
                        # 處理檔名：使用 '#' 定位強制替換前綴
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
