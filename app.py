import streamlit as st
import zipfile
import io
import re
import os

# 設定網頁基礎
st.set_page_config(page_title="ThermalTune - 全面同步版", layout="wide")

st.title("🔥 ThermalTune: 爐溫專案一鍵生成工具")
st.markdown("本版本已優化「多重編號同步」，確保壓縮檔內的所有檔名與內容均會更新。")

# --- 第一區：側邊欄設定 ---
with st.sidebar:
    st.header("基礎設定")
    speed_option = st.selectbox("選擇基準速度 (Speed)", options=["85", "90"])
    
    st.divider()
    
    # 這裡定義母本中所有可能出現的「舊編號」
    # 如果你發現還有漏掉的編號，可以加進這個列表
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
        text = raw_data.decode('utf-8', errors='ignore')
        
        # 1. 取代公司代號
        text = text.replace(OLD_CLIENT, n_client)
        
        # 2. 循環取代所有已知的舊編號
        for old_id in OLD_IDENTIFIERS:
            text = text.replace(old_id, n_part)
        
        # 3. 取代爐溫標籤
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
                            original_data = f.read()
                        
                        # 處理內容
                        final_data = process_content(original_data, new_client, new_part, z_vals)
                        
                        # 【關鍵修正】：同步修改檔名與路徑
                        # 將所有已知的舊編號都換成新編號
                        new_filename = file_info.filename
                        for old_id in OLD_IDENTIFIERS:
                            new_filename = new_filename.replace(old_id, n_part)
                        
                        new_zip.writestr(new_filename, final_data)
            
            st.success("✅ 完整結果已生成！")
            st.download_button("📥 下載結果", data=output_buffer.getvalue(), file_name=f"{new_part}_Result.zip")
        except Exception as e:
            st.error(f"發生錯誤: {e}")
