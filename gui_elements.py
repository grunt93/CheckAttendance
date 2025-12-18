# gui_elements.py

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict

# 引入配置與數據模組
import config_data 

# --- 編輯視窗類別 ---

class EditFactorsWindow(tk.Toplevel):
    def __init__(self, master, current_factors: Dict[str, int], update_callback):
        super().__init__(master)
        self.title("編輯課程因子 (課程名稱: 應計節次)")
        self.geometry("450x400")
        self.transient(master) 
        self.grab_set() 
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.current_factors = current_factors 
        self.update_callback = update_callback
        
        self.factor_tree = None
        self.create_widgets()
        self.populate_tree()

    def create_widgets(self):
        tree_frame = ttk.Frame(self, padding="10")
        tree_frame.pack(fill='both', expand=True)

        columns = ('課程名稱', '應計節次')
        self.factor_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        self.factor_tree.heading('課程名稱', text='課程名稱')
        self.factor_tree.column('課程名稱', width=250, anchor='w')
        self.factor_tree.heading('應計節次', text='應計節次')
        self.factor_tree.column('應計節次', width=100, anchor='center')

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.factor_tree.yview)
        vsb.pack(side='right', fill='y')
        self.factor_tree.configure(yscrollcommand=vsb.set)
        self.factor_tree.pack(fill='both', expand=True)
        
        button_frame = ttk.Frame(self, padding="10")
        button_frame.pack(fill='x')
        
        ttk.Button(button_frame, text="新增課程", command=self.add_factor).pack(side='left', padx=5)
        ttk.Button(button_frame, text="修改節次", command=self.edit_factor).pack(side='left', padx=5)
        ttk.Button(button_frame, text="移除課程", command=self.remove_factor).pack(side='left', padx=5)
        ttk.Button(button_frame, text="儲存並關閉", command=self.save_and_close).pack(side='right', padx=5)
        ttk.Button(button_frame, text="取消", command=self.on_close).pack(side='right', padx=5)

    def populate_tree(self):
        for item in self.factor_tree.get_children():
            self.factor_tree.delete(item)
            
        for name, factor in sorted(self.current_factors.items()):
            self.factor_tree.insert('', tk.END, values=(name, factor))

    def add_factor(self):
        new_name = simpledialog.askstring("新增課程", "請輸入新的課程名稱:", parent=self)
        if new_name:
            new_name = new_name.strip()
            if new_name in self.current_factors:
                messagebox.showwarning("警告", f"課程【{new_name}】已存在，請使用修改節次功能。", parent=self)
                return
                
            new_factor_str = simpledialog.askstring("新增課程", f"請輸入【{new_name}】的應計節次(一個禮拜有幾節課) (數字):", parent=self)
            try:
                if new_factor_str is None: return
                new_factor = int(new_factor_str)
                if new_factor <= 0:
                    raise ValueError
                self.current_factors[new_name] = new_factor
                self.populate_tree()
            except (TypeError, ValueError):
                messagebox.showerror("錯誤", "應計節次必須是一個正整數。", parent=self)
                
    def edit_factor(self):
        selected_item = self.factor_tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "請先選擇要修改的課程。", parent=self)
            return

        item = selected_item[0]
        current_name = self.factor_tree.item(item, 'values')[0]
        
        new_factor_str = simpledialog.askstring("修改節次", f"請輸入【{current_name}】新的應計節次 (目前為 {self.current_factors[current_name]}):", parent=self)
        
        if new_factor_str is not None:
            try:
                new_factor = int(new_factor_str)
                if new_factor <= 0:
                    raise ValueError
                self.current_factors[current_name] = new_factor
                self.populate_tree()
            except (TypeError, ValueError):
                messagebox.showerror("錯誤", "應計節次必須是一個正整數。", parent=self)

    def remove_factor(self):
        selected_item = self.factor_tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "請先選擇要移除的課程。", parent=self)
            return
            
        item = selected_item[0]
        course_name = self.factor_tree.item(item, 'values')[0]

        if messagebox.askyesno("確認移除", f"確定要移除課程【{course_name}】嗎?", parent=self):
            del self.current_factors[course_name]
            self.populate_tree()

    def save_and_close(self):
        # 調用 config_data 中的儲存函數
        config_data.save_factors_to_file(self.current_factors)
        self.update_callback(self.current_factors)
        self.destroy()

    def on_close(self):
        self.destroy()