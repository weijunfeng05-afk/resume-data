# AI Resume Screening Copilot V0.5

这是一个最小可运行的招聘简历辅助评估工具。它读取一份文本型 PDF 简历，通过DeepSeek API同时评估两个岗位，并返回结构化 JSON。结果仅供 HR 人工复核，不能自动录用或淘汰。

## 项目架构

数据流很短：`PDF 上传 → pypdf 提取文本 → DeepSeek Chat Completions → JSON 解析与字段校验 → Streamlit 展示/下载`。

第一版刻意不加入数据库、用户系统、批量处理、OCR、向量数据库或复杂后端。这样更容易理解、运行和修改。

## 文件作用

- `app.py`：Streamlit 页面，负责上传、输入 API Key、触发评估和展示结果。
- `screening.py`：核心逻辑，包括 PDF 文本提取、固定岗位标准、公平性规则、JSON 校验和DeepSeek模型调用。
- `requirements.txt`：Python 依赖清单。
- `.env.example`：可选环境变量示例；不要把真实 API Key 提交到代码仓库。
- `.streamlit/secrets.toml.example`：Streamlit Community Cloud Secrets 填写示例，不含真实密钥。
- `.streamlit/config.toml`：关闭本地使用统计，避免受限环境写入用户目录导致会话中断。
- `README.md`：运行和使用说明。

## 运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

浏览器打开 Streamlit 显示的本地地址（通常是 `http://localhost:8501`），在左侧输入DeepSeek API Key，再上传 PDF。
可先点击“测试 API 连接”，验证 Key 是否有效以及所选模型是否可访问；该检查不会上传简历。

如果从 Codex 中启动的页面提示 `Connection error`，请双击 `start_local_app.bat`。它会用本机普通进程在 `http://localhost:8502` 启动应用，从而允许访问DeepSeek API。

### 本地 `.env` 配置

复制 `.env.example` 为 `.env`，然后只在本机填写真实 Key：

```powershell
Copy-Item .env.example .env
python -m streamlit run app.py
```

`.env` 已被 `.gitignore` 排除，不能上传到 GitHub。

## 上传到 GitHub

先在 GitHub 创建一个空仓库，再在项目根目录执行：

```powershell
git init
git add .
git status
git commit -m "Prepare Streamlit Cloud V0.5"
git branch -M main
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin main
```

执行 `git add .` 后必须先看 `git status`：确认没有 `.env`、`.streamlit/secrets.toml`、PDF 简历、`outputs/`、`work/` 或候选人结果文件。

## 部署到 Streamlit Community Cloud

1. 打开 `https://share.streamlit.io`，使用 GitHub 登录。
2. 点击 **Create app**，选择刚创建的仓库和 `main` 分支。
3. Entrypoint file 填写 `app.py`。
4. 打开 **Advanced settings**，Python 选择 `3.12`。
5. 在 **Secrets** 中填写以下内容，并把占位符换成真实 Key：

```toml
DEEPSEEK_API_KEY = "replace_with_your_deepseek_api_key"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-flash"
```

6. 点击 **Deploy**，部署后先用虚构测试简历完成一次 API 连接和评估测试。

真实 API Key 只放在 Community Cloud 的 Secrets 设置里，不要创建并提交真实的 `.streamlit/secrets.toml`。

## 数据与安全

- 当前应用不会主动把上传的 PDF 或结果写入项目目录；文件内容只在当前 Streamlit 会话中处理。
- 简历文字会发送给DeepSeek模型 API。使用真实候选人数据前，需确认公司的告知、授权、留存和跨境/第三方处理政策。
- V0.5 尚未加入用户登录和权限控制。公开分享链接前，建议先限制访问；如果无法限制，只使用脱敏测试简历，避免 API Key 额度被他人消耗。
- `.gitignore` 能防止未跟踪的敏感文件被新增提交，但不能自动移除已经提交过的密钥。若密钥曾进入 Git 历史，应立即在DeepSeek控制台轮换。

## MVP 限制

- 扫描件或图片型 PDF 暂无 OCR，可能提取不到文字。
- 评分依赖简历自述，必须在面试中核验。
- 简历文本会发送给所配置的模型 API，使用前应确认公司隐私与数据处理政策。
- 公平性规则已写入提示词，但上线前仍应增加人工审计、日志与本地法规审查。

## V0.5 DeepSeek 接入更新

保留原版两个岗位的评分权重和提示词，改用 DeepSeek 官方 API。旧的 ARK_* 配置不再读取，请填写 DEEPSEEK_API_KEY。默认模型 deepseek-v4-flash，可在侧栏修改。使用 JSON 输出模式，并关闭思考模式以获得直接的结构化结果。

接口参考：https://api-docs.deepseek.com/ 和 https://api-docs.deepseek.com/guides/json_mode/ 。

本地验证：`python -m unittest discover -s tests -v`。真实连接验证：`python scripts/test_deepseek_chat.py`，需要自行配置 Key，会产生少量 API 用量。
