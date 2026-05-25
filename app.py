from __future__ import annotations
from datetime import date, datetime
from pathlib import Path
import pandas as pd
import streamlit as st

# -------------------------- 基础配置 --------------------------
APP_TITLE = "OKKISS 地推销售与库存管理"
ADMIN_PWD = "okkiss2026"
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DATA_FILE = DATA_DIR / "sales_records.csv"
INVENTORY_FILE = DATA_DIR / "inventory_movements.csv"
COST_FILE = DATA_DIR / "cost_records.csv"
PRICE_FILE = DATA_DIR / "price_settings.csv"

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

# -------------------------- 产品图片（占位图，可替换） --------------------------
PRODUCT_IMAGES = {
    "草莓": "https://via.placeholder.com/300x400.png?text=草莓",
    "小草莓": "https://via.placeholder.com/300x400.png?text=小草莓",
    "蜜桃": "https://via.placeholder.com/300x400.png?text=蜜桃",
    "蜜桃乌龙无醇": "https://via.placeholder.com/300x400.png?text=蜜桃乌龙无醇",
    "阿斯蒂甜白": "https://via.placeholder.com/300x400.png?text=阿斯蒂甜白",
    "莫斯卡托桃红": "https://via.placeholder.com/300x400.png?text=莫斯卡托桃红",
    "绿宝石": "https://via.placeholder.com/300x400.png?text=绿宝石",
    "紫宝石": "https://via.placeholder.com/300x400.png?text=紫宝石",
    "快乐王子": "https://via.placeholder.com/300x400.png?text=快乐王子",
    "长相思": "https://via.placeholder.com/300x400.png?text=长相思",
    "赤霞珠": "https://via.placeholder.com/300x400.png?text=赤霞珠"
}

# -------------------------- 初始化文件 --------------------------
def init_file(path, cols):
    if not path.exists():
        pd.DataFrame(columns=cols).to_csv(path, index=False, encoding="utf-8-sig")

init_file(DATA_FILE, ["日期", "城市", "活动地点", "产品名称", "销售类型", "数量", "单价", "总价", "折扣", "备注"])
init_file(INVENTORY_FILE, ["日期", "产品名称", "变动类型", "数量", "备注"])
init_file(COST_FILE, ["日期", "费用类型", "金额", "备注"])
init_file(PRICE_FILE, ["产品名称", "瓶卖", "杯卖"])

# -------------------------- 页面初始化 --------------------------
st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
page = st.sidebar.radio("功能模块", PAGE_OPTIONS)

if "pwd_verified" not in st.session_state:
    st.session_state.pwd_verified = False

# ======================================================================================
# ===================================== 销售录入（带产品图片） =======================================
# ======================================================================================
if page == "销售录入":
    st.header("✅ 销售录入（带产品图）")
    col1, col2 = st.columns(2)
    with col1:
        city = st.selectbox("城市", ["上海", "杭州", "南京", "苏州", "其他"])
    with col2:
        activity_date = st.date_input("活动日期", date.today())

    location = st.selectbox("活动地点", ["上海来福士", "杭州湖滨银泰", "南京新街口", "苏州中心", "自定义"])
    if location == "自定义":
        location = st.text_input("输入地点")

    st.divider()
    st.subheader("快速录入（左选产品，右看图片）")

    form_col, img_col = st.columns([2, 1])

    with form_col:
        with st.form("sales_form"):
            product = st.selectbox("产品名称", PRODUCT_LIST)
            sales_type = st.radio("销售类型", ["瓶卖", "杯卖", "试饮"], horizontal=True)
            qty = st.number_input("数量", min_value=1, value=1)
            price = 0
            total = 0
            discount = "无"

            if sales_type in ["瓶卖", "杯卖"]:
                price = PRODUCT_PRICES[product][sales_type]
                if sales_type == "瓶卖":
                    discount = st.radio("折扣", ["无", "2瓶9折", "3瓶85折"], horizontal=True)
                    if discount == "2瓶9折" and qty >= 2:
                        price = round(price * 0.9, 2)
                    if discount == "3瓶85折" and qty >= 3:
                        price = round(price * 0.85, 2)
                total = price * qty
                st.success(f"💰 总价：{total} 元")

            remark = st.text_input("备注")
            submit = st.form_submit_button("✅ 保存记录")

            if submit:
                row = {
                    "日期": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "城市": city,
                    "活动地点": location,
                    "产品名称": product,
                    "销售类型": sales_type,
                    "数量": qty,
                    "单价": price,
                    "总价": total,
                    "折扣": discount,
                    "备注": remark
                }
                df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

                inv_row = {
                    "日期": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "产品名称": product,
                    "变动类型": "出库" if sales_type != "试饮" else "试饮消耗",
                    "数量": -qty,
                    "备注": sales_type
                }
                inv_df = pd.read_csv(INVENTORY_FILE, encoding="utf-8-sig")
                inv_df = pd.concat([inv_df, pd.DataFrame([inv_row])], ignore_index=True)
                inv_df.to_csv(INVENTORY_FILE, index=False, encoding="utf-8-sig")

                st.success("✅ 保存成功！库存已同步更新！")

    with img_col:
        st.subheader("产品实物图")
        st.image(PRODUCT_IMAGES[product], caption=product, width=300)
        st.caption("（可替换为真实酒品图）")

# ======================================================================================
# ===================================== 库存管理 =======================================
# ======================================================================================
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

# ======================================================================================
# =================================== 费用与成本（需密码）======================================
# ======================================================================================
elif page == "费用与成本":
    st.header("🧾 费用与成本")

    if not st.session_state.pwd_verified:
        st.warning("🔒 该模块需要管理员密码才能访问")
        input_pwd = st.text_input("请输入密码", type="password")
        if st.button("验证密码"):
            if input_pwd == ADMIN_PWD:
                st.session_state.pwd_verified = True
                st.rerun()
            else:
                st.error("❌ 密码错误，请重新输入")
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

        if not cost_df.empty:
            total_cost = cost_df["金额"].sum()
            st.subheader(f"📊 总费用支出：**{total_cost:.2f} 元**")

# ======================================================================================
# ================================ 盈利分析与洞察（需密码）======================================
# ======================================================================================
elif page == "盈利分析与洞察":
    st.header("📈 盈利分析与洞察")

    if not st.session_state.pwd_verified:
        st.warning("🔒 该模块需要管理员密码才能访问")
        input_pwd = st.text_input("请输入密码", type="password")
        if st.button("验证密码"):
            if input_pwd == ADMIN_PWD:
                st.session_state.pwd_verified = True
                st.rerun()
            else:
                st.error("❌ 密码错误，请重新输入")
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
            total_test = sales[sales["销售类型"] == "试饮"]["数量"].sum()

            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("总销售额", f"{total_revenue:.2f}元")
            with col_b:
                st.metric("总瓶卖", f"{total_bottle}瓶")
            with col_c:
                st.metric("总杯卖", f"{total_cup}杯")
            with col_d:
                st.metric("总试饮", f"{total_test}杯")

            st.divider()
            st.subheader("🍷 各产品销量 & 试饮统计")
            product_stats = sales.groupby(["产品名称", "销售类型"])["数量"].sum().unstack(fill_value=0)
            st.dataframe(product_stats, use_container_width=True)

            st.divider()
            st.subheader("🎯 试饮 → 成交 分析")
            if total_test > 0 and total_bottle > 0:
                rate = total_bottle / total_test
                st.success(f"✅ 平均 **{rate:.2f} 杯试饮 → 成交 1 瓶**")
                st.info("可直接核算单瓶成交对应的试饮成本")
            else:
                st.info("试饮或瓶卖数据不足，暂时无法计算转化率")

            st.divider()
            total_cost = cost_df["金额"].sum() if not cost_df.empty else 0
            profit = total_revenue - total_cost
            st.subheader(f"💰 最终毛利：**{profit:.2f} 元**")
            st.caption(f"总销售额 {total_revenue:.2f} 元 - 总费用 {total_cost:.2f} 元")
