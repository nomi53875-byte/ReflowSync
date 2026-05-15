import streamlit as st
import zipfile
import io
import re
import os

# 設定網頁基礎
st.set_page_config(page_title="ThermalTune - 全面同步修正版", layout="wide")

st.title("🔥 ThermalTune: 爐溫專案一鍵生成工具")
st.markdown("本版本修正了變數未定義錯誤，並強化了「檔名與路徑」的深度替換邏輯。")

# --- 第一區：側邊欄設定 ---
with st.sidebar:
    st.header("基礎設定")
    speed_option = st.selectbox("選擇基準速度 (Speed)", options=["85", "90"])
    
    st.divider()
    
    # 定義母本中可能出現的所有舊編號（請根據你的母本實際情況調整）
    OLD_IDENTIFIERS = ["31ABC001-001AFA", "31BAG902-001ZRA", "31DCC001-001AFA"]
    OLD_CLIENT = "ABC"
    
    new_client = st.text_input("1. 新公司代號 (取代 ABC)", value="BBB")
    new_part = st.text_input("2. 新產品編號 (取代所有舊編號)", value="31BBB002-002BFA")

# --- 第二區：爐溫設定 ---
st.header("🌡️ 爐溫同步設定 (Zone 1 - 10)")
col1, col2, col3, col4, col5 = st.columns(5)
z_vals = []
for i in range(1, 11):
    col_target = [col1, col2, col3, col4, col5][(i-1) % 5]
    with col_target:
        val = st.number_input(f"Zone {i}", value=180 if i <= 3 else 200 + (i-4)*20 if i <= 8 else 260, key=f"z{i}")
        z_vals.append(val)

# --- 第三區：核心取代邏輯 ---
def process_content(raw_data, n_client, n_part, v_list):
    try:
        # 嘗試解碼成文字，若失敗則回傳原始資料
        text = raw_data.decode('utf-8', errors='ignore')
        
        # 1. 取代公司代號
        text = text.replace(OLD_CLIENT, n_client)
        
        # 2. 循環取代所有已知的舊產品編號
        for old_id in OLD_IDENTIFIERS:
            text = text.replace(old_id, n_part)
        
        # 3. 取代爐溫標籤 <ZoneX_SetPoint>
        for i in range(1, 11):
            tag = f"Zone{i}_SetPoint"
            pattern = f"<{tag}>.*?</{tag}>"
            replacement = f"<{tag}>{v_list[i-1]};{v_list[i-1]}</{tag}>"
            text = re.sub(pattern, replacement, text)
            
        return text.encode('utf-8')
    except:
        return raw_data

# --- 第四區：打包輸出 ---
if st.button("🚀 產生並下載完整結果 (.zip)", type="primary"):
    # 檢查根目錄下的 template_{85|90}.zip
    template_path = f"template_{speed_option}.zip"
    
    if not os.path.exists(template_path):
        st.error(f"❌ 找不到母本檔案: {template_path}。請確認 ZIP 檔已上傳至 GitHub 專案首頁。")
    else:
        output_buffer = io.BytesIO()
        try:
            with zipfile.ZipFile(template_path, 'r') as zip_ref:
                with zipfile.ZipFile(output_buffer, 'w') as new_zip:
                    for file_info in zip_ref.infolist():
                        with zip_ref.open(file_info.filename) as f:
                            original_data = f.read()
                        
                        # 處理檔案內容 (文字取代)
                        final_data = process_content(original_data, new_client, new_part, z_vals)
                        
                        # --- 深度修改檔名與路徑邏輯 ---
                        new_filename = file_info.filename
                        # 逐一檢查並替換路徑中所有可能的舊編號
                        for old_id in OLD_IDENTIFIERS:
                            if old_id in new_filename:
                                new_filename = new_filename.replace(old_id, new_part)
                        
                        # 寫入新壓縮檔
                        new_zip.writestr(new_filename, final_data)
            
            st.success("✅ 完整結果已生成！")
            st.download_button(
                label="📥 點此下載結果壓縮檔", 
                data=output_buffer.getvalue(), 
                file_name=f"{new_part}_Result.zip",
                mime="application/zip"
            )
        except Exception as e:
            st.error(f"執行過程發生錯誤: {e}")
