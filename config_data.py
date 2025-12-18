# config_data.py

import os
import sys
import json
from typing import Dict
from tkinter import messagebox

# ===============================================
#                【設定常數區】
# ===============================================

CONFIG_FILE = "course_factors_config.json"
LOGIN_URL = "https://std.uch.edu.tw/Std_Xerox/Login_Index.aspx" 
TARGET_URL = "https://std.uch.edu.tw/Std_Xerox/Miss_ct.aspx" 
TABLE_ID = "ctl00_ContentPlaceHolder1_gw_absent"
ABSENCE_TYPES = ['事假', '病假', '遲到', '曠課']
DEFAULT_COURSE_FACTORS: Dict[str, int] = {} 

# --- 資料持久化函數 ---

def get_app_path():
    """獲取程式運行的基礎路徑，兼容打包後的環境"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_config_filepath():
    """獲取配置檔案的完整路徑"""
    return os.path.join(get_app_path(), CONFIG_FILE)

def load_factors_from_file() -> Dict[str, int]:
    """從檔案載入課程因子，失敗則使用預設值"""
    filepath = get_config_filepath()
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {str(k): int(v) for k, v in data.items()}
        except Exception:
            print(f"警告：載入配置檔失敗，使用預設因子。")
            return DEFAULT_COURSE_FACTORS
    return DEFAULT_COURSE_FACTORS

def save_factors_to_file(factors: Dict[str, int]):
    """將課程因子儲存到檔案"""
    filepath = get_config_filepath()
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(factors, f, ensure_ascii=False, indent=4)
        print(f"課程因子已成功儲存到: {filepath}")
    except Exception as e:
        messagebox.showerror("儲存錯誤", f"無法儲存課程因子到檔案: {e}")
        print(f"儲存錯誤: {e}")