import streamlit as st
import zipfile
import io
import re
import os

st.set_page_config(page_title="ThermalTune - 結構定位版", layout="wide")
st.title("🔥 ThermalTune: 結構定位同步工具")
st.markdown("本版本採用「標籤定位」與「模式匹配」，無需統一母檔編號即可強制替換。")

with st.sidebar:
    st.header("基礎設定")
    speed_option = st.selectbox("選擇基準速度", options=["85", "90"])
    st.divider()
    
    # 這裡我們只需要保留一個最基礎的代號作為保險，其他靠結構定位
    OLD_CLIENT = "ABC"
    new_client = st.text_input("1. 新公司代號", value="BBB")
    new_part = st.text_input("2. 新產品編號", value="31BBB002-002BFA")

st.header("🌡️ 爐溫同步設定 (Zone 1 - 10)")
col1, col2, col3, col4, col5 = st.columns(5)
z_vals = []
for i in range(1, 11):
    col_target = [col1, col2, col3, col4, col5][(i-1) % 5]
    with col_target:
        val = st.number_input(f"Zone {i}", value=180, key=f"z{i}")
        z_vals.append(val)

def process_content_by_structure(raw_data, n_client, n_part, v_list):
    try:
        text = raw_data.decode('utf-8', errors='ignore')
        
        # 1. 處理公司代號 (保留關鍵字取代)
        text = text.replace(OLD_CLIENT, n_client)
        
        # 2. 強制位置取代：針對 XML 標籤內的內容進行強制換血
        # 匹配 <ProductName>內容</ProductName> 等標籤，無視內容直接換成 n_part
        tags_to_fix = ["Name", "ProductName", "RecipeName", "ProductPath", "RecipePath"]
        for tag in tags_to_fix:
            pattern = f"<{tag}>.*?</{tag}>"
            text = re.sub(pattern, f"<{tag}>{n_part}</{tag}>", text)
            
        # 3. 處理特殊路徑：LatestBaseLine 裡面的完整路徑
        # 找到路徑最後一部分並替換
        text = re.sub(r'ReflowFiles\\.*?\\', f'ReflowFiles\\\\{n_part}\\\\', text)
        text = re.sub(r'ReflowFiles\\.*?#', f'ReflowFiles\\\\{n_part}#', text)

        # 4. 爐溫取代 (原有的邏輯)
        for i in range(1, 11):
            tag = f"Zone{i}_SetPoint"
            pattern = f"<{tag}>.*?</{tag}>"
            replacement = f"<{tag}>{v_list[i-1]};{v_list[i-1]}</{tag}>"
            text = re.sub(pattern, replacement, text)
            
        return text.encode('utf-8')
    except:
        return raw_data

if st.button("🚀 執行結構化同步", type="primary"):
    template_path = f"template_{speed_option}.zip"
    if not os.path.exists(template_path):
        st.error(f"找不到檔案: {template_path}")
    else:
        output_buffer = io.BytesIO()
        with zipfile.ZipFile(template_path, 'r') as zip_ref:
            with zipfile.ZipFile(output_buffer, 'w') as new_zip:
                for file_info in zip_ref.infolist():
                    with zip_ref.open(file_info.filename) as f:
                        data = f.read()
                    
                    # 處理內容
                    processed_data = process_content_by_structure(data, new_client, new_part, z_vals)
                    
                    # 處理檔名：使用 Regex 匹配模式，不抓特定編號
                    # 邏輯：將檔名中第一個 '#' 之前的字串全部替換掉
                    old_filename = file_info.filename
                    if "#" in old_filename:
                        # 抓取路徑中最後一個斜槓之後、井字號之前的檔名部分
                        path_parts = old_filename.split('/')
                        last_part = path_parts[-1]
                        if "#" in last_part:
                            new_last_part = re.sub(r'^.*?#', f"{new_part}#", last_part)
                            path_parts[-1] = new_last_part
                            new_name = "/".join(path_parts)
                        else:
                            new_name = old_filename
                    else:
                        # 如果是資料夾名稱或不含 # 的設定檔，執行關鍵字保險取代
                        new_name = old_filename.replace("31ABC001-001AFA", new_part)
                    
                    new_zip.writestr(new_name, processed_data)
        
        st.success("✅ 結構化生成完成！")
        st.download_button("📥 下載", data=output_buffer.getvalue(), file_name=f"{new_part}_Final.zip")
