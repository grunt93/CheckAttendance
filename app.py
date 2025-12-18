from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
import time
from collections import defaultdict 

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

# 課程應計節次因子 (根據您提供的範例.txt資訊)
COURSE_FACTORS = {
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
    
    raw_data = [] 
    
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
            # 1. 計算總節次數 (總缺課數量)
            summary_data[course_name][status] += 1
            summary_data[course_name]['總缺課數量'] += 1
            
    # 6. 列印計算後的總結表格
    
    print("\n" + "="*85)
    print("                   【缺曠記錄總結與計算結果】")
    print("="*85)
    
    if COURSE_FACTORS:
        # 準備要顯示的欄位 
        columns = ['課程名稱'] + absence_types + ['總缺課數量', '總天數']
        output_rows = [columns]
        
        # 關鍵修改：迭代 COURSE_FACTORS 的鍵，確保輸出包含所有設定的課程名稱
        for course_name in COURSE_FACTORS.keys():
            # 即使該課程沒有缺課記錄，defaultdict 機制也會返回一個空的 defaultdict(float)
            counts = summary_data[course_name] 

            total_absent = counts.get('總缺課數量', 0)
            factor = COURSE_FACTORS.get(course_name)
            calculated_days = 0.0

            # 計算總天數：總缺課數量 / 應計節次 (如果因子存在且缺課數大於 0)
            if factor and total_absent > 0:
                calculated_days = total_absent / factor

            row = [course_name]
            for status in absence_types:
                row.append(int(counts.get(status, 0))) # 節次數量為整數
            row.append(int(total_absent)) # 總節次數量為整數
            
            # 總天數為浮點數，格式化為小數點後兩位
            row.append(f"{calculated_days:.2f}") 
            output_rows.append(row)
            
        # 格式化輸出
        str_output_rows = [[str(item) for item in row] for row in output_rows]

        # 計算每個欄位的最大寬度
        col_widths = [max(len(item) for item in col) for col in zip(*str_output_rows)]
        col_widths[0] = max(col_widths[0], 12) 

        for i, row in enumerate(str_output_rows):
            formatted_row = " | ".join(f"{item:<{col_widths[j]}}" for j, item in enumerate(row))
            print(formatted_row)
            if i == 0:
                print("-" * (sum(col_widths) + 3 * (len(col_widths) - 1)))
    else:
        print("COURSE_FACTORS 字典為空，請定義課程資訊。")
        
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