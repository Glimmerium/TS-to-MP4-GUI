# 第三方组件

本项目自有 GUI 源码及图标使用仓库中的 MIT 许可证。该许可不替代下列组件各自的许可。

## FFmpeg

- 项目：https://ffmpeg.org/
- 下载：https://ffmpeg.org/download.html
- 许可说明：https://ffmpeg.org/legal.html

本项目通过独立进程调用用户提供的 `ffmpeg.exe` 和 `ffprobe.exe`，源码 ZIP 和默认程序 ZIP 均不包含这两个二进制文件。

FFmpeg 构建的许可证取决于启用的组件；不要假定所有构建都采用同一个许可。如果另行发布附带 FFmpeg 的整合包，应依据所选构建附带的许可和来源说明准备分发材料；本仓库的 MIT 许可证不能覆盖它。推荐直接让用户从上游下载。

## Python、Tcl/Tk 和 PyInstaller

从源码运行时使用用户本机的 Python/Tkinter；EXE 打包时会包含 Python 和 Tcl/Tk 运行时。打包脚本会附带该 Python 安装中的 Python、Tcl 和 Tk 许可证文本。

- Python：https://docs.python.org/3/license.html
- Tcl/Tk：https://www.tcl-lang.org/software/tcltk/license.html
- PyInstaller：https://pyinstaller.org/en/stable/license.html

PyInstaller 用于生成可执行文件，其许可包含针对生成程序的例外条款。打包工具本身不作为本项目源码的一部分分发。
