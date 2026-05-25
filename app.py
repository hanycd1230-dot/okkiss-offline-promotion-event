from __future__ import annotations
from datetime import date, datetime
from pathlib import Path
import pandas as pd
import streamlit as st

# ===================== 基础配置 =====================
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

# ===================== 初始化文件 =====================
def init_file(path, cols):
    if not path.exists():
        pd.DataFrame(columns=cols).to_csv(path, index=False, encoding="utf-8-sig")

init_file(DATA_FILE, ["日期", "城市", "活动地点", "产品名称", "销售类型", "数量", "单价", "总价", "折扣", "备注"])
init_file(INVENTORY_FILE, ["日期", "产品名称", "变动类型", "数量", "备注"])
init_file(COST_FILE, ["日期", "费用类型", "金额", "备注"])

# ===================== 页面初始化 =====================
st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
page = st.sidebar.radio("功能模块", PAGE_OPTIONS)

if "pwd_verified" not in st.session_state:
    st.session_state.pwd_verified = False

# ===================== 保存订单函数 =====================
def save_order(city, location, product, sale_type, qty, price, discount, remark):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    final_price = round(price * discount, 2)
    total = final_price * qty
    disc_text = f"{discount*10:.1f}折"

    # 销售记录
    row = {
        "日期": now, "城市": city, "活动地点": location, "产品名称": product,
        "销售类型": sale_type, "数量": qty, "单价": price, "总价": total,
        "折扣": disc_text, "备注": remark
    }
    df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

    # 库存记录
    inv_type = "出库" if sale_type != "试饮" else "试饮消耗"
    inv_row = {"日期": now, "产品名称": product, "变动类型": inv_type, "数量": -qty, "备注": sale_type}
    inv_df = pd.read_csv(INVENTORY_FILE, encoding="utf-8-sig")
    inv_df = pd.concat([inv_df, pd.DataFrame([inv_row])], ignore_index=True)
    inv_df.to_csv(INVENTORY_FILE, index=False, encoding="utf-8-sig")
    return total

# ===================== 销售录入（纯手动） =====================
if page == "销售录入":
    st.header("✅ 销售录入（纯手动）")

    # 公共信息
    c1, c2 = st.columns(2)
    with c1:
        city = st.selectbox("城市", ["上海", "杭州", "南京", "苏州", "其他"])
    with c2:
        activity_date = st.date_input("活动日期", date.today())

    location = st.selectbox("活动地点", ["上海来福士", "杭州湖滨银泰", "南京新街口", "苏州中心", "自定义"])
    if location == "自定义":
        location = st.text_input("输入地点")

    st.divider()

    # 表单录入
    product = st.selectbox("产品名称", PRODUCT_LIST)
    sale_type = st.radio("销售类型", ["瓶卖", "杯卖", "试饮"], horizontal=True)
    qty = st.number_input("数量", min_value=1, value=1)
    price = st.number_input("单价", min_value=0.01, value=float(PRODUCT_PRICES[product][sale_type]))
    discount = st.number_input("折扣率（9折=0.9）", min_value=0.1, max_value=1.0, value=1.0)
    remark = st.text_input("备注")

    # 计算总价
    final_price = round(price * discount, 2)
    total = final_price * qty
    st.success(f"💰 订单总价：{total:.2f} 元")

    # 保存按钮
    if st.button("✅ 保存当前订单"):
        save_order(city, location, product, sale_type, qty, price, discount, remark)
        st.success("✅ 保存成功，库存已更新！")

# ===================== 库存管理 =====================
elif page == "库存管理":
    st.header("📦 库存管理")
    df_inv = pd.read_csv(INVENTORY_FILE, encoding="utf-8-sig")
    df_inv["数量"] = pd.to_numeric(df_inv["数量"], errors="coerce")
    stock = df_inv.groupby("产品名称")["数量"].sum().reset_index()
    stock.columns = ["产品名称", "当前库存"]
    st.subheader("实时库存")
    st.dataframe(stock, use_container_width=True)

    st.divider()
    st.subheader("入库登记")
    with st.form("stock_in_form"):
        prod_in = st.selectbox("选择产品", PRODUCT_LIST)
        num_in = st.number_input("入库数量", min_value=1)
        if st.form_submit_button("确认入库"):
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            row = {"日期": now, "产品名称": prod_in, "变动类型": "入库", "数量": num_in, "备注": "手动入库"}
            df = pd.read_csv(INVENTORY_FILE, encoding="utf-8-sig")
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            df.to_csv(INVENTORY_FILE, index=False, encoding="utf-8-sig")
            st.success("入库完成")
    st.divider()
    st.subheader("库存流水记录")
    st.dataframe(df_inv, use_container_width=True)

# ===================== 费用与成本 =====================
elif page == "费用与成本":
    st.header("🧾 费用与成本")
    if not st.session_state.pwd_verified:
        pwd = st.text_input("请输入管理员密码", type="password")
        if st.button("验证"):
            if pwd == ADMIN_PWD:
                st.session_state.pwd_verified = True
                st.rerun()
            else:
                st.error("密码错误")
    else:
        with st.form("cost_form"):
            c_type = st.selectbox("费用类型", ["物料费", "运费", "场地费", "人工费", "杂费"])
            c_money = st.number_input("金额", min_value=0.01)
            c_rem = st.text_input("备注")
            if st.form_submit_button("保存费用"):
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                row = {"日期": now, "费用类型": c_type, "金额": c_money, "备注": c_rem}
                df = pd.read_csv(COST_FILE, encoding="utf-8-sig")
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                df.to_csv(COST_FILE, index=False, encoding="utf-8-sig")
                st.success("费用已记录")
        st.divider()
        st.dataframe(pd.read_csv(COST_FILE, encoding="utf-8-sig"), use_container_width=True)

# ===================== 盈利分析 =====================
elif page == "盈利分析与洞察":
    st.header("📈 盈利分析")
    if not st.session_state.pwd_verified:
        pwd = st.text_input("请输入管理员密码", type="password")
        if st.button("验证"):
            if pwd == ADMIN_PWD:
                st.session_state.pwd_verified = True
                st.rerun()
            else:
                st.error("密码错误")
    else:
        df_sale = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
        df_cost = pd.read_csv(COST_FILE, encoding="utf-8-sig")
        if df_sale.empty:
            st.warning("暂无销售数据")
        else:
            total_sale = df_sale["总价"].sum()
            total_cost = df_cost["金额"].sum() if not df_cost.empty else 0
            profit = total_sale - total_cost
            st.metric("总销售额", f"{total_sale:.2f} 元")
            st.metric("总支出费用", f"{total_cost:.2f} 元")
            st.metric("当前毛利", f"{profit:.2f} 元")
