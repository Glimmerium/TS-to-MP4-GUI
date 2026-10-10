# TS → MP4 GUI

基于 FFmpeg 的 Windows 视频转换工具，提供中文图形界面，方便将本地 TS 视频转换为 MP4，用于播放和后续资料整理。

## 功能

- **快速无损**：直接复制音视频流，避免重新编码。
- **重新编码**：输出 H.264 / AAC，支持画质与编码速度调整。
- 显示转换进度和日志，支持取消与打开输出目录。
- 转换成功后才替换目标文件，覆盖前提示，保留原视频。
- 窗口自动适配屏幕，路径使用 Windows 格式。
- 点击右上角个人 logo 可查看开发者信息。

## 使用

1. 准备 `ffmpeg.exe` 和 `ffprobe.exe`，放入程序旁的 `ffmpeg/bin/` 文件夹，或加入 PATH。下载入口：[FFmpeg](https://ffmpeg.org/download.html)。
2. 双击打包后的 EXE，选择 TS 文件和输出位置。
3. 先尝试“快速无损”；若编码不兼容，改用“重新编码”。

EXE 无需安装 Python。源码包和默认打包产物不附带 FFmpeg。

## 源码运行与打包

使用 Windows x64、Python 3.10+（含 Tcl/Tk）。

```powershell
python converter.py
python -m pip install -r requirements-build.txt
.\scriptsuild.ps1 -Python python
```

也可手动运行仓库的 GitHub Actions 打包工作流。上传步骤见 [发布说明](docs/PUBLISHING.md)。

## 说明

本程序本地处理文件，一次转换一个视频，不提供下载、解密或语音转文字功能。换封装要求 MP4 支持原始编码；重新编码可能改变画质和体积。使用 FFmpeg 默认流选择，不保证保留全部音轨与字幕。

GUI 源码使用 [MIT 许可证](LICENSE)，第三方组件见 [相关说明](THIRD_PARTY_NOTICES.md)。个人 logo 由开发者提供。
