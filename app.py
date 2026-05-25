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

# 会话状态初始化
if "auto_save_done" not in st.session_state:
    st.session_state.auto_save_done = False
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
    # 匹配产品
    for p in PRODUCT_LIST:
        if p in text:
            res["product"] = p
            break
    # 匹配杯/瓶
    if "杯" in text:
        res["sale_type"] = "杯卖"
    elif "瓶" in text:
        res["sale_type"] = "瓶卖"
    # 提取数字
    nums = re.findall(r"\d+\.?\d*", text)
    # 折扣
    res["discount"] = parse_discount(text)
    # 数量、单价
    if len(nums) >= 1:
        res["qty"] = int(float(nums[0]))
    if len(nums) >= 2:
        res["price"] = float(nums[1])
    # 提取备注
    clean_text = re.sub("|".join(PRODUCT_LIST) + r"|杯|瓶|元|块|折|\d+\.?\d*", "", text)
    res["remark"] = clean_text.strip()
    return res

# 保存销售+库存记录
def save_sale_record(city, location, product, sale_type, qty, price, total, discount, remark):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    # 销售记录
    row = {
        "日期": now_str, "城市": city, "活动地点": location, "产品名称": product,
        "销售类型": sale_type, "数量": qty, "单价": price, "总价": total,
        "折扣": discount, "备注": remark
    }
    df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
    # 库存记录
    inv_type = "出库" if sale_type != "试饮" else "试饮消耗"
    inv_row = {
        "日期": now_str, "产品名称": product, "变动类型": inv_type,
        "数量": -qty, "备注": sale_type
    }
    inv_df = pd.read_csv(INVENTORY_FILE, encoding="utf-8-sig")
    inv_df = pd.concat([inv_df, pd.DataFrame([inv_row])], ignore_index=True)
    inv_df.to_csv(INVENTORY_FILE, index=False, encoding="utf-8-sig")

# -------------------------- 主页面逻辑 --------------------------
if page == "销售录入":
    st.header("✅ 销售录入 | 语音极速自动下单")
    mode = st.radio("录入模式", ["🎤 语音一键自动下单", "⚡ 批量快速开单"], horizontal=True)

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

    # ========== 模式1：语音一键自动下单（核心） ==========
    if mode == "🎤 语音一键自动下单":
        st.subheader("🎙️ 操作规则：点击麦克风 → 一口气说完 → 自动识别+自动保存")
        st.info("标准话术示例：蜜桃 5杯 35 9折 地推新客")

        # 语音录制
        audio = st.audio_input("🎤 点击开始语音下单")
        if audio:
            st.info("正在识别语音，请稍等...")
            voice_text = st.text_input("识别结果（可手动修改）", key="voice_full")
            if voice_text:
                # 解析语音内容
                parsed = parse_one_shot(voice_text)
                st.session_state.parsed_data = parsed
                st.session_state.auto_save_done = False

        # 回填表单 + 自动保存
        if st.session_state.parsed_data and not st.session_state.auto_save_done:
            pd_data = st.session_state.parsed_data
            # 产品
            default_prod = pd_data["product"] if pd_data["product"] in PRODUCT_LIST else PRODUCT_LIST[0]
            product = st.selectbox("产品名称", PRODUCT_LIST, index=PRODUCT_LIST.index(default_prod))
            # 销售类型
            stype_list = ["瓶卖", "杯卖", "试饮"]
            default_stype = pd_data["sale_type"] if pd_data["sale_type"] in stype_list else "瓶卖"
            sales_type = st.radio("销售类型", stype_list, horizontal=True, index=stype_list.index(default_stype))
            # 数量
            default_qty = pd_data["qty"] if pd_data["qty"] else 1
            qty = st.number_input("数量", min_value=1, value=default_qty)
            # 单价
            default_price = pd_data["price"] if pd_data["price"] else PRODUCT_PRICES[product][sales_type]
            price = st.number_input("单价", min_value=0.01, value=float(default_price))
            # 折扣
            discount_val = st.number_input("折扣率（9折=0.9）", min_value=0.1, max_value=1.0, value=pd_data["discount"])
            # 备注
            remark = st.text_input("备注", value=pd_data["remark"])

            # 计算最终价格与总价
            final_price = round(price * discount_val, 2)
            total = final_price * qty
            discount_text = f"{discount_val * 10:.1f}折"
            st.success(f"💰 核算总价：{total:.2f} 元")

            # 自动保存
            save_sale_record(city, location, product, sales_type, qty, final_price, total, discount_text, remark)
            st.success("✅ 已自动保存！库存同步完成，可继续下一笔订单")
            # 标记已保存，防止重复提交
            st.session_state.auto_save_done = True
            # 清空解析数据，准备下一轮
            st.session_state.parsed_data = None

    # ========== 模式2：批量快速开单（保留原有功能） ==========
    else:
        st.subheader("⚡ 批量开单（适合多人同品类集中下单）")
        cup_col, bottle_col = st.columns(2)
        cup_num, bottle_num = 0, 0

        with cup_col:
            st.markdown("**🍷 批量杯卖**")
            cup_product = st.selectbox("杯卖产品", PRODUCT_LIST, key="cup_prod")
            c_col1, c_col2 = st.columns([3,1])
            with c_col1:
                cup_num = st.number_input("总杯数", min_value=0, value=0, key="cup_num")
            with c_col2:
                audio_cup = st.audio_input("🎤 报杯数")
                if audio_cup:
                    txt_cup = st.text_input("杯数识别结果", key="cup_voice")
                    n = extract_number(txt_cup)
                    if n:
                        cup_num = int(n)

        with bottle_col:
            st.markdown("**🍾 批量瓶卖**")
            bottle_product = st.selectbox("瓶卖产品", PRODUCT_LIST, key="bottle_prod")
            b_col1, b_col2 = st.columns([3,1])
            with b_col1:
                bottle_num = st.number_input("总瓶数", min_value=0, value=0, key="bottle_num")
            with b_col2:
                audio_bottle = st.audio_input("🎤 报瓶数")
                if audio_bottle:
                    txt_bottle = st.text_input("瓶数识别结果", key="bottle_voice")
                    n = extract_number(txt_bottle)
                    if n:
                        bottle_num = int(n)

        # 批量备注
        bat_col1, bat_col2 = st.columns([4,1])
        with bat_col1:
            batch_remark = st.text_input("批量备注(选填)")
        with bat_col2:
            audio_rem = st.audio_input("🎤 语音备注")
            if audio_rem:
                txt_rem = st.text_input("备注识别结果", key="rem_voice")
                batch_remark = txt_rem

        submit_batch = st.button("🚀 一键批量提交")
        if submit_batch:
            success_msg = []
            if cup_num > 0:
                p = PRODUCT_PRICES[cup_product]["杯卖"]
                total = p * cup_num
                save_sale_record(city, location, cup_product, "杯卖", cup_num, p, total, "无", batch_remark)
                success_msg.append(f"{cup_product} 杯卖 {cup_num}杯")
            if bottle_num > 0:
                p = PRODUCT_PRICES[bottle_product]["瓶卖"]
                total = p * bottle_num
                save_sale_record(city, location, bottle_product, "瓶卖", bottle_num, p, total, "无", batch_remark)
                success_msg.append(f"{bottle_product} 瓶卖 {bottle_num}瓶")
            if success_msg:
                st.success(f"✅ 批量录入完成：{' | '.join(success_msg)}")
            else:
                st.warning("⚠️ 请填写杯数/瓶数")

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
