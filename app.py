import streamlit as st
import pandas as pd
import zipfile
import io
import re
import os

# 設定網頁標題
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
        help="選擇 85 將使用『原始檔85...』作為基底；90 則使用『原始檔90...』"
    )
    
    st.divider()
    
    # 2. 公司代號變更
    old_client = "ABC" # 預設母本中的代碼
    new_client = st.text_input("輸入新公司代號", value="BBB", help="將內容中所有的 ABC 取代為此代號")
    
    # 3. 產品編號/檔名變更
    old_part = "31ABC001-001AFA" # 預設母本中的編號
    new_part = st.text_input("輸入新產品編號 (檔名前綴)", value="31BBB002-002BFA")

# --- 第二區：主畫面爐溫調整 ---
st.header("🌡️ 爐溫設定 (Zone 1 - 10)")
st.info("請輸入前 10 區的溫度值，系統會自動同步至所有檔案中。")

# 建立 5x2 的輸入配置
col1, col2, col3, col4, col5 = st.columns(5)
zones = []

with col1:
    zones.append(st.number_input("Zone 1", value=180))
    zones.append(st.number_input("Zone 6", value=210))
with col2:
    zones.append(st.number_input("Zone 2", value=180))
    zones.append(st.number_input("Zone 7", value=230))
with col3:
    zones.append(st.number_input("Zone 3", value=180))
    zones.append(st.number_input("Zone 8", value=240))
with col4:
    zones.append(st.number_input("Zone 4", value=200))
    zones.append(st.number_input("Zone 9", value=260))
with col5:
    zones.append(st.number_input("Zone 5", value=200))
    zones.append(st.number_input("Zone 10", value=260))

# 重新排序 zones 確保順序為 1~10
zone_values = [zones[0], zones[2], zones[4], zones[6], zones[8], 
               zones[1], zones[3], zones[5], zones[7], zones[9]]

# --- 第三區：核心邏輯處理 ---
def process_content(content, old_c, new_c, old_p, new_p, z_vals):
    # A. 全域取代公司代號
    content = content.replace(old_c, new_c)
    
    # B. 全域取代產品編號
    content = content.replace(old_p, new_p)
    
    # C. 正則表達式取代前 10 區溫度
    # 匹配模式：<Zone1_SetPoint>...</Zone1_SetPoint>
    for i in range(1, 11):
        tag = f"Zone{i}_SetPoint"
        pattern = f"<{tag}>.*?</{tag}>"
        replacement = f"<{tag}>{z_vals[i-1]};{z_vals[i-1]}</{tag}>"
        content = re.sub(pattern, replacement, content)
    
    return content

if st.button("🚀 開始產生調整後的檔案", type="primary"):
    # 模擬從 GitHub assets 讀取母本壓縮檔
    template_file = f"assets/template_{speed_option}.zip"
    
    if not os.path.exists(template_file):