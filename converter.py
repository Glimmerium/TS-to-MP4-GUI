import os
import sys
import queue
import shutil
import subprocess
import threading
import uuid
from collections import deque
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

BASE = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
FLAGS = getattr(subprocess, 'CREATE_NO_WINDOW', 0)


def find_engine(name):
    """Find a portable FFmpeg tool, with PATH as a final fallback."""
    for folder in (BASE / 'ffmpeg' / 'bin', BASE,
                   BASE / 'ffmpeg-9.0.2-essentials_build' / 'bin'):
        candidate = folder / name
        if candidate.is_file():
            return str(candidate)
    return shutil.which(name)


def conversion_command(source, target, mode, crf, preset):
    engine = find_engine('ffmpeg.exe')
    if engine is None:
        raise FileNotFoundError('未找到 ffmpeg.exe，请按照 README 准备 FFmpeg。')
    cmd = [engine, '-hide_banner', '-nostdin', '-y', '-i', str(source)]
    if mode == 'copy':
        cmd += ['-c', 'copy']
    else:
        cmd += ['-c:v', 'libx264', '-crf', str(crf), '-preset', preset, '-c:a', 'aac', '-b:a', '192k']
    return cmd + ['-movflags', '+faststart', '-progress', 'pipe:1', '-nostats', str(target)]


class TSConverterGUI:
    def __init__(self, root):
        self.root = root
        root.title('TS → MP4 · 视频转换器')
        root.withdraw()
        root.configure(bg='#F3F5FA')
        icon = BASE / 'converter.ico'
        if icon.exists():
            root.iconbitmap(str(icon))
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.mode = tk.StringVar(value='copy')
        self.crf = tk.DoubleVar(value=23)
        self.preset = tk.StringVar(value='medium')
        self.status = tk.StringVar(value='准备就绪')
        self.percent = tk.StringVar(value='等待选择视频')
        self.msg_queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.is_running = False
        self.close_pending = False
        self.process = None
        self.controls = []
        self._build_ui()
        self._fit_window()
        root.protocol('WM_DELETE_WINDOW', self.close)
        self._poll_queue()

    def _build_ui(self):
        s = ttk.Style()
        s.theme_use('clam')
        s.configure('.', font=('Microsoft YaHei UI', 10), background='#FFFFFF', foreground='#233149')
        s.configure('TFrame', background='#FFFFFF')
        s.configure('TLabel', background='#FFFFFF')
        s.configure('Muted.TLabel', foreground='#778296')
        s.configure('Title.TLabel', font=('Microsoft YaHei UI', 12, 'bold'))
        s.configure('TEntry', padding=9, fieldbackground='#F7F9FC', bordercolor='#DFE5EF')
        s.configure('TButton', padding=(15, 9), background='#EDF1F8', borderwidth=0)
        s.map('TButton', background=[('active', '#E0E7F4')])
        s.configure('Primary.TButton', background='#4167E8', foreground='white', font=('Microsoft YaHei UI', 11, 'bold'))
        s.map('Primary.TButton', background=[('disabled', '#ADBCEB'), ('active', '#3155CD')], foreground=[('disabled', '#FFFFFF')])
        s.configure('TRadiobutton', background='#FFFFFF', padding=(0, 4))
        s.map('TRadiobutton', background=[('active', '#FFFFFF')])
        s.configure('Horizontal.TProgressbar', background='#4167E8', troughcolor='#E9EDF5', borderwidth=0)
        # Keep conversion controls visible even on small or scaled displays.
        self.footer = tk.Frame(self.root, bg='#F3F5FA')
        self.footer.pack(side='bottom', fill='x')
        self.content = tk.Frame(self.root, bg='#F3F5FA')
        self.content.pack(fill='both', expand=True)
        header = tk.Frame(self.content, bg='#F3F5FA')
        header.pack(fill='x', padx=30, pady=(12, 8))
        logo_path = Path(getattr(sys, '_MEIPASS', BASE)) / 'personal-logo.png'
        if logo_path.exists():
            original = tk.PhotoImage(file=str(logo_path))
            factor = max(1, round(original.width() / 76))
            self.logo_image = original.subsample(factor, factor)
            tk.Button(header, image=self.logo_image, bd=0, bg='#FFFFFF',
                      activebackground='#FFFFFF', cursor='hand2',
                      command=lambda: messagebox.showinfo('关于', '本软件由化院 24 本郭嘉开发，祝使用愉快。')).pack(side='right', padx=(12, 0))
        tk.Label(header, text='TS → MP4', font=('Segoe UI', 23, 'bold'), fg='#233149', bg='#F3F5FA').pack(anchor='w')
        tk.Label(header, text='轻松转换视频，让播放与分享更简单。', font=('Microsoft YaHei UI', 10), fg='#778296', bg='#F3F5FA').pack(anchor='w', pady=(4, 0))
        files = self.card('01   选择文件')
        self.path_row(files, '输入视频', self.input_path, self.choose_input, '选择 TS 文件')
        self.path_row(files, '保存位置', self.output_path, self.choose_output, '更改位置')
        ttk.Label(files, text='默认保存在原视频旁，原始 TS 文件会保留。', style='Muted.TLabel').pack(anchor='w', pady=(5, 0))
        modes = self.card('02   转换方式')
        for value, label in [('copy', '快速无损   ·   保留原画质，通常只需短暂等待'), ('reencode', '重新编码   ·   转为 H.264 / AAC，可调整画质与体积')]:
            radio = ttk.Radiobutton(modes, text=label, variable=self.mode, value=value, command=self._toggle_options)
            radio.pack(anchor='w')
            self.controls.append(radio)
        advanced = ttk.Frame(modes)
        advanced.pack(fill='x', pady=(10, 0))
        ttk.Label(advanced, text='画质').pack(side='left')
        self.scale = ttk.Scale(advanced, from_=0, to=51, variable=self.crf, command=lambda _: self.quality.configure(text=str(round(self.crf.get()))))
        self.scale.pack(side='left', fill='x', expand=True, padx=12)
        self.quality = ttk.Label(advanced, text='23', width=4)
        self.quality.pack(side='left')
        ttk.Label(advanced, text='编码速度').pack(side='left', padx=(16, 8))
        self.combo = ttk.Combobox(advanced, textvariable=self.preset, values=['ultrafast', 'veryfast', 'fast', 'medium', 'slow', 'veryslow'], width=11, state='readonly')
        self.combo.pack(side='left')
        ttk.Label(modes, text='画质数值越小越清晰；编码越慢，通常压缩效率越高。', style='Muted.TLabel').pack(anchor='w', pady=(8, 0))
        task = self.card('03   转换进度', self.footer)
        row = ttk.Frame(task)
        row.pack(fill='x')
        ttk.Label(row, textvariable=self.status).pack(side='left')
        ttk.Label(row, textvariable=self.percent, style='Muted.TLabel').pack(side='right')
        self.progress = ttk.Progressbar(task, mode='determinate', maximum=100)
        self.progress.pack(fill='x', pady=(12, 16))
        buttons = ttk.Frame(task)
        buttons.pack(fill='x')
        self.btn_start = ttk.Button(buttons, text='开始转换', style='Primary.TButton', command=self.start_convert)
        self.btn_start.pack(side='left')
        self.btn_cancel = ttk.Button(buttons, text='取消', command=self.cancel, state='disabled')
        self.btn_cancel.pack(side='left', padx=10)
        ttk.Button(buttons, text='打开输出目录', command=self.open_output_dir).pack(side='right')
        logs = tk.Frame(self.content, bg='#F3F5FA')
        logs.pack(fill='both', expand=True, padx=30, pady=(0, 20))
        tk.Label(logs, text='运行记录', bg='#F3F5FA', fg='#778296', font=('Microsoft YaHei UI', 9)).pack(anchor='w', pady=(0, 5))
        self.log_text = tk.Text(logs, height=2, width=50, wrap='word', state='disabled', bg='#E9EDF5', fg='#5D6980', relief='flat', padx=12, pady=8, font=('Microsoft YaHei UI', 9))
        self.log_text.pack(fill='both', expand=True)
        self._toggle_options()
        self.log_text.configure(state='normal')
        self.log_text.insert('1.0', '选择 TS 视频后，点击开始转换。')
        self.log_text.configure(state='disabled')
        self.log_text.yview_moveto(0)

    def card(self, title, parent=None):
        card = ttk.Frame(parent if parent is not None else self.content, padding=10)
        card.pack(fill='x', padx=30, pady=(0, 8))
        ttk.Label(card, text=title, style='Title.TLabel').pack(anchor='w', pady=(0, 8))
        return card

    def _fit_window(self):
        # Use measured widget sizes at the actual Windows DPI, not fixed pixels.
        self.root.update_idletasks()
        left, top = 0, 0
        right, bottom = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        try:
            import ctypes
            from ctypes import wintypes
            rect = wintypes.RECT()
            if ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0):
                left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom
        except Exception:
            pass
        available_w = max(320, right - left - 32)
        available_h = max(320, bottom - top - 80)
        width = min(available_w, max(820, self.content.winfo_reqwidth() + 30, self.footer.winfo_reqwidth()))
        height = min(available_h, self.content.winfo_reqheight() + self.footer.winfo_reqheight() + 16)
        requested = self.content.winfo_reqheight() + self.footer.winfo_reqheight() + 16
        if requested > available_h:
            ratio = max(0.65, available_h / requested)
            for style_name, size in [('.', 10), ('Title.TLabel', 12), ('Primary.TButton', 11)]:
                ttk.Style().configure(style_name, font=('Microsoft YaHei UI', max(8, int(size * ratio))))
            self.root.update_idletasks()
            height = min(available_h, self.content.winfo_reqheight() + self.footer.winfo_reqheight() + 16)
        self.root.minsize(min(width, 700), height)
        self.root.geometry(f'{width}x{height}+{left + (right-left-width)//2}+{top + 16}')
        self.root.deiconify()

    def path_row(self, parent, label, variable, command, button_text):
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=4)
        ttk.Label(row, text=label, width=9).pack(side='left')
        entry = ttk.Entry(row, textvariable=variable)
        entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        button = ttk.Button(row, text=button_text, command=command, width=12)
        button.pack(side='right')
        self.controls.extend([entry, button])

    def _toggle_options(self):
        enabled = self.mode.get() == 'reencode' and not self.is_running
        self.scale.configure(state='normal' if enabled else 'disabled')
        self.combo.configure(state='readonly' if enabled else 'disabled')

    def choose_input(self):
        path = filedialog.askopenfilename(title='选择 TS 视频', filetypes=[('TS 视频', '*.ts'), ('所有文件', '*.*')])
        if path:
            self.input_path.set(os.path.normpath(path))
            self.output_path.set(str(Path(path).with_suffix('.mp4')))

    def choose_output(self):
        path = filedialog.asksaveasfilename(title='保存 MP4 视频', defaultextension='.mp4', filetypes=[('MP4 视频', '*.mp4')])
        if path:
            self.output_path.set(os.path.normpath(path))

    def log(self, text):
        self.msg_queue.put(('log', text))

    def start_convert(self):
        if self.is_running:
            return
        source = Path(self.input_path.get().strip())
        if not source.is_file():
            messagebox.showwarning('请选择视频', '请先选择一个有效的 TS 视频。')
            return
        target = Path(self.output_path.get().strip()) if self.output_path.get().strip() else source.with_suffix('.mp4')
        if source.resolve() == target.resolve():
            messagebox.showwarning('保存位置无效', '输入和输出不能是同一个文件。')
            return
        if target.suffix.lower() != '.mp4' or not target.parent.is_dir() or target.is_dir():
            messagebox.showwarning('保存位置无效', '请选择已存在的文件夹，并使用 .mp4 文件名。')
            return
        if target.exists() and not messagebox.askyesno('替换已有文件？', f'{target.name} 已存在。\n转换成功后是否替换？'):
            return
        if not find_engine('ffmpeg.exe') or not find_engine('ffprobe.exe'):
            messagebox.showerror('缺少转换组件', '请把 ffmpeg.exe 和 ffprobe.exe 放入程序旁的 ffmpeg/bin 文件夹，或将它们加入系统 PATH。')
            return
        self.output_path.set(str(target))
        self.is_running = True
        self.cancel_event.clear()
        for control in self.controls:
            control.configure(state='disabled')
        self._toggle_options()
        self.btn_start.configure(state='disabled')
        self.btn_cancel.configure(state='normal')
        self.status.set('正在转换…')
        self.percent.set('正在读取视频信息')
        self.progress.configure(value=0)
        self.log(f'开始：{source.name}')
        args = (source, target, self.mode.get(), round(self.crf.get()), self.preset.get())
        threading.Thread(target=self._worker, args=args, daemon=True).start()

    def _worker(self, source, target, mode, crf, preset):
        temporary = target.with_name(f'.{target.stem}.{uuid.uuid4().hex}.partial.mp4')
        tail = deque(maxlen=20)
        result, detail = 'error', ''
        try:
            try:
                probe_engine = find_engine('ffprobe.exe')
                if probe_engine is None:
                    raise FileNotFoundError('未找到 ffprobe.exe，请按照 README 准备 FFmpeg。')
                probe = subprocess.run([probe_engine, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(source)], capture_output=True, text=True, creationflags=FLAGS, timeout=15)
                duration = float(probe.stdout.strip())
            except (ValueError, subprocess.TimeoutExpired):
                duration = 0
            if self.cancel_event.is_set():
                result = 'cancelled'
                return
            self.msg_queue.put(('duration', duration))
            self.process = subprocess.Popen(conversion_command(source, temporary, mode, crf, preset), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', creationflags=FLAGS)
            if self.cancel_event.is_set():
                self.process.terminate()
            with self.process.stdout as stream:
                for raw in stream:
                    line = raw.strip()
                    if line.startswith('out_time_us='):
                        try:
                            seconds = int(line.split('=', 1)[1]) / 1_000_000
                            self.msg_queue.put(('progress', min(99, max(0, seconds / duration * 100)) if duration > 0 else None))
                        except ValueError:
                            pass
                    elif line and '=' not in line.split(' ', 1)[0]:
                        tail.append(line)
                        self.log(line)
            code = self.process.wait()
            if self.cancel_event.is_set():
                result = 'cancelled'
            elif code == 0:
                os.replace(temporary, target)
                result, detail = 'success', str(target)
            else:
                detail = '\n'.join(tail) or f'转换组件退出，代码 {code}'
        except Exception as exc:
            detail = str(exc)
        finally:
            self.process = None
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                self.log(f'临时文件未能清理：{temporary}')
            self.msg_queue.put(('done', (result, detail)))

    def cancel(self):
        self.cancel_event.set()
        self.status.set('正在取消…')
        self.btn_cancel.configure(state='disabled')
        process = self.process
        if process is not None:
            try:
                process.terminate()
            except OSError:
                pass

    def close(self):
        if self.is_running:
            if messagebox.askyesno('退出转换器', '正在转换。确定取消并退出吗？'):
                self.close_pending = True
                self.cancel()
        else:
            self.root.destroy()

    def _poll_queue(self):
        try:
            while True:
                kind, value = self.msg_queue.get_nowait()
                if kind == 'log':
                    self.log_text.configure(state='normal')
                    self.log_text.insert('end', '\n' + value)
                    if int(self.log_text.index('end-1c').split('.')[0]) > 400:
                        self.log_text.delete('1.0', '100.0')
                    self.log_text.see('end-1c')
                    self.log_text.configure(state='disabled')
                elif kind == 'duration':
                    self.percent.set('0%' if value > 0 else '处理中…')
                    if value <= 0:
                        self.progress.configure(mode='indeterminate')
                        self.progress.start(15)
                elif kind == 'progress' and value is not None:
                    self.progress.configure(value=value)
                    self.percent.set(f'{value:.0f}%')
                elif kind == 'done':
                    result, detail = value
                    self.is_running = False
                    self.progress.stop()
                    self.progress.configure(mode='determinate', value=100 if result == 'success' else 0)
                    for control in self.controls:
                        control.configure(state='normal')
                    self._toggle_options()
                    self.btn_start.configure(state='normal')
                    self.btn_cancel.configure(state='disabled')
                    self.status.set({'success': '转换完成', 'cancelled': '已取消', 'error': '转换失败'}[result])
                    self.percent.set('100%' if result == 'success' else '可以重新开始')
                    self.log(detail if detail else '已取消；原文件保持完整。')
                    if self.close_pending:
                        self.root.destroy()
                        return
                    if result == 'error':
                        messagebox.showerror('转换失败', '请检查视频和保存位置；快速无损失败时可尝试重新编码。\n\n' + detail[-2500:])
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def open_output_dir(self):
        path = self.output_path.get().strip()
        if not path:
            messagebox.showinfo('尚未选择位置', '选择视频后即可打开输出目录。')
            return
        try:
            os.startfile(str(Path(path).resolve().parent))
        except OSError as exc:
            messagebox.showerror('无法打开目录', str(exc))


if __name__ == '__main__':
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    TSConverterGUI(root)
    root.mainloop()
