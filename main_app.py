#主程式結構

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict

# 引入拆分後的模組
import config_data
import gui_elements
import scraper_core

# --- 主程式類別 ---

class MissingAttendanceApp:
    def __init__(self, master):
        self.master = master
        master.title("學務系統缺曠課查詢工具")
        
        self.show_startup_messages()

        # 載入課程因子
        self.COURSE_FACTORS = config_data.load_factors_from_file()
        
        self.create_widgets(master)
        self.set_status("準備就緒。請輸入學號和密碼。")

    def show_startup_messages(self):
        """在程式啟動時跳出提醒視窗"""
        messagebox.showinfo(
            "【重要提醒】計算總天數",
            "本系統會自動計算您的缺曠總天數。\n\n"
            "⚠️ 總天數的計算公式為：**總缺課節次 / 課程應計節次**\n\n"
            "請自行選擇是否修改 **【課程因子】** 若不修改將無法查看總天數"
        )
        
        messagebox.showinfo(
            "【系統需求】瀏覽器依賴",
            "本程式使用 Chrome 瀏覽器作為爬蟲工具。\n\n"
            "✅ 請確認您的電腦已經安裝 **Google Chrome**。\n\n"
            "如果程式無法啟動或閃退，請檢查 Chrome 瀏覽器版本是否為最新，並確保 **chromedriver.exe** 檔案與程式在同一目錄下。",
        )


    def update_factors(self, new_factors: Dict[str, int]):
        """從編輯視窗接收並更新課程因子 (供主程式使用)"""
        self.COURSE_FACTORS = new_factors

    def open_edit_factors_window(self):
        """開啟編輯課程因子視窗，調用 gui_elements 模組"""
        gui_elements.EditFactorsWindow(self.master, self.COURSE_FACTORS.copy(), self.update_factors)


    def create_widgets(self, master):
        # --- 登入資訊框架 ---
        input_frame = ttk.Frame(master, padding="10")
        input_frame.pack(fill='x')

        ttk.Label(input_frame, text="學號/帳號:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.account_entry = ttk.Entry(input_frame, width=30)
        self.account_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="密碼:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.password_entry = ttk.Entry(input_frame, width=30, show='*')
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # --- 按鈕框架 ---
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        self.run_button = ttk.Button(button_frame, text="開始查詢並計算", command=self.run_scraper)
        self.run_button.pack(side='left', padx=10)

        ttk.Button(button_frame, text="編輯課程因子", command=self.open_edit_factors_window).pack(side='left', padx=10)

        # --- 狀態訊息 ---
        self.status_label = ttk.Label(master, text="", foreground="blue", padding="10")
        self.status_label.pack(fill='x')
        
        # --- 結果顯示框架 (Treeview) ---
        result_frame = ttk.Frame(master, padding="10")
        result_frame.pack(fill='both', expand=True)
        
        # 定義 Treeview (表格)
        columns = ['課程名稱'] + config_data.ABSENCE_TYPES + ['總缺課數量', '總天數']
        self.tree = ttk.Treeview(result_frame, columns=columns, show='headings')
        
        self.tree.heading('課程名稱', text='課程名稱', anchor='w')
        self.tree.column('課程名稱', width=200, anchor='w')
        for col in config_data.ABSENCE_TYPES:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=60, anchor='center')
        self.tree.heading('總缺課數量', text='總節次')
        self.tree.column('總缺課數量', width=70, anchor='center')
        self.tree.heading('總天數', text='總天數')
        self.tree.column('總天數', width=70, anchor='center')
        
        # 添加滾動條
        vsb = ttk.Scrollbar(result_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(fill='both', expand=True)

    def set_status(self, message, is_error=False):
        """更新狀態欄的訊息和顏色"""
        self.status_label.config(text=message)
        self.status_label.config(foreground="red" if is_error else "blue")
        self.master.update_idletasks() # 強制更新介面

    def run_scraper(self):
        """點擊按鈕時執行的函數"""
        
        # 清除舊的表格數據
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        account = self.account_entry.get().strip()
        password = self.password_entry.get()
        
        if not account or not password:
            messagebox.showerror("錯誤", "請輸入學號和密碼！")
            return
            
        self.run_button.config(state=tk.DISABLED, text="查詢中...")
        self.set_status("開始運行爬蟲程式...")
        
        # 執行核心邏輯，調用 scraper_core 模組
        data = scraper_core.scrape_and_calculate(
            account, 
            password, 
            self.COURSE_FACTORS, 
            self.set_status
        )
        
        # 顯示結果到 Treeview
        if data:
            self.set_status(f"查詢完成。總計找到 {len(data)} 門課程記錄。", is_error=False)
            for row in data:
                self.tree.insert('', tk.END, values=row)
        else:
            self.set_status("查詢失敗或未找到任何缺曠記錄。", is_error=True)

        self.run_button.config(state=tk.NORMAL, text="開始查詢並計算")


if __name__ == "__main__":
    # 創建主視窗
    root = tk.Tk()
    app = MissingAttendanceApp(root)
    # 設置視窗大小
    root.geometry("700x500") 
    # 啟動主循環
    root.mainloop()