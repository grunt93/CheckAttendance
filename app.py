from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
import time
from collections import defaultdict 
from typing import Set, Dict, Any, List

# ===============================================
#                【設定變數區】
# ===============================================

# 替換成您的目標登入頁面網址
LOGIN_URL = "https://std.uch.edu.tw/Std_Xerox/Login_Index.aspx" 
YOUR_ACCOUNT = "D11213201" # 替換成您的學號/帳號
MY_PASSWORD = "Gg0976682163" # 替換成您的密碼

# 登入成功後要跳轉的目標網址 (缺曠記錄頁面)
TARGET_URL = "https://std.uch.edu.tw/Std_Xerox/Miss_ct.aspx" 

# 缺曠記錄表格的 ID
TABLE_ID = "ctl00_ContentPlaceHolder1_gw_absent"

# 課程應計節次因子 (作為主要列印清單)
COURSE_FACTORS: Dict[str, int] = {
    "程式設計與應用(三)": 4,
    "資料庫系統與實習": 2,
    "網頁資料庫程式開發實作": 4,
    "廣域網路與實習": 4,
    "性別與文化": 2,
    "RHCE紅帽Linux系統自動化": 4, 
}

try:
    # 1. 初始化瀏覽器並訪問登入頁面
    driver = webdriver.Chrome()
    driver.get(LOGIN_URL)
    print(f"已成功訪問登入頁面: {LOGIN_URL}")
    
    # 2. 執行登入操作
    account_input = driver.find_element(By.NAME, "account")
    password_input = driver.find_element(By.NAME, "account_pass")
    sign_in_button = driver.find_element(By.NAME, "SignIn")
    
    account_input.send_keys(YOUR_ACCOUNT)
    password_input.send_keys(MY_PASSWORD) 
    print("帳號密碼已填寫完畢。")
    
    sign_in_button.click()
    print("已點擊登入按鈕。")
        
    # 給予伺服器一點時間處理登入請求並跳轉 (例如 3 秒)
    print("等待 3 秒讓登入流程完成...")
    time.sleep(3)
    
    # 3. 直接跳轉到目標頁面 (Miss_ct.aspx)
    driver.get(TARGET_URL)
    print(f"✅ 已直接跳轉到目標頁面: {TARGET_URL}")
    
    # 4. 擷取表格資訊
    
    # 等待表格元素出現 (最多 10 秒)
    print(f"等待表格 ({TABLE_ID}) 載入...")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, TABLE_ID))
    )
    
    table = driver.find_element(By.ID, TABLE_ID)
    rows = table.find_elements(By.TAG_NAME, "tr")
    
    raw_data: List[Any] = [] 
    
    if len(rows) > 1:
        for row in rows[1:]:
            cols = row.find_elements(By.TAG_NAME, "td")
            if cols:
                # 抓取：[課程名稱(索引2), 狀態(索引3)]
                course_name = cols[2].text
                absence_status = cols[3].text
                raw_data.append((course_name, absence_status))

    # 5. 統計數據
    
    # 結構: {課程名稱: {狀態: 數量, 總缺課數量: 數量}}
    summary_data = defaultdict(lambda: defaultdict(float)) 
    absence_types = ['事假', '病假', '遲到', '曠課'] 
    
    # 遍歷原始資料 (課程名稱, 狀態)
    for course_name, status in raw_data: 
        if status in absence_types:
            # 計算總節次數 (總缺課數量)
            summary_data[course_name][status] += 1
            summary_data[course_name]['總缺課數量'] += 1
            
    # 6. 列印計算後的總結表格
    
    print("\n" + "="*85)
    print("                   【缺曠記錄總結與計算結果】")
    print("="*85)
    
    # --- 聯集邏輯 ---
    # 1. 取得所有在網頁上有記錄的課程名稱 (集合 A)
    recorded_courses: Set[str] = set(summary_data.keys())
    # 2. 取得所有在 COURSE_FACTORS 中定義的課程名稱 (集合 B)
    factor_courses: Set[str] = set(COURSE_FACTORS.keys())
    
    # 3. 創建聯集 (A U B)，並進行排序，以 factor_courses 為優先順序
    # 將 factor_courses 放在前面，確保它們的順序優先
    # 這裡使用 factor_courses + 額外記錄的課程（去重）來決定輸出的順序
    all_courses_set = factor_courses.union(recorded_courses)
    
    # 將 COURSE_FACTORS 中的課程放在前面，然後是其他有記錄的課程
    # 為了保持一定的順序性 (例如按字母排序)，這裡我們使用排序後的集合
    # 否則直接使用 list(all_courses_set) 順序會比較隨機
    
    # 優先保持 COURSE_FACTORS 的定義順序，然後是其他課程的字母順序
    final_course_list: List[str] = list(factor_courses)
    for course in sorted(list(recorded_courses - factor_courses)):
        final_course_list.append(course)
    # --- 聯集邏輯結束 ---


    if final_course_list:
        # 準備要顯示的欄位 
        columns = ['課程名稱'] + absence_types + ['總缺課數量', '總天數']
        output_rows = [columns]
        
        for course_name in final_course_list:
            # 即使課程不在 summary_data 中 (例如: 該課程在 COURSE_FACTORS 但無缺曠記錄)
            # defaultdict 機制會返回一個空的計數器 (所有數值為 0.0)
            counts = summary_data[course_name] 

            total_absent = counts.get('總缺課數量', 0)
            factor = COURSE_FACTORS.get(course_name) # 嘗試從 COURSE_FACTORS 取得因子
            calculated_days_str = "" 

            # 計算總天數
            if factor:
                # 因子存在，計算總天數
                if total_absent > 0:
                    calculated_days = total_absent / factor
                    calculated_days_str = f"{calculated_days:.2f}"
                else:
                    calculated_days_str = "0.00"
            else:
                 # 因子不存在，顯示 N/A
                 calculated_days_str = "N/A"
                 if total_absent > 0:
                     print(f"⚠️ 警告: 課程【{course_name}】有 {int(total_absent)} 筆缺課記錄，但缺少應計節次，總天數無法計算 (N/A)。請更新 COURSE_FACTORS。")

            row = [course_name]
            for status in absence_types:
                row.append(int(counts.get(status, 0))) # 節次數量為整數
            row.append(int(total_absent)) # 總節次數量為整數
            
            row.append(calculated_days_str) # 總天數
            output_rows.append(row)
            
        # 格式化輸出
        str_output_rows = [[str(item) for item in row] for row in output_rows]

        # 計算每個欄位的最大寬度
        col_widths = [max(len(item) for item in col) for col in zip(*str_output_rows)]
        # 確保「課程名稱」欄位有足夠的最小寬度
        col_widths[0] = max(col_widths[0], 12) 

        for i, row in enumerate(str_output_rows):
            formatted_row = " | ".join(f"{item:<{col_widths[j]}}" for j, item in enumerate(row))
            print(formatted_row)
            if i == 0:
                print("-" * (sum(col_widths) + 3 * (len(col_widths) - 1)))
    else:
        print("未找到任何課程資訊（COURSE_FACTORS 為空且網頁上無缺曠記錄）。")
        
    print("="*85)
    
    # 7. 結束
    time.sleep(5) 
    driver.quit()
    print("\n程式執行完畢，瀏覽器已關閉。")

except Exception as e:
    print(f"初始化或整體執行過程中發生錯誤: {e}")
    try:
        driver.quit()
    except:
        pass