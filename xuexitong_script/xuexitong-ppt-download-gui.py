"""
学习通 PPT 辅助下载 — 程序入口
PyInstaller 打包入口
"""
import sys
import os
# 确保能正确找到同级模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from GUI import App
App().mainloop()
