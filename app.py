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

# ---------------- 产品配置 ----------------
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

PRODUCT_PRICES = {
    "草莓": {"瓶卖": 128, "杯卖": 38, "试饮": 0},
    "小草莓": {"瓶卖": 98, "杯卖": 28, "试饮": 0},
    "蜜桃": {"瓶卖": 118, "杯卖": 35, "试饮": 0},
    "蜜桃乌龙无醇": {"瓶卖": 108, "杯卖": 32, "试饮": 0},
    "阿斯蒂甜白": {"瓶卖": 158, "杯卖": 45, "试饮": 0},
    "莫斯卡托桃红": {"瓶卖": 138, "杯卖": 40, "试饮": 0},
    "绿宝石": {"瓶卖": 168, "杯卖": 48, "试饮": 0},
    "紫宝石": {"瓶卖": 168, "杯卖": 48, "试饮": 0},
    "快乐王子": {"瓶卖": 198, "杯卖": 55, "试饮": 0},
    "长相思": {"瓶卖": 178, "杯卖": 50, "试饮": 0},
    "赤霞珠": {"瓶卖": 228, "杯卖": 65, "试饮": 0}
}

# 初始化数据文件
def init_file(file_path: Path, columns: list):
    if not file_path.exists():
        df = pd.DataFrame(columns=columns)
        df.to_csv(file_path, index=False, encoding="utf-8-sig")

init_file(DATA_FILE, ["日期", "城市", "活动地点", "产品名称", "销售类型", "数量", "单价", "总价", "折扣", "备注"])
init_file(INVENTORY_FILE, ["日期", "产品名称", "变动类型", "数量", "备注"])
init_file(COST_FILE, ["日期", "项目", "金额", "备注"])
init_file(PRICE_FILE, ["产品名称", "瓶卖价格", "杯卖价格", "试饮成本", "更新时间"])

# 主页面
st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
page = st.sidebar.radio("功能模块", PAGE_OPTIONS)

# ---------------- 销售录入模块（含试饮、价格、折扣、图片上传） ----------------
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

    # 快速录入
    st.subheader("快速录入")
    with st.form("sales_entry_form"):
        # 1. 产品选择
        product_name = st.selectbox("产品名称/SKU", PRODUCT_LIST)

        # 2. 产品图片展示 + 上传
        st.write("**产品图片**")
        image_path = Path("product_images") / f"{product_name}.jpg"
        if image_path.exists():
            st.image(str(image_path), caption=product_name, width=150)
        else:
            st.info(f"暂未上传 {product_name} 的产品图片")

        # 界面上传图片功能
        uploaded_image = st.file_uploader("上传/更新产品图片（jpg/png）", type=["jpg", "png"], key=product_name)
        if uploaded_image is not None:
            image_path.parent.mkdir(exist_ok=True)
            with open(image_path, "wb") as f:
                f.write(uploaded_image.getbuffer())
            st.success(f"✅ {product_name} 的图片已上传成功！")

        # 3. 销售类型选择（含试饮）
        sales_type = st.radio("销售类型", ["瓶卖", "杯卖", "试饮"], horizontal=True)

        # 4. 数量输入
        quantity = st.number_input("数量", min_value=1, value=1)

        # 5. 价格与折扣
        unit_price = 0
        total_price = 0
        discount_option = "无折扣"

        if sales_type in ["瓶卖", "杯卖"]:
            base_price = PRODUCT_PRICES[product_name][sales_type]
            unit_price = st.number_input(f"{sales_type}单价（元）", value=base_price)

            if sales_type == "瓶卖":
                discount_option = st.radio("多瓶折扣", ["无折扣", "2瓶9折", "3瓶及以上8.5折"], horizontal=True)
                if discount_option == "2瓶9折" and quantity >= 2:
                    unit_price = round(unit_price * 0.9, 2)
                elif discount_option == "3瓶及以上8.5折" and quantity >= 3:
                    unit_price = round(unit_price * 0.85, 2)

            total_price = round(quantity * unit_price, 2)
            st.write(f"**{sales_type}总价：{total_price} 元**")

        # 备注
        remark = st.text_input("备注")

        # 保存按钮
        submitted = st.form_submit_button("保存记录")
        if submitted:
            new_record = {
                "日期": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "城市": city,
                "活动地点": location,
                "产品名称": product_name,
                "销售类型": sales_type,
                "数量": quantity,
                "单价": unit_price,
                "总价": total_price,
                "折扣": discount_option,
                "备注": remark
            }

            # 保存到销售记录
            df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
            df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
            df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

            # 同步更新库存
            new_inventory = {
                "日期": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "产品名称": product_name,
                "变动类型": "出库",
                "数量": -quantity,
                "备注": f"{sales_type} {quantity} 件"
            }
            inv_df = pd.read_csv(INVENTORY_FILE, encoding="utf-8-sig")
            inv_df = pd.concat([inv_df, pd.DataFrame([new_inventory])], ignore_index=True)
            inv_df.to_csv(INVENTORY_FILE, index=False, encoding="utf-8-sig")

            st.success("✅ 记录已保存，库存数据已同步更新！")

# ---------------- 库存管理模块 ----------------
elif page == "库存管理":
    st.header("库存管理")
    st.info("后续可扩展：入库、出库、库存预警、物料/赠品管理")

# ---------------- 费用与成本模块 ----------------
elif page == "费用与成本":
    st.header("费用与成本")
    st.info("后续可扩展：物料费、运费、杂费录入")

# ---------------- 盈利分析模块 ----------------
elif page == "盈利分析与洞察":
    st.header("盈利分析与洞察")
    st.info("后续可扩展：销量排行、试饮-成交转化率、成本核算、毛利分析")
