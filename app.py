import streamlit as st
import zipfile
import io
import re
import os

# 1. 網頁基礎設定
st.set_page_config(page_title="ThermalTune - 完整專案生成器", layout="wide")

st.title("🔥 ThermalTune: 爐溫專案一鍵生成工具")
st.markdown("輸入設定後，系統將根據母本產生一個「完整的壓縮專案」，包含所有資料夾與數據檔案。")

# --- 第一區：側邊欄設定 ---
with st.sidebar:
    st.header("基礎設定")
    
    # 選擇速度母本
    speed_option = st.selectbox(
        "選擇基準速度 (Speed)",
        options=["85", "90"],
        help="選擇 85 將以 template_85.zip 為基礎；90 則使用 template_90.zip"
    )
    
    st.divider()
    
    # 預設母本中的舊資訊 (請確保母本內的內容與此一致)
    OLD_CLIENT = "ABC"
    OLD_PART = "31ABC001-001AFA"
    
    new_client = st.text_input("1. 新公司代號 (取代 ABC)", value="BBB")
    new_part = st.text_input("2. 新產品編號 (取代舊編號)", value="31BBB002-002BFA")

# --- 第二區：主畫面爐溫調整 ---
st.header("🌡️ 爐溫同步設定 (Zone 1 - 10)")
st.info("這裡設定的溫度會同步更新到壓縮檔內「所有相關」的內容中。")

col1, col2, col3, col4, col5 = st.columns(5)
z_vals = []

# 建立 10 個溫區輸入框
for i in range(1, 11):
    col_target = [col1, col2, col3, col4, col5][(i-1) % 5]
    with col_target:
        # 設定預設溫度
        default_temp = 180 if i <= 3 else 200 + (i-4)*20 if i <= 8 else 260
        val = st.number_input(f"Zone {i}", value=int(default_temp), key=f"z{i}")
        z_vals.append(val)

# --- 第三區：核心處理邏輯 ---
def process_data(raw_data, n_client, n_part, v_list):
    try:
        # 嘗試將二進位轉為文字進行取代 (針對 ESA, XML, TXT 等)
        text = raw_data.decode('utf-8', errors='ignore')
        
        # 1. 取代公司代號
        text = text.replace(OLD_CLIENT, n_client)
        # 2. 取代產品編號
        text = text.replace(OLD_PART, n_part)
        
        # 3. 正則表達式取代前 10 區爐溫標籤 <ZoneX_SetPoint>
        for i in range(1, 11):
            tag = f"Zone{i}_SetPoint"
            pattern = f"<{tag}>.*?</{tag}>"
            replacement = f"<{tag}>{v_list[i-1]};{v_list[i-1]}</{tag}>"
            text = re.sub(pattern, replacement, text)
            
        return text.encode('utf-8')
    except:
        # 如果檔案無法以文字處理，則回傳原始二進位資料
        return raw_data

# --- 第四區：打包輸出邏輯 ---
if st.button("🚀 產生並下載完整結果 (.zip)", type="primary"):
    # 這裡直接在根目錄尋找檔案
    template_path = f"template_{speed_option}.zip"
    
    if not os.path.exists(template_path):
        st.error(f"❌ 找不到母本檔案: {template_path}。請確認已將 ZIP 檔上傳至 GitHub 專案首頁。")
    else:
        output_buffer = io.BytesIO()
        try:
            with zipfile.ZipFile(template_path, 'r') as zip_ref:
                with zipfile.ZipFile(output_buffer, 'w') as new_zip:
                    # 遍歷壓縮檔內所有的路徑與檔案
                    for file_info in zip_ref.infolist():
                        with zip_ref.open(file_info.filename) as f:
                            original_data = f.read()
                        
                        # 處理檔案內容
                        final_data = process_data(original_data, new_client, new_part, z_vals)
                        
                        # 修改檔名與路徑：取代舊編號，保留日期時間戳記
                        new_filename = file_info.filename.replace(OLD_PART, new_part)
                        
                        # 寫入新壓縮檔，維持原本目錄結構
                        new_zip.writestr(new_filename, final_data)
            
            st.success("✅ 完整結果已成功生成！")
            st.download_button(
                label="📥 點此下載結果壓縮檔",
                data=output_buffer.getvalue(),
                file_name=f"{new_part}_Result.zip",
                mime="application/zip"
            )
        except Exception as e:
            st.error(f"執行時發生錯誤: {e}")
