import streamlit as st
import zipfile
import io
import re
import os

# 設定網頁標題與佈局
st.set_page_config(page_title="ThermalTune - 爐溫曲線同步工具", layout="wide")

st.title("🔥 ThermalTune: 爐溫曲線調整小工具")
st.markdown("本工具將根據設定，同步修改三個關鍵檔案的名稱、內容 ID、公司代號及前 10 區溫點。")

# --- 第一區：側邊欄設定 ---
with st.sidebar:
    st.header("基礎設定")
    
    # 1. 鏈條速度選擇 (決定母本)
    speed_option = st.selectbox(
        "選擇鏈條速度母本 (Speed)",
        options=["85", "90"],
        help="選擇 85 將使用 template_85.zip；選擇 90 將使用 template_90.zip"
    )
    
    st.divider()
    
    # 2. 公司代號與產品編號
    old_client = "ABC"
    new_client = st.text_input("輸入新公司代號", value="BBB")
    
    old_part = "31ABC001-001AFA"
    new_part = st.text_input("輸入新產品編號 (檔名前綴)", value="31BBB002-002BFA")

# --- 第二區：主畫面爐溫調整 (Zone 1 - 10) ---
st.header("🌡️ 爐溫設定 (Zone 1 - 10)")
st.info("請輸入前 10 區的溫度值（例如輸入 180，程式會自動填入 180;180）。")

col1, col2, col3, col4, col5 = st.columns(5)
z_vals = []

# 建立輸入框並分配到 5 欄
for i in range(1, 11):
    col_target = [col1, col2, col3, col4, col5][(i-1) % 5]
    with col_target:
        # 預設一些數值方便測試，可依需求自行修改
        default_val = 180 if i <= 3 else 200 + (i-4)*20 if i <= 8 else 260
        val = st.number_input(f"Zone {i}", value=int(default_val), key=f"z{i}")
        z_vals.append(val)

# --- 第三區：核心邏輯處理函式 ---
def process_content(content, n_client, n_part, v_list):
    # A. 全域取代公司代號
    content = content.replace("ABC", n_client)
    
    # B. 全域取代產品編號 (內容中的 ID)
    content = content.replace("31ABC001-001AFA", n_part)
    
    # C. 正則表達式取代前 10 區溫度標籤 <ZoneX_SetPoint>
    for i in range(1, 11):
        tag = f"Zone{i}_SetPoint"
        pattern = f"<{tag}>.*?</{tag}>"
        replacement = f"<{tag}>{v_list[i-1]};{v_list[i-1]}</{tag}>"
        content = re.sub(pattern, replacement, content)
    
    return content

# --- 第四區：執行按鈕與檔案輸出 ---
if st.button("🚀 開始同步修改並下載", type="primary"):
    # 預設路徑在 assets 資料夾內
    template_path = f"assets/template_{speed_option}.zip"
    
    if not os.path.exists(template_path):
        st.error(f"❌ 找不到母本檔案: {template_path}，請確認檔案已上傳至 GitHub 的 assets 資料夾中。")
    else:
        output_zip = io.BytesIO()
        try:
            with zipfile.ZipFile(template_path, 'r') as zip_ref:
                with zipfile.ZipFile(output_zip, 'w') as new_zip:
                    for file_info in zip_ref.infolist():
                        # 讀取檔案內容
                        with zip_ref.open(file_info.filename) as f:
                            # 嘗試使用 utf-8 讀取，並忽略無法解碼的字元
                            content = f.read().decode('utf-8', errors='ignore')
                        
                        # 執行內容取代
                        updated_content = process_content(content, new_client, new_part, z_vals)
                        
                        # 處理檔名：取代舊編號，保留 # 及其後的日期
                        new_filename = file_info.filename.replace("31ABC001-001AFA", new_part)
                        
                        # 將處理後的內容寫入新的 ZIP
                        new_zip.writestr(new_filename, updated_content)
            
            st.success("✅ 調整完成！")
            st.download_button(
                label="📥 點此下載調整後的壓縮檔 (.zip)",
                data=output_zip.getvalue(),
                file_name=f"{new_part}_Adjusted.zip",
                mime="application/zip"
            )
        except Exception as e:
            st.error(f"執行過程發生錯誤: {e}")
