# 暂停键桌游推荐助手 - 最终优化版（难度1-5 两位小数+人数全部+多标签）
import streamlit as st
import pandas as pd
import re

# ---------------------- 页面基础配置 ----------------------
st.set_page_config(
    page_title="暂停键桌游推荐助手",
    page_icon="🎲",
    layout="wide"
)
st.title("🎲 暂停键桌游推荐助手")

# ---------------------- 核心：加载数据（修复编码报错） ----------------------
# @st.cache_data(ttl=3600)
def load_data():
    # 修复UnicodeDecodeError报错，兼容Windows中文CSV
    df = pd.read_csv(
        "board_games.csv",
        engine="python",
        encoding="gbk",          
        encoding_errors="replace",
        on_bad_lines="skip",     
        skip_blank_lines=True    
    )
    
    # 数据清洗：游戏时长转数字
    if "游戏时长(分钟)" in df.columns:
        df["游戏时长(分钟)"] = pd.to_numeric(df["游戏时长(分钟)"], errors="coerce").fillna(0).astype(int)
    
    # 数据清洗：难度等级保留两位小数
    if "难度等级" in df.columns:
        df["难度等级"] = pd.to_numeric(df["难度等级"], errors="coerce").fillna(1.00).round(2)
    
    return df

# 加载数据
try:
    df = load_data()
except Exception as e:
    # 备用编码：如果GBK报错，自动切换UTF-8
    df = pd.read_csv(
        "board_games.csv",
        engine="python",
        encoding="utf-8-sig",
        encoding_errors="replace",
        on_bad_lines="skip",
        skip_blank_lines=True
    )

# ---------------------- 核心：多分类标签拆分 ----------------------
def get_all_categories(dataframe):
    """自动拆分逗号分隔的分类标签，生成筛选列表"""
    category_set = set()
    for value in dataframe["分类"].dropna():
        tags = [tag.strip() for tag in str(value).split(",")]
        for tag in tags:
            if tag and tag != "nan":
                category_set.add(tag)
    return sorted(list(category_set))

# 获取所有分类标签
all_tags = get_all_categories(df)

# ---------------------- 侧边栏筛选功能 ----------------------
st.sidebar.header("🔍 筛选条件")

# 1. 游玩人数筛选 【全部】默认选中
player_num = st.sidebar.selectbox(
    "选择游玩人数",
    options=["全部",1,2,3,4,5,6,7,8,9,10,12,15,20],
    index=0
)

# 2. 难度等级筛选 ✅ 核心修改：1.00-5.00 小数点后两位
difficulty = st.sidebar.slider(
    "难度等级范围",
    min_value=1.00,    # 固定下限1
    max_value=5.00,    # 固定上限5
    value=(1.00, 5.00),# 默认全范围
    step=0.01          # 精度：两位小数
)

# 3. 分类标签筛选（支持多选/多标签）
selected_tags = st.sidebar.multiselect(
    "游戏分类（可多选）",
    options=all_tags,
    default=[]
)

# ---------------------- 搜索功能 ----------------------
search_key = st.text_input("🔎 搜索桌游名称")

# ---------------------- 数据筛选逻辑 ----------------------
filtered_df = df.copy()

# 匹配推荐人数：全部则不筛选
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

# 匹配难度等级（1.00-5.00 两位小数）
filtered_df = filtered_df[
    (filtered_df["难度等级"] >= difficulty[0]) &
    (filtered_df["难度等级"] <= difficulty[1])
]

# 匹配分类标签（核心：多标签兼容）
if selected_tags:
    mask = filtered_df["分类"].apply(
        lambda x: any(tag in str(x).split(",") for tag in selected_tags)
    )
    filtered_df = filtered_df[mask]

# 关键词搜索
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
                    st.image(f"images/{row['图片链接']}", width=250)
                except:
                    st.write("🖼️ 暂无图片")
            
            with col_info:
                st.markdown(f"**👥 推荐人数**：{row['推荐人数']}")
                st.markdown(f"**⏱️ 游戏时长**：{row['游戏时长(分钟)']} 分钟")
                st.markdown(f"**⭐ 难度等级**：{round(row['难度等级'], 2)}")  # 显示两位小数
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