from __future__ import annotations
import csv
from io import BytesIO
from datetime import date, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import altair as alt
import pandas as pd
import streamlit as st

# 基础配置
APP_TITLE = "OKKISS 地推销售与库存管理"
MANAGER_PASSWORD = "okkiss2026"
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE = DATA_DIR / "sales_records.csv"
INVENTORY_FILE = DATA_DIR / "inventory_movements.csv"
COST_FILE = DATA_DIR / "cost_records.csv"
PRICE_FILE = DATA_DIR / "price_settings.csv"

PAGE_OPTIONS = ["销售录入", "库存管理", "费用与成本", "盈利分析与洞察"]

# 产品配置（按你给的列表更新）
PRODUCT_LIST = [
    "草莓",
    "小草莓",
    "蜜桃",
    "蜜桃乌龙无醇",
    "阿斯蒂甜白",
    "莫斯卡托桃红",
    "绿宝石",
    "紫宝石",
    "快乐王子",
    "长相思",
    "赤霞珠"
]

# 瓶卖/杯卖基础价格（可根据实际情况修改）
PRODUCT_PRICES = {
    "草莓": {"瓶卖": 128, "杯卖": 38},
    "小草莓": {"瓶卖": 98, "杯卖": 28},
    "蜜桃": {"瓶卖": 118, "杯卖": 35},
    "蜜桃乌龙无醇": {"瓶卖": 108, "杯卖": 32},
    "阿斯蒂甜白": {"瓶卖": 158, "杯卖": 45},
    "莫斯卡托桃红": {"瓶卖": 138, "杯卖": 40},
    "绿宝石": {"瓶卖": 168, "杯卖": 48},
    "紫宝石": {"瓶卖": 168, "杯卖": 48},
    "快乐王子": {"瓶卖": 198, "杯卖": 55},
    "长相思": {"瓶卖": 178, "杯卖": 50},
    "赤霞珠": {"瓶卖": 228, "杯卖": 65}
}

# 初始化数据文件
def init_file(file_path: Path, columns: list):
    if not file_path.exists():
        df = pd.DataFrame(columns=columns)
        df.to_csv(file_path, index=False, encoding="utf-8-sig")

init_file(DATA_FILE, ["日期", "城市", "活动地点", "产品名称", "销售类型", "数量", "单价", "总价", "折扣"])
init_file(INVENTORY_FILE, ["日期", "产品名称", "变动类型", "数量", "备注"])
init_file(COST_FILE, ["日期", "项目", "金额", "备注"])
init_file(PRICE_FILE, ["产品名称", "瓶卖价格", "杯卖价格"])

# 主页面
st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)

# 侧边栏选择页面
page = st.sidebar.radio("功能模块", PAGE_OPTIONS)

# ---------------- 销售录入模块 ----------------
if page == "销售录入":
    st.header("销售录入")

    # 场次信息
    col1, col2 = st.columns(2)
    with col1:
        city = st.selectbox("城市", ["上海", "杭州", "南京", "苏州", "其他"])
    with col2:
        activity_date = st.date_input("活动日期", date.today())

    location_options = ["上海来福士", "杭州湖滨银泰", "南京新街口", "苏州中心", "新增活动地点"]
    location = st.selectbox("活动地点", location_options)
    if location == "新增活动地点":
        location = st.text_input("新增活动地点", placeholder="例如：杭州湖滨银泰A区")

    st.divider()

    # 快速录入（带所有新功能）
    st.subheader("快速录入")
    with st.form("sales_entry_form"):
        # 产品选择
        product_name = st.selectbox("产品名称/SKU", PRODUCT_LIST)
        
        # 图片展示（需上传产品图片到 product_images 文件夹）
        image_path = Path("product_images") / f"{product_name}.jpg"
        if image_path.exists():
            st.image(str(image_path), caption=product_name, width=150)
        else:
            st.info(f"暂未上传 {product_name} 的产品图片")
        
        # 销售类型和数量
        sales_type = st.radio("销售类型", ["瓶卖", "杯卖"], horizontal=True)
        quantity = st.number_input("数量", min_value=1, value=1)
        
        # 折扣选择（仅瓶卖生效）
        if sales_type == "瓶卖":
            discount_option = st.radio("多瓶折扣", ["无折扣", "2瓶9折", "3瓶及以上8.5折"], horizontal=True)
        else:
            discount_option = "无折扣"
            st.info("杯卖不参与多瓶折扣活动")
        
        # 价格自动计算
        base_price = PRODUCT_PRICES[product_name][sales_type]
        if sales_type == "瓶卖":
            if discount_option == "2瓶9折" and quantity >= 2:
                unit_price = round(base_price * 0.9, 2)
            elif discount_option == "3瓶及以上8.5折" and quantity >= 3:
                unit_price = round(base_price * 0.85, 2)
            else:
                unit_price = base_price
        else:
            unit_price = base_price
        total_price = round(unit_price * quantity, 2)
        
        # 价格预览
        st.write(f"**单价：{unit_price} 元 | 总价：{total_price} 元**")
        
        # 保存按钮
        submitted = st.form_submit_button("保存记录")
        if submitted:
            # 构建记录
            new_record = {
                "日期": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "城市": city,
                "活动地点": location,
                "产品名称": product_name,
                "销售类型": sales_type,
                "数量": quantity,
                "单价": unit_price,
                "总价": total_price,
                "折扣": discount_option
            }
            # 保存到CSV
            df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
            df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
            df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
            st.success("✅ 销售记录已保存！")

# ---------------- 库存管理模块 ----------------
elif page == "库存管理":
    st.header("库存管理")
    # 库存管理功能可在此扩展

# ---------------- 费用与成本模块 ----------------
elif page == "费用与成本":
    st.header("费用与成本")
    # 费用与成本功能可在此扩展

# ---------------- 盈利分析与洞察模块 ----------------
elif page == "盈利分析与洞察":
    st.header("盈利分析与洞察")
    # 盈利分析功能可在此扩展