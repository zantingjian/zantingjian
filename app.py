# 暂停键桌游推荐助手 - 最终完美版（隐藏管理应用按钮+全功能）
import streamlit as st
import pandas as pd
import re

# ---------------------- 页面基础配置 ----------------------
st.set_page_config(
    page_title="暂停键桌游推荐助手",
    page_icon="🎲",
    layout="wide"
)

# ---------------------- ✅ 核心：彻底隐藏右下角「Manage app 管理应用」按钮 ----------------------
hide_streamlit_ui = """
<style>
/* 精准定位Streamlit云端「Manage app 管理应用」按钮 */
[aria-label="Manage app"],
[data-testid="stActionButton"],
.stActionButton,
/* 隐藏右下角悬浮容器，彻底清除按钮 */
.stApp > div:nth-child(3),
.stApp > header + div > div > div > button,
/* 兜底：隐藏所有右下角操作控件 */
[class*="stActionButton"],
[data-testid="stHeaderActionElements"] > div > button {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    height: 0 !important;
    width: 0 !important;
}
</style>
"""
st.markdown(hide_streamlit_ui, unsafe_allow_html=True)

# ---------------------- 标题 ----------------------
st.title("🎲 暂停键桌游推荐助手")
st.caption("支持多分类标签筛选 | 默认显示全部游戏 | 难度1.00-5.00")

# ---------------------- 加载数据（修复中文编码） ----------------------
@st.cache_data(ttl=3600)
def load_data():
    try:
        df = pd.read_csv(
            "board_games.csv",
            engine="python",
            encoding="gbk",
            encoding_errors="replace",
            on_bad_lines="skip",
            skip_blank_lines=True
        )
    except:
        df = pd.read_csv(
            "board_games.csv",
            engine="python",
            encoding="utf-8-sig",
            encoding_errors="replace",
            on_bad_lines="skip",
            skip_blank_lines=True
        )

    # 清洗数据
    if "游戏时长(分钟)" in df.columns:
        df["游戏时长(分钟)"] = pd.to_numeric(df["游戏时长(分钟)"], errors="coerce").fillna(0).astype(int)
    if "难度等级" in df.columns:
        df["难度等级"] = pd.to_numeric(df["难度等级"], errors="coerce").fillna(1.00).round(2)
    
    return df

df = load_data()

# ---------------------- 拆分多分类标签 ----------------------
def get_all_categories(dataframe):
    category_set = set()
    for value in dataframe["分类"].dropna():
        tags = [tag.strip() for tag in str(value).split(",")]
        for tag in tags:
            if tag and tag != "nan":
                category_set.add(tag)
    return sorted(list(category_set))

all_tags = get_all_categories(df)

# ---------------------- 侧边栏筛选 ----------------------
st.sidebar.header("🔍 筛选条件")

# 1. 游玩人数（默认全部）
player_num = st.sidebar.selectbox(
    "选择游玩人数",
    options=["全部",1,2,3,4,5,6,7,8,9,10,12,15,20],
    index=0
)

# 2. 难度等级（1.00-5.00 两位小数）
difficulty = st.sidebar.slider(
    "难度等级范围",
    min_value=1.00,
    max_value=5.00,
    value=(1.00, 5.00),
    step=0.01
)

# 3. 游戏分类（多选，修复显示问题）
selected_tags = st.sidebar.multiselect(
    "游戏分类（可多选）",
    options=all_tags,
    default=[]
)

# ---------------------- 搜索功能 ----------------------
search_key = st.text_input("🔎 搜索桌游名称")

# ---------------------- 筛选逻辑 ----------------------
filtered_df = df.copy()

# 人数匹配
def match_players(player_range, target):
    if target == "全部":
        return True
    try:
        numbers = re.findall(r"\d+", str(player_range))
        if len(numbers) == 1:
            return int(numbers[0]) == target
        min_p, max_p = int(numbers[0]), int(numbers[1])
        return min_p <= target <= max_p
    except:
        return True

filtered_df = filtered_df[filtered_df["推荐人数"].apply(lambda x: match_players(x, player_num))]

# 难度筛选
filtered_df = filtered_df[
    (filtered_df["难度等级"] >= difficulty[0]) &
    (filtered_df["难度等级"] <= difficulty[1])
]

# 分类筛选
if selected_tags:
    mask = filtered_df["分类"].apply(
        lambda x: any(tag in str(x).split(",") for tag in selected_tags)
    )
    filtered_df = filtered_df[mask]

# 搜索筛选
if search_key.strip():
    filtered_df = filtered_df[filtered_df["桌游名称"].str.contains(search_key, na=False, case=False)]

# ---------------------- 结果展示 ----------------------
st.divider()
st.subheader(f"🎯 筛选结果：{len(filtered_df)} 款桌游")
st.caption(f"总数据：{len(df)} 款")

if filtered_df.empty:
    st.warning("未找到匹配的桌游，可调整筛选条件~")
else:
    for _, row in filtered_df.iterrows():
        with st.expander(f"📦 {row['桌游名称']}", expanded=False):
            col_img, col_info = st.columns([1, 2])
            
            with col_img:
                try:
                    # 云端图片路径：images/文件夹
                    st.image(f"images/{row['图片链接']}", width=250)
                except:
                    st.write("🖼️ 暂无图片")
            
            with col_info:
                st.markdown(f"**👥 推荐人数**：{row['推荐人数']}")
                st.markdown(f"**⏱️ 游戏时长**：{row['游戏时长(分钟)']} 分钟")
                st.markdown(f"**⭐ 难度等级**：{round(row['难度等级'], 2)}")
                st.markdown(f"**🏷️ 游戏分类**：{row['分类']}")
                st.markdown(f"**📖 核心玩法**：{row['核心玩法简介']}")
            
            # 视频展示
            if "视频链接" in df.columns and pd.notna(row["视频链接"]):
                st.markdown("---")
                st.markdown("**🎬 教学视频**")
                try:
                    st.video(row["视频链接"])
                except:
                    st.write("视频加载失败")

st.divider()
st.caption("✅ 最终版：隐藏管理应用按钮 | 全功能正常 | 界面干净")