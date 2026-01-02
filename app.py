import streamlit as st
from google import genai
import requests
import time

# --- 1. 页面基础配置 ---
st.set_page_config(
    page_title="全球电力数字化情报中心",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 安全与配置加载 ---
try:
    # 这里的写法是正确的，从 Secrets 读取，而不是直接写死 Key
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
except FileNotFoundError:
    st.error("🚨 严重错误：未检测到 API 密钥配置！")
    st.info("请在 Streamlit Cloud 的 App Settings -> Secrets 中配置 GEMINI_API_KEY 和 TAVILY_API_KEY。")
    st.stop()

# 初始化 Gemini 客户端
client = genai.Client(api_key=GEMINI_API_KEY)

# --- 3. 核心功能函数 ---
@st.cache_data(show_spinner=False, ttl=3600)
def search_tavily(query):
    """调用 Tavily 进行联网搜索"""
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "max_results": 7,
        "include_domains": []
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def generate_report(prompt):
    """调用 Gemini 生成报告"""
    try:
        # 【关键修改】这里改成了 flash 模型，解决了 404 问题
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"生成失败: {str(e)}"

# --- 4. 界面布局设计 ---
st.title("🛡️ 华为电力数字化军团 | 全球情报 Agent")
st.markdown("`Powered by Gemini 1.5 Flash & Tavily Search`")
st.divider()

# 侧边栏
with st.sidebar:
    st.header("⚙️ 研判控制台")
    st.markdown("---")
    st.success("🟢 网络连接：全球直连")
    st.success("🟢 AI 引擎：Gemini 1.5 Flash") # 界面文字我也帮您同步改了
    st.info("📚 覆盖情报源：\n- IEEE / CIGRE / IEA\n- 彭博新能源财经 (BNEF)\n- 西门子/施耐德/GE 官网")
    
    st.markdown("---")
    st.caption("© 2025 Huawei Electric Power Digitalization Corps. Internal Tool.")

# 主交互区
col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("🔎 输入调研课题", placeholder="例如：沙特红海新城微电网项目的数字化架构分析")

with col2:
    st.write("")
    st.write("") 
    analyze_btn = st.button("🚀 生成顾问报告", type="primary", use_container_width=True)

# --- 5. 业务逻辑执行 ---
if analyze_btn and query:
    if len(query) < 2:
        st.warning("请输入更具体的关键词。")
    else:
        status_box = st.status("正在启动全球情报侦察...", expanded=True)
        
        # [步骤 1] 联网搜索
        status_box.write("📡 正在连接 Tavily 卫星检索全球数据...")
        search_data = search_tavily(query)
        
        if "error" in search_data:
            status_box.update(label="❌ 搜索服务连接失败", state="error")
            st.error(f"搜索接口报错: {search_data['error']}")
        else:
            results = search_data.get("results", [])
            if not results:
                status_box.update(label="⚠️ 未检索到有效信息", state="error")
                st.warning("全球数据库中未发现相关公开情报，请尝试更换关键词。")
            else:
                # 构建上下文
                context_text = "\n\n".join([
                    f"【来源{i+1}】标题: {r['title']}\n链接: {r['url']}\n摘要: {r['content']}" 
                    for i, r in enumerate(results)
                ])
                
                status_box.write("🧠 情报获取成功，Gemini 正在进行深度研判...")
                
                # [步骤 2] 顾问级 Prompt
                consultant_prompt = f"""
                身份设定：你是华为电力数字化军团的首席战略顾问。
                任务目标：基于提供的外部情报，针对课题【{query}】撰写一份高层决策参考报告。
                
                【情报库数据】：
                {context_text}
                
                请严格按照以下 Markdown 格式输出：
                
                # 🌍 全球情报研判报告：{query}
                
                ## 1. 核心洞察 (Executive Summary)
                (用3句话总结该领域的最新现状，必须包含具体的年份、数据或项目名称)
                
                ## 2. 关键技术/案例拆解
                (基于情报，详细分析1-2个标杆案例的技术架构。例如：使用了什么边缘计算网关、云平台或AI算法)
                
                ## 3. 商业价值与痛点
                (分析该技术解决了什么核心问题？例如：降低了xx%的运维成本，或提升了xx%的新能源消纳率)
                
                ## 4. 华为军团建议 (Internal Advice)
                (结合华为优势——如昇腾算力、鸿蒙OS、盘古大模型，对比竞对（如西门子/ABB），给出差异化打法建议)
                
                ---
                *注：本报告由 AI 实时生成，仅供参考。*
                """
                
                # [步骤 3] 生成内容
                report_content = generate_report(consultant_prompt)
                
                status_box.update(label="✅ 研判报告已生成", state="complete", expanded=False)
                
                # [步骤 4] 结果展示
                tab1, tab2 = st.tabs(["📝 深度研判报告", "🔗 原始情报来源"])
                
                with tab1:
                    st.markdown(report_content)
                    st.download_button(
                        label="💾 导出报告 (TXT)",
                        data=report_content,
                        file_name=f"Report_{query}.txt",
                        mime="text/plain"
                    )
                
                with tab2:
                    st.markdown("### 🕵️‍♂️ 原始检索线索")
                    for r in results:
                        with st.expander(f"来源：{r['title']}"):
                            st.info(f"URL: {r['url']}")
                            st.write(r['content'])
