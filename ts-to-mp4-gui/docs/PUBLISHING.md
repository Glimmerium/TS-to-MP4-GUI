# 上传到 GitHub

当前交付是本地项目和源码 ZIP，没有创建远端仓库，也没有上传任何文件。

建议仓库名：`ts-to-mp4-gui`

建议简介：`面向 Windows 的简洁中文 TS → MP4 转换器，基于 FFmpeg，支持无损换封装与重新编码。`

建议主题：`ffmpeg`、`tkinter`、`video-converter`、`windows`、`python`。

## 使用 Git 上传

1. 在自己的 GitHub 账号下创建空仓库；不要在网页端额外初始化 README、许可证或 .gitignore。
2. 在本地项目文件夹打开终端。交付的文件夹已初始化 main 分支，但尚未提交，作者身份由你自己设置；从 ZIP 解压的副本需先运行 `git init -b main`。
3. 使用你自己的 Git 提交姓名与邮箱，然后执行：

```powershell
git add .
git commit -m "Initial release of TS to MP4 GUI"
git remote add origin https://github.com/YOUR_USERNAME/ts-to-mp4-gui.git
git push -u origin main
```

将 `YOUR_USERNAME` 替换为自己的 GitHub 用户名。若 Git 提示缺少作者身份，按提示设置你自己的姓名与邮箱；可使用 GitHub 提供的 noreply 邮箱。

上传对象是解压后的项目文件，不是把源码 ZIP 当成唯一文件上传。正常情况下仓库首页会直接展示 README。

## 制作可供同学下载的程序包

本地按 README 打包，或在仓库的 Actions 页面手动运行 **Build Windows app**。首次运行需要自己确认 GitHub 已启用 Actions。

输出的 `TS-MP4-windows-x64.zip` 包含 EXE、图标、说明及相关许可证，**不包含 FFmpeg**。用户按 README 准备 `ffmpeg.exe` 和 `ffprobe.exe` 后即可使用，无需安装 Python。

如需发布，在 GitHub Releases 中自行选择标签（例如 `v0.1.0`），上传程序 ZIP，并在发布说明里写明 Windows x64 和 FFmpeg 外部依赖。源码 ZIP 和程序 ZIP 用途不同，请分别命名。

项目整理阶段未重新运行 GUI 或转换测试，因此发布说明不要写成“已全面测试”或“兼容所有 TS 文件”。正式发布前可根据自己的使用情况补充验证记录。
