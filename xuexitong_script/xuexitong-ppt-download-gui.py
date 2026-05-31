import os, threading, shutil, tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
import requests
from fpdf import FPDF
from PIL import Image, ImageTk


def download_pictures(base_url, start, end, dest, log):
    for i in range(start, end + 1):
        try:
            r = requests.get(f"{base_url}{i}.png")
            r.raise_for_status()
            with open(f"{dest}/{i}.png", "wb") as f:
                f.write(r.content)
            log(f"  {i}.png")
        except requests.RequestException as e:
            log(f"  ✗ {i}.png: {e}")
            return False
    return True


def make_pdf(src, dst, name, start, end, log):
    log("生成 PDF...")
    pages = [f"{src}/{i}.png" for i in range(start, end + 1)]
    for p in pages:
        if not os.path.exists(p):
            log(f"  缺少 {p}")
            return False
    im = Image.open(pages[0])
    pdf = FPDF(unit="pt", format=im.size)
    for p in pages:
        im = Image.open(p)
        pdf.add_page()
        pdf.image(p, 0, 0, *im.size)
    pdf.output(f"{dst}/{name}", "F")
    log(f"✓ {name}")
    return True


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("学习通 PPT 下载") # 窗口标题
        self.root.geometry("520x480") # 窗口默认大小
        self.root.minsize(520, 480) # 窗口最小尺寸，只能放大不能缩小
        self.root.resizable(True, True) # 窗口允许调整大小

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.pdf_dir = os.path.join(self.base_dir, "out_pdf") # PDF 输出目录
        os.makedirs(self.pdf_dir, exist_ok=True)

        # 字体检测：按偏好顺序匹配系统可用中文字体
        families = tkfont.families()
        for font_name in ["song ti", "fangsong ti", "Noto Sans CJK SC", "WenQuanYi Micro Hei", "微软雅黑", "SimHei", "TkDefaultFont"]:
            if font_name in families:
                self.font_family = font_name
                break
        else:
            self.font_family = "TkDefaultFont"

        style = ttk.Style()
        style.theme_use("clam") # ttk 主题
        style.configure(".", font=(self.font_family, 16)) # 全局字体大小
        style.configure("TButton", padding=(12, 6)) # 按钮内边距
        style.configure("Title.TLabel", font=(self.font_family, 20, "bold")) # 标题字号
        style.configure("Hint.TLabel", font=(self.font_family, 12), foreground="#888") # 提示字号

        self._build()
        self.running = False

    def _build(self):
        pad = {"padx": 16, "pady": (0, 4)}
        f = self.root

        # Logo
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "logo.png") # 脚本 logo
        iconphoto='logo.png'
        if os.path.exists(logo_path):
            img = Image.open(logo_path)
            img.thumbnail((80, 80))
            self._logo = ImageTk.PhotoImage(img)
            ttk.Label(f, image=self._logo).pack(pady=(12, 0))

        ttk.Label(f, text="学习通 PPT 下载", style="Title.TLabel").pack(anchor=tk.W, **pad)

        # URL row
        ttk.Label(f, text="基础 URL").pack(anchor=tk.W, **pad)
        url_row = ttk.Frame(f)
        url_row.pack(fill=tk.X, padx=16)
        self.url = ttk.Entry(url_row)
        self.url.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.detect_btn = ttk.Button(url_row, text="检测页数", command=self._detect_pages)
        self.detect_btn.pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Label(f, text="通过浏览器查找对应课程的图像源 -> 链接保留到 \"thumb/\" 即可。",
                 style="Hint.TLabel").pack(anchor=tk.W, padx=16, pady=(0, 8))

        # Page + filename row
        row = ttk.Frame(f)
        row.pack(fill=tk.X, padx=16, pady=4)
        ttk.Label(row, text="页码").pack(side=tk.LEFT)
        self.s = ttk.Entry(row, width=8)
        self.s.pack(side=tk.LEFT, padx=(4, 4))
        ttk.Label(row, text="—>").pack(side=tk.LEFT)
        self.e = ttk.Entry(row, width=8)
        self.e.pack(side=tk.LEFT, padx=4)
        ttk.Label(row, text="文件名").pack(side=tk.LEFT, padx=(20, 4))
        self.name = ttk.Entry(row, width=14)
        self.name.insert(0, "test")
        self.name.pack(side=tk.LEFT)
        ttk.Label(row, text=".pdf").pack(side=tk.LEFT)

        # 日志进程
        self.log = tk.Text(f, height=8, state=tk.DISABLED, font=("Consolas", 10), # 日志区域：字体 Consolas 10号
                           relief=tk.FLAT, bg="#f5f5f5")
        self.log.pack(fill=tk.BOTH, expand=True, padx=16, pady=(8, 4))

        # Progress
        self.bar = ttk.Progressbar(f, mode="indeterminate")

        # Buttons
        row2 = ttk.Frame(f)
        row2.pack(fill=tk.X, padx=16, pady=(4, 12))
        self.btn = ttk.Button(row2, text="开始下载", command=self._start)
        self.btn.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(row2, text="打开目录", command=self._open).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(row2, text="清除缓存", command=self._open_cleaner).pack(side=tk.LEFT)

    def _log(self, msg):
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)
        self.root.update_idletasks()

    def _start(self):
        url = self.url.get().strip()
        if not url:
            return messagebox.showwarning("", "请输入基础 URL")
        if not url.endswith("/"):
            url += "/"
        try:
            s, e = int(self.s.get()), int(self.e.get())
        except ValueError:
            return messagebox.showwarning("", "页码必须为数字")
        if s > e:
            return messagebox.showwarning("", "起始页码不能大于结束页码")
        name = (self.name.get().strip() or "test") + ".pdf"

        self.btn.configure(state=tk.DISABLED)
        self.bar.pack(fill=tk.X, padx=16)
        self.bar.start()
        self.log.configure(state=tk.NORMAL)
        self.log.delete(1.0, tk.END)
        self.log.configure(state=tk.DISABLED)
        self.running = True
        threading.Thread(target=self._run, args=(url, s, e, name), daemon=True).start()

    def _detect_pages(self):
        url = self.url.get().strip()
        if not url:
            return messagebox.showwarning("", "请输入基础 URL")
        if not url.endswith("/"):
            url += "/"
        self.detect_btn.configure(state=tk.DISABLED, text="检测中...")
        self._log("正在检测页数...")
        threading.Thread(target=self._do_detect, args=(url,), daemon=True).start()

    def _do_detect(self, url):
        try:
            r = requests.head(f"{url}1.png", timeout=5)
            if r.status_code >= 400:
                return self.root.after(0, self._update_pages, 0)
        except requests.RequestException:
            return self.root.after(0, self._update_pages, 0)

        hi = 1
        while hi < 5000: # 上限 5000 页，防止无限循环
            hi *= 2
            try:
                r = requests.head(f"{url}{hi}.png", timeout=5)
                if r.status_code >= 400:
                    break
            except requests.RequestException:
                break

        lo, hi = hi // 2, hi
        while lo < hi: # 二分查找精确页数
            try:
                r = requests.head(f"{url}{mid}.png", timeout=5)
                if r.status_code < 400:
                    lo = mid
                else:
                    hi = mid - 1
            except requests.RequestException:
                hi = mid - 1
        self.root.after(0, self._update_pages, lo)

    def _update_pages(self, count):
        if count == 0:
            self._log("未检测到有效页面")
        else:
            self.s.delete(0, tk.END)
            self.s.insert(0, "1")
            self.e.delete(0, tk.END)
            self.e.insert(0, str(count))
            self._log(f"检测完成：共 {count} 页")
        self.detect_btn.configure(state=tk.NORMAL, text="检测页数")

    def _run(self, url, s, e, name):
        name_no_ext = name.replace(".pdf", "")
        img_dir = os.path.join(self.base_dir, "images", name_no_ext)
        if os.path.exists(img_dir):
            for f in os.listdir(img_dir):
                os.remove(os.path.join(img_dir, f))
        else:
            os.makedirs(img_dir)

        self._log("下载中...")
        ok = download_pictures(url, s, e, img_dir, self._log)
        if ok:
            self._log("")
            ok = make_pdf(img_dir, self.pdf_dir, name, s, e, self._log)
        self.root.after(0, self._done, ok)

    def _done(self, ok):
        self.bar.stop()
        self.bar.pack_forget()
        self.btn.configure(state=tk.NORMAL)
        self.running = False
        if ok:
            self._log("\n完成 ✓")
            messagebox.showinfo("", f"PDF 已保存到 out_pdf/")
        else:
            messagebox.showerror("", "处理失败，请检查日志")

    def _open(self):
        p = os.path.abspath(self.pdf_dir)
        if os.name == "nt":
            os.startfile(p)
        else:
            os.system(f'xdg-open "{p}"' if os.uname().sysname != "Darwin" else f'open "{p}"')

    def _open_cleaner(self):
        img_base = os.path.join(self.base_dir, "images")
        if not os.path.exists(img_base):
            return messagebox.showinfo("", "images 目录不存在")
        dirs = sorted(d for d in os.listdir(img_base)
                      if os.path.isdir(os.path.join(img_base, d)) and not d.startswith("."))
        if not dirs:
            return messagebox.showinfo("", "没有找到可清理的缓存文件夹")

        win = tk.Toplevel(self.root)
        win.title("清除缓存")
        win.geometry("420x360") # 弹窗默认大小
        win.minsize(320, 200) # 弹窗最小尺寸
        win.transient(self.root)
        win.grab_set()

        ttk.Label(win, text="选择要删除的缓存文件夹：", style="Hint.TLabel").pack(anchor=tk.W, padx=12, pady=(10, 4))

        frame = ttk.Frame(win)
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        canvas = tk.Canvas(frame, highlightthickness=0)
        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.configure(yscrollcommand=scroll.set)

        inner = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner, anchor=tk.NW)

        vars_ = []
        for d in dirs:
            var = tk.BooleanVar()
            vars_.append((d, var))
            cb = ttk.Checkbutton(inner, text=d, variable=var)
            cb.pack(anchor=tk.W, padx=8, pady=2)

        inner.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        inner.bind("<Configure>", _on_frame_configure)

        def _select_all():
            sel = any(v.get() for _, v in vars_)
            for _, v in vars_:
                v.set(not sel)

        def _delete():
            selected = [d for d, v in vars_ if v.get()]
            if not selected:
                return messagebox.showwarning("", "请先选择要删除的文件夹")
            n = len(selected)
            if not messagebox.askyesno("确认", f"确定删除选中的 {n} 个文件夹？\n此操作不可恢复。"):
                return
            for d in selected:
                shutil.rmtree(os.path.join(img_base, d), ignore_errors=True)
            win.destroy()
            self._log(f"已清理 {n} 个缓存文件夹")
            messagebox.showinfo("", f"已删除 {n} 个文件夹")

        row = ttk.Frame(win)
        row.pack(fill=tk.X, padx=12, pady=(4, 10))
        ttk.Button(row, text="全选/取消全选", command=_select_all).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(row, text="删除选中", command=_delete).pack(side=tk.LEFT)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
