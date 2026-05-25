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

# 数据文件路径
DATA_FILE = DATA_DIR / "sales_records.csv"
INVENTORY_FILE = DATA_DIR / "inventory_movements.csv"
COST_FILE = DATA_DIR / "cost_records.csv"
RETURN_FILE = DATA_DIR / "return_records.csv"
PRODUCT_COST_FILE = DATA_DIR / "product_costs.csv"

PAGE_OPTIONS = ["销售录入", "销售记录/删除单据", "退货登记", "库存管理", "费用与成本", "盈利分析与洞察"]

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
init_file(RETURN_FILE, ["日期", "产品名称", "销售类型", "数量", "原因", "备注"])
# 初始化产品成本表（产品+成本）
init_file(PRODUCT_COST_FILE, ["产品名称", "成本单价"])
# 如果是首次运行，填充默认成本
if len(pd.read_csv(PRODUCT_COST_FILE, encoding="utf-8-sig")) == 0:
    default_costs = pd.DataFrame({
        "产品名称": PRODUCT_LIST,
        "成本单价": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    })
    default_costs.to_csv(PRODUCT_COST_FILE, index=False, encoding="utf-8-sig")

# ===================== 页面初始化 =====================
st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
page = st.sidebar.radio("功能模块", PAGE_OPTIONS)

if "pwd_verified" not in st.session_state:
    st.session_state.pwd_verified = False

# ===================== 通用函数 =====================
def save_order(city, location, product, sale_type, qty, price, discount, remark):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    final_price = round(price * discount, 2)
    total = final_price * qty
    disc_text = f"{discount*10:.1f}折"

    row = {
        "日期": now, "城市": city, "活动地点": location, "产品名称": product,
        "销售类型": sale_type, "数量": qty, "单价": price, "总价": total,
        "折扣": disc_text, "备注": remark
    }
    df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

    inv_type = "出库" if sale_type != "试饮" else "试饮消耗"
    inv_row = {"日期": now, "产品名称": product, "变动类型": inv_type, "数量": -qty, "备注": sale_type}
    inv_df = pd.read_csv(INVENTORY_FILE, encoding="utf-8-sig")
    inv_df = pd.concat([inv_df, pd.DataFrame([inv_row])], ignore_index=True)
    inv_df.to_csv(INVENTORY_FILE, index=False, encoding="utf-8-sig")
    return total

# 删除单条销售记录并恢复库存
def del_sale_record(idx):
    sales_df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
    if idx < 0 or idx >= len(sales_df):
        return False
    row = sales_df.iloc[idx]
    product = row["产品名称"]
    sale_type = row["销售类型"]
    qty = int(row["数量"])

    sales_df = sales_df.drop(idx).reset_index(drop=True)
    sales_df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    inv_df = pd.read_csv(INVENTORY_FILE, encoding="utf-8-sig")
    inv_row = {"日期": now, "产品名称": product, "变动类型": "退货/撤销单据", "数量": qty, "备注": f"撤销{sale_type}单据"}
    inv_df = pd.concat([inv_df, pd.DataFrame([inv_row])], ignore_index=True)
    inv_df.to_csv(INVENTORY_FILE, index=False, encoding="utf-8-sig")
    return True

# 登记退货并恢复库存
def add_return(product, sale_type, qty, reason, remark):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    ret_row = {"日期": now, "产品名称": product, "销售类型": sale_type, "数量": qty, "原因": reason, "备注": remark}
    ret_df = pd.read_csv(RETURN_FILE, encoding="utf-8-sig")
    ret_df = pd.concat([ret_df, pd.DataFrame([ret_row])], ignore_index=True)
    ret_df.to_csv(RETURN_FILE, index=False, encoding="utf-8-sig")

    inv_df = pd.read_csv(INVENTORY_FILE, encoding="utf-8-sig")
    inv_row = {"日期": now, "产品名称": product, "变动类型": "退货入库", "数量": qty, "备注": f"{sale_type}退货"}
    inv_df = pd.concat([inv_df, pd.DataFrame([inv_row])], ignore_index=True)
    inv_df.to_csv(INVENTORY_FILE, index=False, encoding="utf-8-sig")

# 导出CSV按钮通用函数
def download_csv(df, filename):
    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 导出为CSV文件",
        data=csv,
        file_name=filename,
        mime="text/csv"
    )

# ===================== 1. 销售录入 =====================
if page == "销售录入":
    st.header("✅ 销售录入（纯手动）")

    c1, c2 = st.columns(2)
    with c1:
        city = st.selectbox("城市", ["上海", "杭州", "南京", "苏州", "其他"])
    with c2:
        activity_date = st.date_input("活动日期", date.today())

    location = st.selectbox("活动地点", ["上海来福士", "杭州湖滨银泰", "南京新街口", "苏州中心", "自定义"])
    if location == "自定义":
        location = st.text_input("输入地点")

    st.divider()

    product = st.selectbox("产品名称", PRODUCT_LIST)
    sale_type = st.radio("销售类型", ["瓶卖", "杯卖", "试饮"], horizontal=True)
    qty = st.number_input("数量", min_value=1, value=1)
    price = st.number_input("单价", min_value=0.01, value=float(PRODUCT_PRICES[product][sale_type]))
    discount = st.number_input("折扣率（9折=0.9）", min_value=0.1, max_value=1.0, value=1.0)
    remark = st.text_input("备注")

    final_price = round(price * discount, 2)
    total = final_price * qty
    st.success(f"💰 订单总价：{total:.2f} 元")

    if st.button("✅ 保存当前订单"):
        save_order(city, location, product, sale_type, qty, price, discount, remark)
        st.success("✅ 保存成功，库存已更新！")

# ===================== 2. 销售记录 & 删除单据 + 导出 =====================
elif page == "销售记录/删除单据":
    st.header("📋 全部销售记录 | 删除错误单据")
    st.warning("⚠️ 删除单据后会自动恢复对应库存，请谨慎操作！")
    df_sale = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
    df_sale.index.name = "序号"
    st.dataframe(df_sale, use_container_width=True)
    download_csv(df_sale, "销售记录.csv")

    st.divider()
    st.subheader("🗑️ 删除指定单据")
    del_idx = st.number_input("输入要删除的【序号】", min_value=0, value=0)
    if st.button("❌ 删除该条单据"):
        if del_sale_record(del_idx):
            st.success("✅ 删除成功，库存已恢复！请刷新页面查看最新记录")
        else:
            st.error("❌ 序号不存在，请检查后重试")

# ===================== 3. 退货登记 + 导出 =====================
elif page == "退货登记":
    st.header("🔄 客户退货登记")
    product = st.selectbox("退货产品", PRODUCT_LIST)
    sale_type = st.radio("原销售类型", ["瓶卖", "杯卖", "试饮"], horizontal=True)
    ret_qty = st.number_input("退货数量", min_value=1, value=1)
    ret_reason = st.selectbox("退货原因", ["品质问题", "客户拒收", "拍错/买多", "其他"])
    ret_remark = st.text_input("补充备注")

    if st.button("✅ 确认退货"):
        add_return(product, sale_type, ret_qty, ret_reason, ret_remark)
        st.success("✅ 退货登记完成，商品已恢复库存！")

    st.divider()
    st.subheader("📄 历史退货记录")
    df_ret = pd.read_csv(RETURN_FILE, encoding="utf-8-sig")
    st.dataframe(df_ret, use_container_width=True)
    download_csv(df_ret, "退货记录.csv")

# ===================== 4. 库存管理 + 产品成本维护 + 导出 =====================
elif page == "库存管理":
    st.header("📦 库存管理（含成本）")

    # 读取库存和成本数据
    df_inv = pd.read_csv(INVENTORY_FILE, encoding="utf-8-sig")
    df_inv["数量"] = pd.to_numeric(df_inv["数量"], errors="coerce")
    df_cost = pd.read_csv(PRODUCT_COST_FILE, encoding="utf-8-sig")

    # 计算实时库存并合并成本
    stock = df_inv.groupby("产品名称")["数量"].sum().reset_index()
    stock.columns = ["产品名称", "当前库存"]
    # 合并成本
    stock = stock.merge(df_cost, on="产品名称", how="right")
    # 补全缺失的库存（新添加成本的产品）
    stock["当前库存"] = stock["当前库存"].fillna(0).astype(int)
    # 计算库存总成本
    stock["库存总成本"] = round(stock["当前库存"] * stock["成本单价"], 2)

    st.subheader("📊 实时库存 & 成本一览")
    st.dataframe(stock, use_container_width=True)
    download_csv(stock, "库存成本报表.csv")

    st.divider()
    st.subheader("✏️ 维护产品成本单价")
    # 选择产品并修改成本
    cost_product = st.selectbox("选择要维护成本的产品", PRODUCT_LIST)
    # 获取当前成本
    current_cost = df_cost.loc[df_cost["产品名称"] == cost_product, "成本单价"].values[0]
    new_cost = st.number_input("设置成本单价", min_value=0.0, value=float(current_cost), step=0.1)

    if st.button("✅ 更新成本单价"):
        df_cost.loc[df_cost["产品名称"] == cost_product, "成本单价"] = new_cost
        df_cost.to_csv(PRODUCT_COST_FILE, index=False, encoding="utf-8-sig")
        st.success(f"✅ {cost_product} 的成本单价已更新为：{new_cost} 元")
        st.info("刷新页面即可看到最新的库存总成本")

    st.divider()
    st.subheader("➡️ 入库登记")
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
    download_csv(df_inv, "库存流水记录.csv")

# ===================== 5. 费用与成本 + 导出 =====================
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
        df_cost = pd.read_csv(COST_FILE, encoding="utf-8-sig")
        st.dataframe(df_cost, use_container_width=True)
        download_csv(df_cost, "费用记录.csv")

# ===================== 6. 盈利分析与洞察 =====================
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
        df_prod_cost = pd.read_csv(PRODUCT_COST_FILE, encoding="utf-8-sig")

        if df_sale.empty:
            st.warning("暂无销售数据")
        else:
            # 读取数据并转换
            df_sale["数量"] = pd.to_numeric(df_sale["数量"], errors="coerce")
            df_sale["总价"] = pd.to_numeric(df_sale["总价"], errors="coerce")
            df_sale["单价"] = pd.to_numeric(df_sale["单价"], errors="coerce")

            # 合并成本数据
            df_sale = df_sale.merge(df_prod_cost, on="产品名称", how="left")
            df_sale["成本单价"] = df_sale["成本单价"].fillna(0)

            # 计算毛利
            df_sale["成本总额"] = df_sale["数量"] * df_sale["成本单价"]
            df_sale["毛利"] = df_sale["总价"] - df_sale["成本总额"]

            # 汇总数据
            total_sale = df_sale["总价"].sum()
            total_cost = df_cost["金额"].sum() if not df_cost.empty else 0
            total_prod_cost = df_sale["成本总额"].sum()
            total_gross_profit = df_sale["毛利"].sum()
            net_profit = total_gross_profit - total_cost

            # 显示指标
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("总销售额", f"{total_sale:.2f} 元")
            with col2:
                st.metric("商品总成本", f"{total_prod_cost:.2f} 元")
            with col3:
                st.metric("总支出费用", f"{total_cost:.2f} 元")
            with col4:
                st.metric("净利润", f"{net_profit:.2f} 元")

            st.divider()
            st.subheader("📄 销售明细（含毛利）")
            st.dataframe(df_sale, use_container_width=True)
            download_csv(df_sale, "销售毛利明细.csv")
