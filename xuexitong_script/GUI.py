import os
import sys
import queue
import threading
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox

from mainScript import (
    download_picture,
    convert_images_to_pdf,
    detect_total_pages,
    clean_cache,
    sanitize_filename,
    is_valid_url,
)


if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
    RES_DIR = sys._MEIPASS
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    RES_DIR = os.path.dirname(os.path.abspath(__file__))

# 主背景色（淡灰）
BG_COLOR = "#f0f0f0"
# 输入框和日志区域背景色（纯白）
FG_COLOR = "#ffffff"


class QueueWriter:
    """
    跨线程安全的 stdout 替代品
    工作线程写入 queue，主线程每隔 50ms 轮询并刷新到 Text 组件
    """
    def __init__(self, log_queue):
        self.queue = log_queue

    def write(self, message):
        if message:
            self.queue.put(("log", message))

    def flush(self):
        pass


class App(tk.Tk):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.title("学习通 PPT 辅助下载  - Github.com/freeShao")
        self.geometry("680x620")
        self.minsize(680, 620)
        self.resizable(True, True)
        self.configure(bg=BG_COLOR)

        icon_path = os.path.join(RES_DIR, "docs", "logo.png")
        if os.path.exists(icon_path):
            self.tk.call("wm", "iconphoto", self._w, tk.PhotoImage(file=icon_path))

        # 状态变量
        self.url_var = tk.StringVar()
        self.start_var = tk.StringVar()          # 初始为空
        self.end_var = tk.StringVar()            # 初始为空
        self.name_var = tk.StringVar(value="test")

        self._running = False
        self.log_queue = queue.Queue()

        # 自动检测系统可用的中文字体
        self.font_cn = self._detect_cjk_font()

        self._setup_ui()
        self.after(50, self._process_log_queue)

    # ===================== 界面布局 =====================

    def _setup_ui(self):
        self._build_title()
        self._build_inputs()
        self._build_actions()
        self._build_cache()
        self._build_log()

    def _make_label(self, parent, text, **kw):
        kw.setdefault("font", (self.font_cn, 12))
        kw.setdefault("bg", BG_COLOR)
        return tk.Label(parent, text=text, **kw)

    def _make_entry(self, parent, variable, **kw):
        kw.setdefault("font", (self.font_cn, 12))
        kw.setdefault("bg", FG_COLOR)
        kw.setdefault("relief", tk.SUNKEN)
        kw.setdefault("bd", 2)
        return tk.Entry(parent, textvariable=variable, **kw)

    def _build_title(self):
        frame = tk.Frame(self, bg=BG_COLOR)
        frame.pack(pady=(12, 2))

        tk.Label(
            frame, text="学习通 PPT 辅助下载",
            fg="#c0392b", font=(self.font_cn, 24, "bold"),
            bg=BG_COLOR
        ).pack()

        tk.Label(
            frame,
            text="Github.com/freeShao/Learning-action/xuexitong_script",
            fg="#555555", font=(self.font_cn, 11),
            bg=BG_COLOR
        ).pack()

    def _build_inputs(self):
        frame = tk.Frame(self, bg=BG_COLOR)
        frame.pack(fill=tk.X, padx=20, pady=6)

        # URL
        self._make_label(frame, "图片基础 URL：")\
            .grid(row=0, column=0, sticky=tk.W, pady=3)
        self._make_entry(frame, self.url_var, width=62)\
            .grid(row=0, column=1, columnspan=2, sticky=tk.W, padx=(5, 0), pady=3)

        # 起始 / 结束 / 检测按钮
        sub = tk.Frame(frame, bg=BG_COLOR)
        sub.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=3)

        self._make_label(sub, "起始页：").grid(row=0, column=0, sticky=tk.W)
        self._make_entry(sub, self.start_var, width=10)\
            .grid(row=0, column=1, padx=(5, 0))

        tk.Label(sub, text="  ", bg=BG_COLOR)\
            .grid(row=0, column=2, padx=(8, 4))

        self._make_label(sub, "结束页：").grid(row=0, column=3, sticky=tk.W)
        self._make_entry(sub, self.end_var, width=10)\
            .grid(row=0, column=4, padx=(5, 0))

        self.btn_detect = tk.Button(
            sub, text="自动检测页数",
            command=self._detect_pages,
            font=(self.font_cn, 11), padx=5, bg="#607D8B", fg="white",
            relief=tk.RAISED, bd=2
        )
        self.btn_detect.grid(row=0, column=5, padx=(10, 0))

        # PDF 文件名
        self._make_label(frame, "PDF 文件名：")\
            .grid(row=2, column=0, sticky=tk.W, pady=3)
        self._make_entry(frame, self.name_var, width=28)\
            .grid(row=2, column=1, columnspan=2, sticky=tk.W, padx=(5, 0), pady=3)

    def _build_actions(self):
        frame = tk.Frame(self, bg=BG_COLOR)
        frame.pack(pady=6)

        self.btn_start = tk.Button(
            frame, text="开始下载并生成 PDF",
            command=self._start_task,
            bg="#27AE60", fg="white",
            font=(self.font_cn, 14, "bold"),
            padx=14, pady=4, relief=tk.RAISED, bd=2
        )
        self.btn_start.pack(side=tk.LEFT, padx=6)

    def _build_cache(self):
        """缓存清理区域：管理 images/ 下的子目录"""
        frame = tk.Frame(self, relief=tk.GROOVE, bd=1, bg=BG_COLOR)
        frame.pack(fill=tk.X, padx=20, pady=5)

        inner = tk.Frame(frame, bg=BG_COLOR)
        inner.pack(padx=10, pady=6, fill=tk.X)

        # 标题
        tk.Label(inner, text="缓存清理", font=(self.font_cn, 12, "bold"),
                 bg=BG_COLOR, fg="#c0392b")\
            .grid(row=0, column=0, sticky=tk.W, pady=2)

        # 子目录列表（含滚动条）
        list_frame = tk.Frame(inner, bg=BG_COLOR)
        list_frame.grid(row=1, column=0, columnspan=5, sticky=tk.W+tk.E, pady=4)

        self.cache_listbox = tk.Listbox(list_frame, height=3, width=50,
                                        font=(self.font_cn, 11), bg=FG_COLOR,
                                        selectmode=tk.SINGLE, exportselection=False)
        self.cache_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scb = tk.Scrollbar(list_frame, command=self.cache_listbox.yview)
        scb.pack(side=tk.RIGHT, fill=tk.Y)
        self.cache_listbox.config(yscrollcommand=scb.set)

        # 按钮行
        btn_frame = tk.Frame(inner, bg=BG_COLOR)
        btn_frame.grid(row=2, column=0, columnspan=5, pady=4)

        self.btn_refresh = tk.Button(
            btn_frame, text="刷新目录列表",
            command=self._refresh_cache_list,
            font=(self.font_cn, 11), padx=6, bg="#455A64", fg="white",
            relief=tk.RAISED, bd=2
        )
        self.btn_refresh.pack(side=tk.LEFT, padx=3)

        self.btn_del_folder = tk.Button(
            btn_frame, text="删除选中文件夹",
            command=self._delete_selected_folder,
            font=(self.font_cn, 11), padx=6, bg="#E67E22", fg="white",
            relief=tk.RAISED, bd=2
        )
        self.btn_del_folder.pack(side=tk.LEFT, padx=3)

        self.btn_clean_all = tk.Button(
            btn_frame, text="清空全部缓存",
            command=self._clean_all_cache,
            font=(self.font_cn, 11), padx=6, bg="#C0392B", fg="white",
            relief=tk.RAISED, bd=2
        )
        self.btn_clean_all.pack(side=tk.LEFT, padx=3)

    def _build_log(self):
        frame = tk.Frame(self, bg=BG_COLOR)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        self._make_label(frame, "运行日志：")\
            .pack(anchor=tk.W)

        txt_frame = tk.Frame(frame, bg=BG_COLOR)
        txt_frame.pack(fill=tk.BOTH, expand=True)

        self.text_log = tk.Text(txt_frame, height=10, font=("Consolas", 9),
                                bg=FG_COLOR, relief=tk.SUNKEN, bd=2,
                                state=tk.DISABLED)
        self.text_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scb = tk.Scrollbar(txt_frame, command=self.text_log.yview)
        scb.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_log.config(yscrollcommand=scb.set)

    # ===================== 内部工具 =====================

    def _detect_cjk_font(self):
        """
        自动检测系统可用的中文字体
        按优先级尝试各平台的 CJK 字体，返回第一个可用的字体名
        全平台通用：Linux（X11 位图）、Windows、macOS
        """
        candidates = [
            # Linux X11 核心 CJK 位图字体（GB2312 编码，覆盖 6763 个汉字）
            "song ti", "fangsong ti", "mincho", "gothic",
            # Windows 系统字体
            "Microsoft YaHei", "SimHei", "SimSun",
            # macOS 系统字体
            "PingFang SC", "STHeiti",
            # 跨平台 fontconfig 字体（需要 Tk 支持 XFT）
            "Noto Sans CJK SC", "Droid Sans Fallback",
            "WenQuanYi Micro Hei", "WenQuanYi Zen Hei",
        ]
        try:
            available = set(tkfont.families())
            for name in candidates:
                if name in available:
                    f = tkfont.Font(family=name, size=12)
                    if f.actual()["family"] == name:
                        return name
        except Exception:
            pass
        return "fixed"

    def _clear_log(self):
        self.text_log.config(state=tk.NORMAL)
        self.text_log.delete(1.0, tk.END)
        self.text_log.config(state=tk.DISABLED)

    def _log(self, message):
        """主线程安全地追加日志"""
        self.text_log.config(state=tk.NORMAL)
        self.text_log.insert(tk.END, message)
        self.text_log.see(tk.END)
        self.text_log.config(state=tk.DISABLED)

    def _process_log_queue(self):
        """主线程轮询：50ms 间隔读取队列并刷新 UI"""
        try:
            while True:
                msg_type, msg = self.log_queue.get_nowait()
                if msg_type == "log":
                    self._log(msg)
                elif msg_type == "done":
                    self._running = False
                    self.btn_start.config(state=tk.NORMAL, text="开始下载并生成 PDF")
                elif msg_type == "detect_result":
                    self._log(msg)
        except queue.Empty:
            pass
        self.after(50, self._process_log_queue)

    def _get_images_dir(self):
        path = os.path.join(APP_DIR, "images")
        os.makedirs(path, exist_ok=True)
        return os.path.abspath(path)

    def _refresh_cache_list(self):
        """刷新缓存子目录列表"""
        self.cache_listbox.delete(0, tk.END)
        img_dir = self._get_images_dir()
        try:
            entries = sorted(os.listdir(img_dir))
            for name in entries:
                full = os.path.join(img_dir, name)
                if os.path.isdir(full):
                    self.cache_listbox.insert(tk.END, name)
        except OSError:
            pass

    # ===================== 页数检测 =====================

    def _detect_pages(self):
        base_url = self.url_var.get().strip()
        if not base_url:
            messagebox.showwarning("输入错误", "请先输入图片基础 URL")
            return
        if not is_valid_url(base_url):
            messagebox.showwarning("输入错误", "URL 格式无效")
            return

        self._log(f"[检测] 开始检测页数: {base_url}\n")

        thread = threading.Thread(target=self._do_detect, args=(base_url,), daemon=True)
        thread.start()

    def _do_detect(self, base_url):
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout = QueueWriter(self.log_queue)
        sys.stderr = QueueWriter(self.log_queue)
        try:
            pages = detect_total_pages(base_url)
            if pages > 0:
                self.log_queue.put(("detect_result", f"[检测] 检测完成，共 {pages} 页\n"))
            else:
                self.log_queue.put(("detect_result", "[检测] 页数检测失败，请检查 URL 后重试\n"))
        except Exception as e:
            self.log_queue.put(("detect_result", f"[检测] 出错: {e}\n"))
        finally:
            sys.stdout, sys.stderr = old_out, old_err

    # ===================== 下载 + PDF 生成 =====================

    def _start_task(self):
        base_url = self.url_var.get().strip()
        start_str = self.start_var.get().strip()
        end_str = self.end_var.get().strip()
        file_name = self.name_var.get().strip()

        if not base_url:
            messagebox.showwarning("输入错误", "请输入图片基础 URL")
            return
        if not is_valid_url(base_url):
            messagebox.showwarning("输入错误", "URL 格式无效")
            return
        if not start_str.isdigit() or not end_str.isdigit():
            messagebox.showwarning("输入错误", "起始页和结束页必须为数字")
            return

        start = int(start_str)
        end = int(end_str)

        if start < 1:
            messagebox.showwarning("输入错误", "起始页必须大于 0")
            return
        if start > end:
            messagebox.showwarning("输入错误", "起始页不能大于结束页")
            return
        if end - start > 5000:
            if not messagebox.askyesno(
                "确认",
                f"页码范围过大 ({start}-{end}，共 {end-start+1} 页)，\n"
                "继续可能导致长时间运行，确定继续吗？"
            ):
                return

        safe_name = sanitize_filename(file_name) if file_name else "output"

        if self._running:
            messagebox.showinfo("提示", "当前有任务正在运行，请等待完成")
            return

        path_img = self._get_images_dir()
        path_pdf = os.path.join(APP_DIR, "out_pdf")
        os.makedirs(path_pdf, exist_ok=True)

        self._running = True
        self.btn_start.config(state=tk.DISABLED, text="正在运行...")

        thread = threading.Thread(
            target=self._run_task,
            args=(start, end, path_img, base_url, path_pdf, safe_name),
            daemon=True,
        )
        thread.start()

    def _run_task(self, start, end, path_img, base_url, path_pdf, file_name):
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout = QueueWriter(self.log_queue)
        sys.stderr = QueueWriter(self.log_queue)

        try:
            print("=" * 50)
            print("任务开始")
            print(f"图片基础 URL：{base_url}")
            print(f"页码范围：{start} ~ {end}")
            print(f"PDF 文件名：{file_name}.pdf")
            print("=" * 50)

            print("\n>>> 开始下载图片...")
            download_picture(start, end, path_img, base_url)

            print("\n>>> 开始生成 PDF...")
            output_pdf = file_name + ".pdf"
            convert_images_to_pdf(path_img, output_pdf, path_pdf, start, end)

            print("\n" + "=" * 50)
            print(f"全部完成！PDF 文件已保存至：{os.path.join(path_pdf, output_pdf)}")
            print("=" * 50)
        except Exception as e:
            print(f"\n!!! 任务执行过程中发生错误：{e}")
        finally:
            sys.stdout, sys.stderr = old_out, old_err
            self.log_queue.put(("done", ""))

    # ===================== 缓存清理 =====================

    def _delete_selected_folder(self):
        selection = self.cache_listbox.curselection()
        if not selection:
            messagebox.showinfo("缓存清理", "请先在列表中选择一个文件夹")
            return

        folder_name = self.cache_listbox.get(selection[0])
        img_dir = self._get_images_dir()
        target = os.path.join(img_dir, folder_name)

        if not os.path.isdir(target):
            messagebox.showerror("错误", f"目录不存在: {folder_name}")
            self._refresh_cache_list()
            return

        msg = f"将删除文件夹及其全部内容：\n  {folder_name}\n\n确定继续吗？"
        if not messagebox.askyesno("确认删除", msg, icon="warning"):
            return

        thread = threading.Thread(
            target=self._do_delete_folder, args=(target, folder_name), daemon=True
        )
        thread.start()

    def _do_delete_folder(self, target, folder_name):
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout = QueueWriter(self.log_queue)
        sys.stderr = QueueWriter(self.log_queue)
        try:
            import shutil
            shutil.rmtree(target)
            print(f"[清理] 已删除文件夹: {folder_name}")
        except Exception as e:
            print(f"[清理] 删除失败: {e}")
        finally:
            sys.stdout, sys.stderr = old_out, old_err
            self.after(0, self._refresh_cache_list)

    def _clean_all_cache(self):
        img_dir = self._get_images_dir()
        entries = []
        try:
            entries = [d for d in os.listdir(img_dir)
                       if os.path.isdir(os.path.join(img_dir, d))]
        except OSError:
            pass

        if not entries:
            messagebox.showinfo("缓存清理", "缓存目录已为空")
            return

        msg = f"将清空以下 {len(entries)} 个文件夹：\n" + "\n".join(f"  • {d}" for d in entries)
        msg += "\n\n此操作不可撤销，确定继续吗？"
        if not messagebox.askyesno("确认清空", msg, icon="warning"):
            return

        thread = threading.Thread(
            target=self._do_clean_all, args=(img_dir, entries), daemon=True
        )
        thread.start()

    def _do_clean_all(self, img_dir, entries):
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout = QueueWriter(self.log_queue)
        sys.stderr = QueueWriter(self.log_queue)
        try:
            import shutil
            for name in entries:
                full = os.path.join(img_dir, name)
                if os.path.isdir(full):
                    shutil.rmtree(full)
                    print(f"[清理] 已删除文件夹: {name}")
            print(f"[清理] 共删除 {len(entries)} 个文件夹")
        except Exception as e:
            print(f"[清理] 出错: {e}")
        finally:
            sys.stdout, sys.stderr = old_out, old_err
            self.after(0, self._refresh_cache_list)


if __name__ == "__main__":
    app = App()
    app.mainloop()
