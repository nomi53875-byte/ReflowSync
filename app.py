import streamlit as st
import zipfile
import io
import re
import os

# 設定網頁標題與佈局
st.set_page_config(page_title="ThermalTune - 完整專案生成器", layout="wide")

st.title("🔥 ThermalTune: 爐溫專案一鍵生成工具")
st.markdown("輸入設定後，系統將根據母本產生一個「完整的壓縮專案」，包含所有資料夾與數據檔案。")

# --- 第一區：側邊欄設定 ---
with st.sidebar:
    st.header("基礎設定")
    
    speed_option = st.selectbox(
        "選擇基準速度 (Speed)",
        options=["85", "90"],
        help="選擇 85 將以 85速母本為基礎進行調整"
    )
    
    st.divider()
    
    # 預設母本中的代碼與編號
    OLD_CLIENT = "ABC"
    OLD_PART = "31ABC001-001AFA"
    
    new_client = st.text_input("1. 新公司代號 (取代 ABC)", value="BBB")
    new_part = st.text_input("2. 新產品編號 (取代舊編號)", value="31BBB002-002BFA")

# --- 第二區：主畫面爐溫調整 ---
st.header("🌡️ 爐溫同步設定 (Zone 1 - 10)")
st.info("這裡設定的溫度會同步更新到壓縮檔內所有相關的 XML 與數據標籤中。")

col1, col2, col3, col4, col5 = st.columns(5)
z_vals = []

for i in range(1, 11):
    col_target = [col1, col2, col3, col4, col5][(i-1) % 5]
    with col_target:
        # 預設起始溫度
        default_temp = 180 if i <= 3 else 200 + (i-4)*20 if i <= 8 else 260
        val = st.number_input(f"Zone {i}", value=int(default_temp), key=f"z{i}")
        z_vals.append(val)

# --- 第三區：核心處理邏輯 ---
def process_data(raw_data, n_client, n_part, v_list):
    try:
        # 將二進位轉為文字進行取代 (針對 ESA, XML, TXT)
        text = raw_data.decode('utf-8', errors='ignore')
        
        # 1. 取代公司代號
        text = text.replace(OLD_CLIENT, n_client)
        
        # 2. 取代產品編號
        text = text.replace(OLD_PART, n_part)
        
        # 3. 取代前 10 區爐溫標籤 <ZoneX_SetPoint>
        for i in range(1, 11):
            tag = f"Zone{i}_SetPoint"
            pattern = f"<{tag}>.*?</{tag}>"
            replacement = f"<{tag}>{v_list[i-1]};{v_list[i-1]}</{tag}>"
            text = re.sub(pattern, replacement, text)
            
        return text.encode('utf-8')
    except:
        # 如果是完全無法處理的二進位檔，則回傳原始資料
        return raw_data

# --- 第四區：打包輸出 ---
if st.button("🚀 產生並下載完整結果 (.zip)", type="primary"):
    # 這裡請根據你在 GitHub 存放的路徑決定是否加上 assets/
    template_path = f"assets/template_{speed_option}.zip"
    
    if not os.path.exists(template_path):
        st.error(f"❌ 找不到母本檔案: {template_path}")
    else:
        output_buffer = io.BytesIO()
        try:
            with zipfile.ZipFile(template_path, 'r') as zip_ref:
                with zipfile.ZipFile(output_buffer, 'w') as new_zip:
                    # 抓取壓縮檔內所有的路徑與檔案
                    for file_info in zip_ref.infolist():
                        with zip_ref.open(file_info.filename) as f:
                            original_data = f.read()
                        
                        # 處理內容 (同步改代碼、編號、溫度)
                        final_data = process_data(original_data, new_client, new_part, z_vals)
                        
                        # 同步修改檔名與路徑中的編號
                        # 保留 # 後面的日期時間，只換掉 31ABC001-001AFA
                        new_filename = file_info.filename.replace(OLD_PART, new_part)
                        
                        # 寫入新的壓縮檔，維持原本目錄結構
                        new_zip.writestr(new_filename, final_data)
            
            st.success("✅ 完整結果已生成！")
            st.download_button(
                label="📥 點此下載結果壓縮檔",
                data=output_buffer.getvalue(),
                file_name=f"{new_part}_Result.zip",
                mime="application/zip"
            )
        except Exception as e:
            st.error(f"執行時發生錯誤: {e}")
