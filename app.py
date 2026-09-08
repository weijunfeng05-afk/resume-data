import json
import os

import streamlit as st
from dotenv import load_dotenv

from screening import (
    DEFAULT_DEEPSEEK_BASE_URL,
    DEFAULT_DEEPSEEK_MODEL,
    ModelResponseFormatError,
    PdfExtractionError,
    extract_pdf_text,
    screen_resume,
    test_deepseek_connection,
)


load_dotenv()


def get_setting(name: str, default: str = "") -> str:
    """Read Streamlit Cloud secrets first, then local environment/.env."""
    try:
        value = st.secrets[name]
    except (FileNotFoundError, KeyError):
        value = os.getenv(name, default)
    return str(value).strip() if value is not None else default


def friendly_api_error(exc: Exception) -> str:
    name = type(exc).__name__
    status = getattr(exc, "status_code", None)
    if "Timeout" in name:
        return "DeepSeek 请求超时，请稍后重试。"
    if status in (401, 403):
        return f"HTTP {status}：API Key 无效，或该 Key 没有访问此模型的权限。"
    if status == 404:
        return "HTTP 404：未找到接口或模型，请检查 Base URL 和 Model ID。"
    if status == 429:
        return "HTTP 429：请求过于频繁或额度不足，请稍后重试并检查方舟额度。"
    if status and status >= 500:
        return f"HTTP {status}：DeepSeek服务暂时异常，请稍后重试。"
    if "Connection" in name or "connection" in str(exc).lower():
        return "无法连接DeepSeek，请检查部署环境网络后重试。"
    if isinstance(exc, ValueError):
        return str(exc)
    return f"API 调用失败（{name}），请检查配置后重试。"


st.set_page_config(page_title="AI Resume Screening Copilot", page_icon="📄", layout="wide")
st.title("AI Resume Screening Copilot V0.5 · DeepSeek")
st.caption("MVP：同时评估两个岗位，只提供 HR 人工复核建议，不自动录用或淘汰。")

with st.sidebar:
    st.header("设置")
    configured_api_key = get_setting("DEEPSEEK_API_KEY")
    if configured_api_key:
        api_key = configured_api_key
        st.success("DeepSeek API Key 已通过安全配置加载。")
    else:
        api_key = st.text_input(
            "DeepSeek API Key",
            type="password",
            help="仅保存在当前浏览器会话中，不会写入项目文件。",
        )
    base_url = st.text_input(
        "ARK Base URL",
        value=get_setting("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL),
    )
    model = st.text_input("模型", value=get_setting("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL))
    if st.button("测试 API 连接", use_container_width=True):
        if not api_key:
            st.error("请先输入DeepSeek API Key。")
        else:
            try:
                reply = test_deepseek_connection(api_key=api_key, base_url=base_url, model=model)
                st.success(f"Chat Completions 调用成功：{reply}")
            except Exception as exc:
                st.error(f"API 连接失败：{friendly_api_error(exc)}")
    st.warning("请勿依据性别、民族、国籍、政治面貌、年龄、婚育等敏感信息做评分。")

uploaded_file = st.file_uploader("上传一份 PDF 简历", type=["pdf"])

if uploaded_file:
    try:
        resume_text = extract_pdf_text(uploaded_file)
    except PdfExtractionError as exc:
        st.error(f"PDF 读取失败：{exc}")
        st.stop()
    except Exception:
        st.error("PDF 读取失败：文件可能已损坏或不是有效的 PDF。")
        st.stop()

    st.success(f"已提取 {len(resume_text):,} 个字符。")
    with st.expander("查看提取文本"):
        st.text(resume_text)

    if not resume_text.strip():
        st.error("未提取到文本。扫描版 PDF 暂不支持，需要后续增加 OCR。")
    elif st.button("开始评估", type="primary", use_container_width=True):
        if not api_key:
            st.error("请先在左侧输入DeepSeek API Key。")
        else:
            try:
                with st.spinner("正在按固定标准评估两个岗位……"):
                    result = screen_resume(
                        resume_text,
                        api_key=api_key,
                        base_url=base_url,
                        model=model,
                    )

                st.subheader("人工复核结果")
                left, right = st.columns(2)
                left.metric("ToC 商业化产品运营", f"{result['toc_score']}/100", result["toc_priority"])
                right.metric("内部提效 AI 产品经理", f"{result['internal_ai_score']}/100", result["internal_ai_priority"])

                st.write(f"**候选人：** {result['candidate_name']}")
                st.write(f"**相对更匹配岗位：** {result['best_fit_role']}")
                st.write(f"**最终人工复核建议：** {result['final_recommendation']}")

                for label, key in [
                    ("AI 深度（简历自述）", "claimed_ai_depth"),
                    ("证据可信度", "verification_confidence"),
                    ("Owner 程度", "ownership_level"),
                    ("优势", "strengths"),
                    ("风险", "risks"),
                    ("未知项", "unknowns"),
                    ("面试必须核验", "must_verify"),
                ]:
                    st.markdown(f"### {label}")
                    value = result[key]
                    if isinstance(value, list):
                        for item in value:
                            st.write(f"- {item}")
                    else:
                        st.write(value)

                st.download_button(
                    "下载 JSON",
                    data=json.dumps(result, ensure_ascii=False, indent=2),
                    file_name="screening_result.json",
                    mime="application/json",
                )
                st.info("该结果不能作为自动录用或淘汰决定，必须由 HR 结合面试与事实核验后判断。")
            except ModelResponseFormatError as exc:
                st.error(f"模型返回格式错误：{exc}")
                st.info("本次没有生成招聘建议。请重新评估；如持续出现，请检查模型是否支持稳定的 JSON 输出。")
            except Exception as exc:
                st.error(f"评估失败：{friendly_api_error(exc)}")
