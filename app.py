from __future__ import annotations
from datetime import date, datetime
from pathlib import Path
import pandas as pd
import streamlit as st
import re

# -------------------------- 基础配置 --------------------------
APP_TITLE = "OKKISS 地推销售与库存管理"
ADMIN_PWD = "okkiss2026"
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DATA_FILE = DATA_DIR / "sales_records.csv"
INVENTORY_FILE = DATA_DIR / "inventory_movements.csv"
COST_FILE = DATA_DIR / "cost_records.csv"

PAGE_OPTIONS = ["销售录入", "库存管理", "费用与成本", "盈利分析与洞察"]

PRODUCT_LIST = [
    "草莓", "小草莓", "蜜桃", "蜜桃乌龙无醇", "阿斯蒂甜白",
    "莫斯卡托桃红", "绿宝石", "紫宝石", "快乐王子", "长相思", "赤霞珠"
]

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

# -------------------------- 初始化文件 --------------------------
def init_file(path, cols):
    if not path.exists():
        pd.DataFrame(columns=cols).to_csv(path, index=False, encoding="utf-8-sig")

init_file(DATA_FILE, ["日期", "城市", "活动地点", "产品名称", "销售类型", "数量", "单价", "总价", "折扣", "备注"])
init_file(INVENTORY_FILE, ["日期", "产品名称", "变动类型", "数量", "备注"])
init_file(COST_FILE, ["日期", "费用类型", "金额", "备注"])

# -------------------------- 页面初始化 --------------------------
st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
page = st.sidebar.radio("功能模块", PAGE_OPTIONS)

if "pwd_verified" not in st.session_state:
    st.session_state.pwd_verified = False
if "parsed_data" not in st.session_state:
    st.session_state.parsed_data = None

# -------------------------- 解析工具函数 --------------------------
def extract_number(text: str):
    nums = re.findall(r"\d+\.?\d*", text)
    return float(nums[0]) if nums else None

def parse_discount(text: str):
    if "折" in text:
        num = extract_number(text)
        return num / 10 if num else 1.0
    return 1.0

def parse_sale_type(text: str):
    if "杯" in text:
        return "杯卖"
    if "瓶" in text:
        return "瓶卖"
    return None

def parse_one_shot(text: str):
    res = {
        "product": None,
        "sale_type": None,
        "qty": None,
        "price": None,
        "discount": 1.0,
        "remark": ""
    }
    for p in PRODUCT_LIST:
        if p in text:
            res["product"] = p
            break
    if "杯" in text:
        res["sale_type"] = "杯卖"
    elif "瓶" in text:
        res["sale_type"] = "瓶卖"
    nums = re.findall(r"\d+\.?\d*", text)
    res["discount"] = parse_discount(text)
    if len(nums) >= 1:
        res["qty"] = int(float(nums[0]))
    if len(nums) >= 2:
        res["price"] = float(nums[1])
    clean_text = re.sub("|".join(PRODUCT_LIST) + r"|杯|瓶|元|块|折|\d+\.?\d*", "", text)
    res["remark"] = clean_text.strip()
    return res

# 保存销售+库存记录
def save_sale_record(city, location, product, sale_type, qty, price, total, discount, remark):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    row = {
        "日期": now_str, "城市": city, "活动地点": location, "产品名称": product,
        "销售类型": sale_type, "数量": qty, "单价": price, "总价": total,
        "折扣": discount, "备注": remark
    }
    df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

    inv_type = "出库" if sale_type != "试饮" else "试饮消耗"
    inv_row = {
        "日期": now_str, "产品名称": product, "变动类型": inv_type,
        "数量": -qty, "备注": sale_type
    }
    inv_df = pd.read_csv(INVENTORY_FILE, encoding="utf-8-sig")
    inv_df = pd.concat([inv_df, pd.DataFrame([inv_row])], ignore_index=True)
    inv_df.to_csv(INVENTORY_FILE, index=False, encoding="utf-8-sig")

# -------------------------- 销售录入主逻辑 --------------------------
if page == "销售录入":
    st.header("✅ 销售录入 | 语音+手动 双输入（同时显示）")

    # 公共基础信息
    col1, col2 = st.columns(2)
    with col1:
        city = st.selectbox("城市", ["上海", "杭州", "南京", "苏州", "其他"])
    with col2:
        activity_date = st.date_input("活动日期", date.today())

    location = st.selectbox("活动地点", ["上海来福士", "杭州湖滨银泰", "南京新街口", "苏州中心", "自定义"])
    if location == "自定义":
        location = st.text_input("输入地点")

    st.divider()

    # ========== 上半区：语音输入区 ==========
    st.subheader("🎤 语音输入（说完自动填入下方表单）")
    st.info("示例：蜜桃 5杯 35 9折 地推新客")
    audio = st.audio_input("🎤 点击麦克风，一口气说完订单信息")
    if audio:
        st.info("识别中...")
        voice_text = st.text_input("语音识别结果（可改）", key="voice_full")
        if voice_text:
            st.session_state.parsed_data = parse_one_shot(voice_text)

    st.divider()

    # ========== 下半区：完整手动表单区（语音自动回填） ==========
    st.subheader("📝 手动表单（可直接手填，也可语音自动填入）")
    pd_data = st.session_state.parsed_data

    # 产品
    prod_def = pd_data["product"] if (pd_data and pd_data["product"] in PRODUCT_LIST) else PRODUCT_LIST[0]
    product = st.selectbox("产品名称", PRODUCT_LIST, index=PRODUCT_LIST.index(prod_def))

    # 销售类型
    stype_list = ["瓶卖", "杯卖", "试饮"]
    stype_def = pd_data["sale_type"] if (pd_data and pd_data["sale_type"]) else "瓶卖"
    sales_type = st.radio("销售类型", stype_list, horizontal=True, index=stype_list.index(stype_def))

    # 数量
    qty_def = pd_data["qty"] if (pd_data and pd_data["qty"]) else 1
    qty = st.number_input("数量", min_value=1, value=qty_def)

    # 单价
    price_def = pd_data["price"] if (pd_data and pd_data["price"]) else PRODUCT_PRICES[product][sales_type]
    price = st.number_input("单价", min_value=0.01, value=float(price_def))

    # 折扣
    disc_def = pd_data["discount"] if (pd_data and pd_data["discount"]) else 1.0
    discount_val = st.number_input("折扣率（9折=0.9）", min_value=0.1, max_value=1.0, value=disc_def)

    # 备注
    remark_def = pd_data["remark"] if (pd_data and pd_data["remark"]) else ""
    remark = st.text_input("备注", value=remark_def)

    # 核算
    final_price = round(price * discount_val, 2)
    total = final_price * qty
    discount_text = f"{discount_val * 10:.1f}折"
    st.success(f"💰 核算总价：{total:.2f} 元")

    # 保存按钮
    if st.button("✅ 保存订单（语音/手动都可）"):
        save_sale_record(city, location, product, sales_type, qty, final_price, total, discount_text, remark)
        st.success("✅ 保存成功，库存已同步！")
        st.session_state.parsed_data = None

# -------------------------- 库存管理 --------------------------
elif page == "库存管理":
    st.header("📦 库存管理")
    inv = pd.read_csv(INVENTORY_FILE, encoding="utf-8-sig")
    inv["数量"] = pd.to_numeric(inv["数量"], errors="coerce")
    stock = inv.groupby("产品名称")["数量"].sum().reset_index()
    stock.columns = ["产品名称", "当前库存"]
    st.subheader("📊 当前实时库存")
    st.dataframe(stock, use_container_width=True)
    st.divider()
    st.subheader("➡️ 入库登记")
    with st.form("stock_in"):
        p = st.selectbox("产品", PRODUCT_LIST)
        n = st.number_input("入库数量", min_value=1)
        btn_in = st.form_submit_button("✅ 确认入库")
        if btn_in:
            new_row = {
                "日期": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "产品名称": p,
                "变动类型": "入库",
                "数量": n,
                "备注": "手动入库"
            }
            df = pd.read_csv(INVENTORY_FILE, encoding="utf-8-sig")
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(INVENTORY_FILE, index=False, encoding="utf-8-sig")
            st.success("✅ 入库成功")
    st.divider()
    st.subheader("🗒 全部库存流水")
    st.dataframe(inv, use_container_width=True)

# -------------------------- 费用与成本 --------------------------
elif page == "费用与成本":
    st.header("🧾 费用与成本")
    if not st.session_state.pwd_verified:
        st.warning("🔒 该模块需要管理员密码")
        input_pwd = st.text_input("请输入密码", type="password")
        if st.button("验证密码"):
            if input_pwd == ADMIN_PWD:
                st.session_state.pwd_verified = True
                st.rerun()
            else:
                st.error("❌ 密码错误")
    else:
        st.subheader("➕ 新增费用")
        with st.form("cost_form"):
            cost_type = st.selectbox("费用类型", ["物料费", "运费", "场地费", "人工费", "杂费"])
            amount = st.number_input("金额（元）", min_value=0.01)
            remark_cost = st.text_input("备注")
            submit_cost = st.form_submit_button("✅ 保存费用")
            if submit_cost:
                row = {
                    "日期": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "费用类型": cost_type,
                    "金额": amount,
                    "备注": remark_cost
                }
                df = pd.read_csv(COST_FILE, encoding="utf-8-sig")
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                df.to_csv(COST_FILE, index=False, encoding="utf-8-sig")
                st.success("✅ 费用已记录")
        st.divider()
        cost_df = pd.read_csv(COST_FILE, encoding="utf-8-sig")
        st.subheader("📋 全部费用记录")
        st.dataframe(cost_df, use_container_width=True)

# -------------------------- 盈利分析 --------------------------
elif page == "盈利分析与洞察":
    st.header("📈 盈利分析与洞察")
    if not st.session_state.pwd_verified:
        st.warning("🔒 该模块需要管理员密码")
        input_pwd = st.text_input("请输入密码", type="password")
        if st.button("验证密码"):
            if input_pwd == ADMIN_PWD:
                st.session_state.pwd_verified = True
                st.rerun()
            else:
                st.error("❌ 密码错误")
    else:
        sales = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
        cost_df = pd.read_csv(COST_FILE, encoding="utf-8-sig")
        if sales.empty:
            st.warning("暂无销售数据")
        else:
            sales["数量"] = pd.to_numeric(sales["数量"], errors="coerce")
            sales["总价"] = pd.to_numeric(sales["总价"], errors="coerce")
            total_revenue = sales["总价"].sum()
            total_bottle = sales[sales["销售类型"] == "瓶卖"]["数量"].sum()
            total_cup = sales[sales["销售类型"] == "杯卖"]["数量"].sum()

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("总销售额", f"{total_revenue:.2f}元")
            with col_b:
                st.metric("总瓶卖", f"{total_bottle}瓶")
            with col_c:
                st.metric("总杯卖", f"{total_cup}杯")

            st.divider()
            total_cost = cost_df["金额"].sum() if not cost_df.empty else 0
            profit = total_revenue - total_cost
            st.subheader(f"💰 最终毛利：**{profit:.2f} 元**")
