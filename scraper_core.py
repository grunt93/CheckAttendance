# scraper_core.py

import os # <--- 修正：新增 os 模組導入
import time
from collections import defaultdict
from typing import Set, Dict, List, Tuple

# 引入 Selenium 相關模組
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# 引入常數和路徑函數
import config_data 

# ===============================================
#                【爬蟲核心函數】
# ===============================================

def get_driver_path(driver_name="chromedriver.exe"):
    """獲取 ChromeDriver 的路徑 (用於打包兼容性)"""
    # 調用 config_data 中的通用路徑函數
    base_path = config_data.get_app_path()
    return os.path.join(base_path, driver_name)

def scrape_and_calculate(
    account: str, 
    password: str, 
    course_factors: Dict[str, int],
    set_status_callback # 傳入 GUI 的狀態更新函式
) -> List[List[str]]:
    """
    核心爬蟲和計算邏輯
    返回整理好的表格數據 (List[List[str]])
    """
    driver = None
    set_status_callback("1/7 正在初始化瀏覽器...")
    
    try:
        # 嘗試初始化驅動
        try:
            driver = webdriver.Chrome()
        except WebDriverException:
            # 嘗試使用 PyInstaller 兼容路徑 
            driver_path = get_driver_path()
            driver = webdriver.Chrome(executable_path=driver_path)
        
        driver.get(config_data.LOGIN_URL)
        set_status_callback(f"2/7 已訪問登入頁面: {config_data.LOGIN_URL}")
        time.sleep(1) 

        # 2. 執行登入操作
        account_input = driver.find_element(By.NAME, "account")
        password_input = driver.find_element(By.NAME, "account_pass")
        sign_in_button = driver.find_element(By.NAME, "SignIn")
        
        account_input.send_keys(account)
        password_input.send_keys(password) 
        set_status_callback("3/7 帳號密碼已填寫，正在登入...")
        
        sign_in_button.click()
        time.sleep(3)
        
        # 3. 直接跳轉到目標頁面
        driver.get(config_data.TARGET_URL)
        set_status_callback(f"4/7 登入成功，已跳轉到缺曠記錄頁面: {config_data.TARGET_URL}")
        
        # 4. 擷取表格資訊
        set_status_callback(f"5/7 正在抓取表格數據...")
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, config_data.TABLE_ID))
        )
        
        table = driver.find_element(By.ID, config_data.TABLE_ID)
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        raw_data: List[Tuple[str, str]] = [] 
        if len(rows) > 1:
            for row in rows[1:]:
                cols = row.find_elements(By.TAG_NAME, "td")
                if cols:
                    course_name = cols[2].text
                    absence_status = cols[3].text
                    raw_data.append((course_name, absence_status))

        # 5. 統計數據
        set_status_callback("6/7 正在計算總結數據...")
        summary_data = defaultdict(lambda: defaultdict(float)) 
        
        for course_name, status in raw_data: 
            if status in config_data.ABSENCE_TYPES:
                summary_data[course_name][status] += 1
                summary_data[course_name]['總缺課數量'] += 1
                
        # 6. 整理最終輸出列表
        recorded_courses: Set[str] = set(summary_data.keys())
        factor_courses: Set[str] = set(course_factors.keys())
        
        final_course_list: List[str] = list(factor_courses)
        for course in sorted(list(recorded_courses - factor_courses)):
            final_course_list.append(course)
            
        output_rows = []
        
        for course_name in final_course_list:
            counts = summary_data[course_name] 
            total_absent = counts.get('總缺課數量', 0)
            factor = course_factors.get(course_name)
            calculated_days_str = "" 

            # 計算總天數
            if factor:
                if total_absent > 0:
                    calculated_days = total_absent / factor
                    calculated_days_str = f"{calculated_days:.2f}"
                else:
                    calculated_days_str = "0.00"
            else:
                 calculated_days_str = "N/A"
                 if total_absent > 0:
                     set_status_callback(f"⚠️ 警告: 課程【{course_name}】缺少應計節次，總天數無法計算 (N/A)。", is_error=True)

            row: List[str] = [course_name]
            for status in config_data.ABSENCE_TYPES:
                row.append(str(int(counts.get(status, 0)))) 
            row.append(str(int(total_absent))) 
            row.append(calculated_days_str) 
            
            output_rows.append(row)
        
        set_status_callback("7/7 資料抓取與計算完成！")
        return output_rows

    except (TimeoutException, NoSuchElementException) as e:
        set_status_callback(f"錯誤：抓取頁面元素或登入超時。請檢查帳密或網路。錯誤: {e.__class__.__name__}", is_error=True)
        return []
    except WebDriverException as e:
        set_status_callback(f"錯誤：瀏覽器驅動程式問題。請確保 Chrome 和 ChromeDriver 版本匹配。錯誤: {e.__class__.__name__}", is_error=True)
        return []
    except Exception as e:
        set_status_callback(f"發生未預期的錯誤: {e}", is_error=True)
        return []
    finally:
        if driver:
            driver.quit()