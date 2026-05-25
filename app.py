from __future__ import annotations
from datetime import date, datetime
from pathlib import Path
import pandas as pd
import streamlit as st
import re

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

# 会话状态：单独存储每个字段语音结果
if "voice_product" not in st.session_state:
    st.session_state.voice_product = ""
if "voice_type" not in st.session_state:
    st.session_state.voice_type = ""
if "voice_qty" not in st.session_state:
    st.session_state.voice_qty = ""
if "voice_price" not in st.session_state:
    st.session_state.voice_price = ""
if "voice_discount" not in st.session_state:
    st.session_state.voice_discount = ""
if "voice_remark" not in st.session_state:
    st.session_state.voice_remark = ""
if "pwd_verified" not in st.session_state:
    st.session_state.pwd_verified = False

# ===================== 简易解析工具（高容错） =====================
def get_num(text):
    """提取数字，容错最高"""
    res = re.findall(r"\d+", text)
    return res[0] if res else ""

def match_product(text):
    """模糊匹配产品"""
    for p in PRODUCT_LIST:
        if p in text:
            return p
    return ""

def match_sale_type(text):
    if "杯" in text:
        return "杯卖"
    if "瓶" in text:
        return "瓶卖"
    return ""

def match_discount(text):
    num = get_num(text)
    if num:
        n = int(num)
        if 1 <= n <= 10:
            return n / 10
    return 1.0

# ===================== 保存函数 =====================
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

# ===================== 销售录入（单字段语音 + 手动同屏） =====================
if page == "销售录入":
    st.header("✅ 销售录入 | 分字段语音 + 手动输入（高灵敏）")
    st.info("💡 建议：逐个点麦克风说短内容，比一整段识别更稳！嘈杂环境优先手动")

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
    st.subheader("🎤 分字段语音录入（每个字段独立麦克风）")

    # 1. 产品名称
    col_p1, col_p2 = st.columns([4,1])
    with col_p2:
        audio_p = st.audio_input("产品")
        if audio_p:
            st.session_state.voice_product = st.text_input("产品语音", value="", key="vp")
    prod_text = st.session_state.voice_product
    match_p = match_product(prod_text)
    default_p = match_p if match_p else PRODUCT_LIST[0]
    with col_p1:
        product = st.selectbox("产品名称", PRODUCT_LIST, index=PRODUCT_LIST.index(default_p))

    # 2. 销售类型（杯/瓶）
    col_t1, col_t2 = st.columns([4,1])
    with col_t2:
        audio_t = st.audio_input("杯/瓶")
        if audio_t:
            st.session_state.voice_type = st.text_input("类型语音", value="", key="vt")
    type_text = st.session_state.voice_type
    match_t = match_sale_type(type_text)
    type_list = ["瓶卖", "杯卖", "试饮"]
    default_t = match_t if match_t else "瓶卖"
    with col_t1:
        sale_type = st.radio("销售类型", type_list, horizontal=True, index=type_list.index(default_t))

    # 3. 数量
    col_q1, col_q2 = st.columns([4,1])
    with col_q2:
        audio_q = st.audio_input("数量")
        if audio_q:
            st.session_state.voice_qty = st.text_input("数量语音", value="", key="vq")
    qty_text = st.session_state.voice_qty
    qty_num = get_num(qty_text)
    default_q = int(qty_num) if qty_num else 1
    with col_q1:
        qty = st.number_input("数量", min_value=1, value=default_q)

    # 4. 单价
    col_pr1, col_pr2 = st.columns([4,1])
    with col_pr2:
        audio_pr = st.audio_input("单价")
        if audio_pr:
            st.session_state.voice_price = st.text_input("单价语音", value="", key="vpr")
    price_text = st.session_state.voice_price
    price_num = get_num(price_text)
    default_pr = float(price_num) if price_num else PRODUCT_PRICES[product][sale_type]
    with col_pr1:
        price = st.number_input("单价", min_value=0.01, value=default_pr)

    # 5. 折扣
    col_d1, col_d2 = st.columns([4,1])
    with col_d2:
        audio_d = st.audio_input("折扣")
        if audio_d:
            st.session_state.voice_discount = st.text_input("折扣语音", value="", key="vd")
    disc_text = st.session_state.voice_discount
    disc_val = match_discount(disc_text)
    with col_d1:
        discount = st.number_input("折扣率（9折=0.9）", min_value=0.1, max_value=1.0, value=disc_val)

    # 6. 备注
    col_r1, col_r2 = st.columns([4,1])
    with col_r2:
        audio_r = st.audio_input("备注")
        if audio_r:
            st.session_state.voice_remark = st.text_input("备注语音", value="", key="vr")
    remark = st.session_state.voice_remark
    with col_r1:
        remark = st.text_input("备注", value=remark)

    # 总价计算
    final_price = round(price * discount, 2)
    total = final_price * qty
    st.success(f"💰 订单总价：{total:.2f} 元")

    # 保存按钮
    if st.button("✅ 保存当前订单"):
        save_order(city, location, product, sale_type, qty, price, discount, remark)
        st.success("✅ 保存成功，库存已更新！")
        # 清空语音缓存，下一笔重新录入
        st.session_state.voice_product = ""
        st.session_state.voice_type = ""
        st.session_state.voice_qty = ""
        st.session_state.voice_price = ""
        st.session_state.voice_discount = ""
        st.session_state.voice_remark = ""

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
