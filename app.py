from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
import time
from collections import defaultdict # 用於方便地初始化計數器

# ===============================================
#                【設定變數區】
# ===============================================

# 替換成您的目標登入頁面網址
LOGIN_URL = "https://std.uch.edu.tw/Std_Xerox/Login_Index.aspx" 
YOUR_ACCOUNT = "D11213201" # 替換成您的學號/帳號
MY_PASSWORD = "Gg0976682163" # 替換成您的密碼

# 登入成功後要跳轉的目標網址 (缺曠記錄頁面)
TARGET_URL = "https://std.uch.edu.tw/Std_Xerox/Miss_ct.aspx" 

# 缺曠記錄表格的 ID (來自您提供的 HTML 內容)
TABLE_ID = "ctl00_ContentPlaceHolder1_gw_absent"

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
    
    # 等待表格元素出現 (最多 10 秒)，確保頁面已載入
    print(f"等待表格 ({TABLE_ID}) 載入...")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, TABLE_ID))
    )
    
    # 找到表格元素
    table = driver.find_element(By.ID, TABLE_ID)
    
    # 抓取所有行 (Row)
    rows = table.find_elements(By.TAG_NAME, "tr")
    
    raw_data = []
    
    # 抓取資料行 (從第二行開始，忽略表頭)
    if len(rows) > 1:
        for row in rows[1:]:
            cols = row.find_elements(By.TAG_NAME, "td")
            if cols:
                # 抓取：[課程名稱(索引2), 狀態(索引3)]
                course_name = cols[2].text
                absence_status = cols[3].text
                raw_data.append((course_name, absence_status))

    # 5. 統計數據
    
    # 使用 defaultdict(lambda: defaultdict(int)) 來計數
    # 結構: {課程名稱: {狀態: 數量, 總計: 數量}}
    summary_data = defaultdict(lambda: defaultdict(int))
    absence_types = ['事假', '病假', '遲到', '曠課'] # 依據範例文件定義的順序
    
    for course_name, status in raw_data:
        if status in absence_types:
            summary_data[course_name][status] += 1
            summary_data[course_name]['總缺課數量'] += 1
    
    # 6. 列印計算後的總結表格
    
    print("\n" + "="*80)
    print("                 【缺曠記錄總結與計算結果】")
    print("="*80)
    
    if summary_data:
        # 準備要顯示的欄位
        columns = ['課程名稱'] + absence_types + ['總缺課數量']
        output_rows = [columns]
        
        for course_name, counts in summary_data.items():
            row = [course_name]
            for status in absence_types:
                row.append(counts.get(status, 0)) # 取得假別數量，若無則為 0
            row.append(counts.get('總缺課數量', 0)) # 取得總缺課數量
            output_rows.append(row)
            
        # 格式化輸出
        # 將所有數值轉換為字串以便計算長度
        str_output_rows = [[str(item) for item in row] for row in output_rows]

        # 計算每個欄位的最大寬度
        col_widths = [max(len(item) for item in col) for col in zip(*str_output_rows)]
        # 確保「課程名稱」欄位有足夠的最小寬度
        col_widths[0] = max(col_widths[0], 12) 

        for i, row in enumerate(str_output_rows):
            # 格式化並列印行
            formatted_row = " | ".join(f"{item:<{col_widths[j]}}" for j, item in enumerate(row))
            print(formatted_row)
            if i == 0:
                # 在標題下方列印分隔線
                print("-" * (sum(col_widths) + 3 * (len(col_widths) - 1)))
    else:
        print("未找到缺曠記錄或表格中沒有資料。")
        
    print("="*80)
    
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