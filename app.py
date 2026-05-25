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


APP_TITLE = "OKKISS 地推销售与库存管理"
MANAGER_PASSWORD = "okkiss2026"
DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "sales_records.csv"
INVENTORY_FILE = DATA_DIR / "inventory_movements.csv"
COST_FILE = DATA_DIR / "cost_records.csv"
PRICE_FILE = DATA_DIR / "price_settings.csv"

PAGE_OPTIONS = ["销售录入", "库存管理", "费用与成本", "盈利分析与洞察"]
PROTECTED_PAGES = {"费用与成本", "盈利分析与洞察"}

FIELDS = [
    "record_id",
    "created_at",
    "city",
    "activity_date",
    "location",
    "product_sku",
    "cup_qty",
    "bottle_qty",
    "tasting_qty",
    "note",
]

INVENTORY_FIELDS = [
    "movement_id",
    "created_at",
    "city",
    "activity_date",
    "location",
    "item_category",
    "item_name",
    "unit",
    "flow_type",
    "quantity",
    "warehouse_delta",
    "site_delta",
    "consumed_qty",
    "returned_qty",
    "note",
]

COST_FIELDS = [
    "cost_id",
    "created_at",
    "city",
    "activity_date",
    "location",
    "cost_type",
    "cost_subtype",
    "product_sku",
    "unit_price",
    "quantity",
    "amount",
    "note",
]

PRICE_FIELDS = [
    "product_sku",
    "cup_price",
    "bottle_price",
    "updated_at",
]

CITY_OPTIONS = [
    "上海",
    "杭州",
    "南京",
    "苏州",
    "广州",
    "深圳",
    "北京",
    "成都",
    "武汉",
    "长沙",
    "其他",
]

DEFAULT_SKUS = [
    "OKKISS 白桃起泡酒 275ml",
    "OKKISS 青提起泡酒 275ml",
    "OKKISS 草莓起泡酒 275ml",
    "OKKISS 玫瑰起泡酒 275ml",
]

MATERIAL_ITEMS = [
    "陈列物料",
    "布置物料",
    "冰块",
    "水",
    "纸巾",
    "赠品物料",
]

UNIT_OPTIONS = ["瓶", "件", "袋", "包", "箱", "套", "个"]

FLOW_TYPES = [
    "城市仓库补货/期初",
    "城市仓库发货到现场",
    "现场实际消耗",
    "未卖完/未使用退回仓库",
    "库存盘点调整",
]

WAREHOUSE_AREA = "城市仓库"
SITE_AREA = "活动现场"

COST_TYPES = [
    "产品成本",
    "物料采购费",
    "运费",
    "其他杂费",
]

FREIGHT_SUBTYPES = [
    "城市入仓费",
    "仓库到现场运费",
    "剩余货物返程运费",
]

OTHER_COST_SUBTYPES = [
    "现场搭建费",
    "临时人工费",
    "场地费",
    "其他杂费",
]


def init_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        with DATA_FILE.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDS)
            writer.writeheader()
    if not INVENTORY_FILE.exists():
        with INVENTORY_FILE.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=INVENTORY_FIELDS)
            writer.writeheader()
    if not COST_FILE.exists():
        with COST_FILE.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=COST_FIELDS)
            writer.writeheader()
    if not PRICE_FILE.exists():
        with PRICE_FILE.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=PRICE_FIELDS)
            writer.writeheader()


def load_records() -> pd.DataFrame:
    init_storage()
    df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
    if df.empty:
        return pd.DataFrame(columns=FIELDS)

    for col in ["cup_qty", "bottle_qty", "tasting_qty"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["activity_date"] = df["activity_date"].astype(str)
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    return df


def load_inventory_movements() -> pd.DataFrame:
    init_storage()
    df = pd.read_csv(INVENTORY_FILE, encoding="utf-8-sig")
    if df.empty:
        return pd.DataFrame(columns=INVENTORY_FIELDS)

    for col in INVENTORY_FIELDS:
        if col not in df.columns:
            df[col] = ""

    numeric_cols = [
        "quantity",
        "warehouse_delta",
        "site_delta",
        "consumed_qty",
        "returned_qty",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["activity_date"] = df["activity_date"].astype(str)
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    return df[INVENTORY_FIELDS]


def load_cost_records() -> pd.DataFrame:
    init_storage()
    df = pd.read_csv(COST_FILE, encoding="utf-8-sig")
    if df.empty:
        return pd.DataFrame(columns=COST_FIELDS)

    for col in COST_FIELDS:
        if col not in df.columns:
            df[col] = ""

    for col in ["unit_price", "quantity", "amount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["activity_date"] = df["activity_date"].astype(str)
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    return df[COST_FIELDS]


def load_price_settings() -> pd.DataFrame:
    init_storage()
    df = pd.read_csv(PRICE_FILE, encoding="utf-8-sig")
    if df.empty:
        return pd.DataFrame(columns=PRICE_FIELDS)

    for col in PRICE_FIELDS:
        if col not in df.columns:
            df[col] = ""
    for col in ["cup_price", "bottle_price"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")
    return df[PRICE_FIELDS]


def upsert_price_setting(product_sku: str, cup_price: float, bottle_price: float) -> None:
    init_storage()
    df = load_price_settings()
    sku = product_sku.strip()
    new_row = {
        "product_sku": sku,
        "cup_price": float(cup_price),
        "bottle_price": float(bottle_price),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    if df.empty:
        df = pd.DataFrame([new_row], columns=PRICE_FIELDS)
    elif sku not in df["product_sku"].astype(str).tolist():
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        mask = df["product_sku"].astype(str) == sku
        for key, value in new_row.items():
            df.loc[mask, key] = value
    df.to_csv(PRICE_FILE, index=False, encoding="utf-8-sig")


def append_cost_record(
    *,
    city: str,
    activity_date: date,
    location: str,
    cost_type: str,
    cost_subtype: str,
    product_sku: str,
    unit_price: float,
    quantity: float,
    note: str = "",
) -> None:
    init_storage()
    amount = float(unit_price) * float(quantity)
    row = {
        "cost_id": uuid4().hex,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "city": city.strip(),
        "activity_date": activity_date.isoformat(),
        "location": location.strip(),
        "cost_type": cost_type.strip(),
        "cost_subtype": cost_subtype.strip(),
        "product_sku": product_sku.strip(),
        "unit_price": round(float(unit_price), 2),
        "quantity": round(float(quantity), 4),
        "amount": round(amount, 2),
        "note": note.strip(),
    }
    with COST_FILE.open("a", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=COST_FIELDS)
        writer.writerow(row)


def get_inventory_effect(
    flow_type: str, quantity: int, adjustment_area: str = WAREHOUSE_AREA
) -> tuple[int, int, int, int]:
    if flow_type == "城市仓库补货/期初":
        return quantity, 0, 0, 0
    if flow_type == "城市仓库发货到现场":
        return -quantity, quantity, 0, 0
    if flow_type == "现场实际消耗":
        return 0, -quantity, quantity, 0
    if flow_type == "未卖完/未使用退回仓库":
        return quantity, -quantity, 0, quantity
    if flow_type == "库存盘点调整":
        if adjustment_area == SITE_AREA:
            return 0, quantity, 0, 0
        return quantity, 0, 0, 0
    return 0, 0, 0, 0


def append_inventory_movement(
    *,
    city: str,
    activity_date: date,
    location: str,
    item_category: str,
    item_name: str,
    unit: str,
    flow_type: str,
    quantity: int,
    adjustment_area: str = WAREHOUSE_AREA,
    note: str = "",
) -> None:
    init_storage()
    warehouse_delta, site_delta, consumed_qty, returned_qty = get_inventory_effect(
        flow_type, int(quantity), adjustment_area
    )
    row = {
        "movement_id": uuid4().hex,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "city": city.strip(),
        "activity_date": activity_date.isoformat(),
        "location": location.strip(),
        "item_category": item_category.strip(),
        "item_name": item_name.strip(),
        "unit": unit.strip(),
        "flow_type": flow_type.strip(),
        "quantity": int(quantity),
        "warehouse_delta": warehouse_delta,
        "site_delta": site_delta,
        "consumed_qty": consumed_qty,
        "returned_qty": returned_qty,
        "note": note.strip(),
    }
    with INVENTORY_FILE.open("a", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=INVENTORY_FIELDS)
        writer.writerow(row)


def append_record(
    *,
    city: str,
    activity_date: date,
    location: str,
    product_sku: str,
    cup_qty: int,
    bottle_qty: int,
    tasting_qty: int,
    note: str = "",
) -> None:
    init_storage()
    row = {
        "record_id": uuid4().hex,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "city": city.strip(),
        "activity_date": activity_date.isoformat(),
        "location": location.strip(),
        "product_sku": product_sku.strip(),
        "cup_qty": int(cup_qty),
        "bottle_qty": int(bottle_qty),
        "tasting_qty": int(tasting_qty),
        "note": note.strip(),
    }
    with DATA_FILE.open("a", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writerow(row)


def current_event_records(
    df: pd.DataFrame, city: str, activity_date: date, location: str
) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    mask = (
        (df["city"] == city)
        & (df["activity_date"] == activity_date.isoformat())
        & (df["location"] == location)
    )
    return df.loc[mask].copy()


def current_event_cost_records(
    df: pd.DataFrame, city: str, activity_date: date, location: str
) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    mask = (
        (df["city"] == city)
        & (df["activity_date"] == activity_date.isoformat())
        & (df["location"] == location)
    )
    return df.loc[mask].copy()


def build_product_options(df: pd.DataFrame) -> list[str]:
    saved_skus: list[str] = []
    if not df.empty and "product_sku" in df:
        saved_skus = sorted(
            sku for sku in df["product_sku"].dropna().astype(str).unique() if sku.strip()
        )

    merged = list(dict.fromkeys(DEFAULT_SKUS + saved_skus))
    return merged + ["新增SKU"]


def build_inventory_item_options(df: pd.DataFrame, item_category: str) -> list[str]:
    base_items = DEFAULT_SKUS if item_category == "起泡酒产品库存" else MATERIAL_ITEMS
    saved_items: list[str] = []
    if not df.empty:
        saved_items = sorted(
            item
            for item in df.loc[df["item_category"] == item_category, "item_name"]
            .dropna()
            .astype(str)
            .unique()
            if item.strip()
        )

    merged = list(dict.fromkeys(base_items + saved_items))
    return merged + ["新增库存项目"]


def build_location_options(df: pd.DataFrame, city: str) -> list[str]:
    saved_locations: list[str] = []
    if not df.empty and city:
        city_records = df.loc[df["city"] == city]
        saved_locations = sorted(
            loc
            for loc in city_records["location"].dropna().astype(str).unique()
            if loc.strip()
        )

    return saved_locations + ["新增活动地点"]


def build_inventory_location_options(
    sales_df: pd.DataFrame, inventory_df: pd.DataFrame, city: str
) -> list[str]:
    locations: list[str] = []
    if not sales_df.empty and city:
        locations.extend(
            loc
            for loc in sales_df.loc[sales_df["city"] == city, "location"]
            .dropna()
            .astype(str)
            .unique()
            if loc.strip()
        )
    if not inventory_df.empty and city:
        locations.extend(
            loc
            for loc in inventory_df.loc[inventory_df["city"] == city, "location"]
            .dropna()
            .astype(str)
            .unique()
            if loc.strip() and loc != WAREHOUSE_AREA
        )

    return sorted(set(locations)) + ["新增活动地点"]


def build_cost_location_options(
    sales_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    cost_df: pd.DataFrame,
    city: str,
) -> list[str]:
    locations: list[str] = []
    if not sales_df.empty and city:
        locations.extend(
            loc
            for loc in sales_df.loc[sales_df["city"] == city, "location"]
            .dropna()
            .astype(str)
            .unique()
            if loc.strip()
        )
    if not inventory_df.empty and city:
        locations.extend(
            loc
            for loc in inventory_df.loc[inventory_df["city"] == city, "location"]
            .dropna()
            .astype(str)
            .unique()
            if loc.strip() and loc != WAREHOUSE_AREA
        )
    if not cost_df.empty and city:
        locations.extend(
            loc
            for loc in cost_df.loc[cost_df["city"] == city, "location"]
            .dropna()
            .astype(str)
            .unique()
            if loc.strip()
        )

    return sorted(set(locations)) + ["新增活动地点"]


def build_cost_sku_options(
    sales_df: pd.DataFrame, cost_df: pd.DataFrame, price_df: pd.DataFrame
) -> list[str]:
    skus: list[str] = DEFAULT_SKUS.copy()
    if not sales_df.empty:
        skus.extend(
            sku
            for sku in sales_df["product_sku"].dropna().astype(str).unique()
            if sku.strip()
        )
    if not cost_df.empty:
        skus.extend(
            sku
            for sku in cost_df["product_sku"].dropna().astype(str).unique()
            if sku.strip()
        )
    if not price_df.empty:
        skus.extend(
            sku
            for sku in price_df["product_sku"].dropna().astype(str).unique()
            if sku.strip()
        )
    return list(dict.fromkeys(skus)) + ["新增SKU"]


def default_unit(item_category: str, item_name: str) -> str:
    if item_category == "起泡酒产品库存":
        return "瓶"
    if item_name == "冰块":
        return "袋"
    if item_name == "水":
        return "瓶"
    if item_name == "纸巾":
        return "包"
    if item_name == "布置物料":
        return "套"
    return "件"


def inventory_threshold(item_category: str, item_name: str) -> int:
    if item_category == "起泡酒产品库存":
        return 24
    if item_name == "冰块":
        return 10
    if item_name == "水":
        return 24
    if item_name == "纸巾":
        return 10
    return 20


def inventory_status(current_qty: int, threshold: int) -> str:
    if current_qty < 0:
        return "库存为负，请核对"
    if current_qty <= threshold:
        return "低库存预警"
    return "正常"


def summarize_city_inventory(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "城市",
        "库存类型",
        "库存项目",
        "单位",
        "城市仓当前库存",
        "预警阈值",
        "状态",
    ]
    if df.empty:
        return pd.DataFrame(columns=columns)

    summary = (
        df.groupby(["city", "item_category", "item_name", "unit"], as_index=False)
        .agg(current_qty=("warehouse_delta", "sum"))
        .rename(
            columns={
                "city": "城市",
                "item_category": "库存类型",
                "item_name": "库存项目",
                "unit": "单位",
                "current_qty": "城市仓当前库存",
            }
        )
    )
    summary["预警阈值"] = summary.apply(
        lambda row: inventory_threshold(str(row["库存类型"]), str(row["库存项目"])),
        axis=1,
    )
    summary["状态"] = summary.apply(
        lambda row: inventory_status(int(row["城市仓当前库存"]), int(row["预警阈值"])),
        axis=1,
    )
    return summary.sort_values(["城市", "状态", "库存类型", "库存项目"]).reset_index(
        drop=True
    )


def summarize_event_inventory(
    df: pd.DataFrame, city: str, activity_date: date, location: str
) -> pd.DataFrame:
    columns = [
        "库存类型",
        "库存项目",
        "单位",
        "发货到现场",
        "现场消耗",
        "退回仓库",
        "当前现场库存",
        "损耗率/消耗率",
        "状态",
    ]
    if df.empty or not city or not location:
        return pd.DataFrame(columns=columns)

    event_df = df.loc[
        (df["city"] == city)
        & (df["activity_date"] == activity_date.isoformat())
        & (df["location"] == location)
    ].copy()
    if event_df.empty:
        return pd.DataFrame(columns=columns)

    event_df["shipped_qty"] = event_df["quantity"].where(
        event_df["flow_type"] == "城市仓库发货到现场", 0
    )
    summary = (
        event_df.groupby(["item_category", "item_name", "unit"], as_index=False)
        .agg(
            shipped_qty=("shipped_qty", "sum"),
            consumed_qty=("consumed_qty", "sum"),
            returned_qty=("returned_qty", "sum"),
            current_qty=("site_delta", "sum"),
        )
        .rename(
            columns={
                "item_category": "库存类型",
                "item_name": "库存项目",
                "unit": "单位",
                "shipped_qty": "发货到现场",
                "consumed_qty": "现场消耗",
                "returned_qty": "退回仓库",
                "current_qty": "当前现场库存",
            }
        )
    )
    summary["损耗率/消耗率"] = summary.apply(
        lambda row: (
            f"{int(row['现场消耗']) / int(row['发货到现场']):.1%}"
            if int(row["发货到现场"]) > 0
            else "0.0%"
        ),
        axis=1,
    )
    summary["状态"] = summary["当前现场库存"].apply(
        lambda qty: "现场库存为负，请核对" if int(qty) < 0 else "正常"
    )
    return summary.sort_values(["状态", "库存类型", "库存项目"]).reset_index(drop=True)


def summarize_material_loss(event_summary: pd.DataFrame) -> pd.DataFrame:
    if event_summary.empty:
        return event_summary.copy()
    return event_summary.loc[event_summary["库存类型"] == "物料库存"].reset_index(drop=True)


def summarize_records(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[
                "排名",
                "产品名称/SKU",
                "杯卖数量",
                "瓶卖数量",
                "试饮数量",
                "销售总量",
                "销售占比",
                "录入次数",
            ]
        )

    summary = (
        df.groupby("product_sku", as_index=False)
        .agg(
            cup_qty=("cup_qty", "sum"),
            bottle_qty=("bottle_qty", "sum"),
            tasting_qty=("tasting_qty", "sum"),
            entries=("record_id", "count"),
        )
        .rename(columns={"product_sku": "产品名称/SKU"})
    )
    summary["销售总量"] = summary["cup_qty"] + summary["bottle_qty"]
    total_sales = int(summary["销售总量"].sum())
    summary["销售占比"] = summary["销售总量"].apply(
        lambda value: f"{value / total_sales:.1%}" if total_sales else "0.0%"
    )
    summary = summary.sort_values(
        by=["销售总量", "bottle_qty", "cup_qty", "tasting_qty"],
        ascending=False,
    ).reset_index(drop=True)
    summary.insert(0, "排名", summary.index + 1)
    return summary.rename(
        columns={
            "cup_qty": "杯卖数量",
            "bottle_qty": "瓶卖数量",
            "tasting_qty": "试饮数量",
            "entries": "录入次数",
        }
    )


def get_price_map(price_df: pd.DataFrame) -> dict[str, dict[str, float]]:
    if price_df.empty:
        return {}
    clean_df = price_df.dropna(subset=["product_sku"]).copy()
    clean_df["product_sku"] = clean_df["product_sku"].astype(str)
    clean_df = clean_df.loc[clean_df["product_sku"].str.strip() != ""]
    clean_df = clean_df.drop_duplicates(subset=["product_sku"], keep="last")
    return {
        str(row["product_sku"]): {
            "cup_price": float(row["cup_price"]),
            "bottle_price": float(row["bottle_price"]),
        }
        for _, row in clean_df.iterrows()
    }


def summarize_event_sales_for_cost(
    df: pd.DataFrame, price_df: pd.DataFrame
) -> pd.DataFrame:
    columns = [
        "产品名称/SKU",
        "杯卖数量",
        "瓶卖数量",
        "试饮数量",
        "销售总量",
        "杯装售价",
        "瓶装售价",
        "杯装收入",
        "瓶装收入",
        "销售收入",
    ]
    if df.empty:
        return pd.DataFrame(columns=columns)

    price_map = get_price_map(price_df)
    summary = (
        df.groupby("product_sku", as_index=False)
        .agg(
            cup_qty=("cup_qty", "sum"),
            bottle_qty=("bottle_qty", "sum"),
            tasting_qty=("tasting_qty", "sum"),
        )
        .rename(
            columns={
                "product_sku": "产品名称/SKU",
                "cup_qty": "杯卖数量",
                "bottle_qty": "瓶卖数量",
                "tasting_qty": "试饮数量",
            }
        )
    )
    summary["销售总量"] = summary["杯卖数量"] + summary["瓶卖数量"]
    summary["杯装售价"] = summary["产品名称/SKU"].apply(
        lambda sku: price_map.get(str(sku), {}).get("cup_price", 0.0)
    )
    summary["瓶装售价"] = summary["产品名称/SKU"].apply(
        lambda sku: price_map.get(str(sku), {}).get("bottle_price", 0.0)
    )
    summary["杯装收入"] = summary["杯卖数量"] * summary["杯装售价"]
    summary["瓶装收入"] = summary["瓶卖数量"] * summary["瓶装售价"]
    summary["销售收入"] = summary["杯装收入"] + summary["瓶装收入"]

    money_cols = ["杯装售价", "瓶装售价", "杯装收入", "瓶装收入", "销售收入"]
    for col in money_cols:
        summary[col] = summary[col].round(2)
    return summary[columns].sort_values("销售收入", ascending=False).reset_index(drop=True)


def summarize_cost_by_type(cost_df: pd.DataFrame) -> pd.DataFrame:
    columns = ["费用类型", "费用明细", "费用金额"]
    if cost_df.empty:
        return pd.DataFrame(columns=columns)

    summary = (
        cost_df.groupby(["cost_type", "cost_subtype"], as_index=False)
        .agg(amount=("amount", "sum"))
        .rename(
            columns={
                "cost_type": "费用类型",
                "cost_subtype": "费用明细",
                "amount": "费用金额",
            }
        )
    )
    summary["费用金额"] = summary["费用金额"].round(2)
    return summary.sort_values("费用金额", ascending=False).reset_index(drop=True)


def build_product_cost_summary(
    sales_summary: pd.DataFrame, cost_df: pd.DataFrame
) -> pd.DataFrame:
    columns = [
        "产品名称/SKU",
        "杯卖数量",
        "瓶卖数量",
        "销售总量",
        "销售收入",
        "产品直接成本",
        "分摊费用",
        "单品总成本",
        "杯装单位成本",
        "瓶装单位成本",
        "单品毛利",
        "单品毛利率",
    ]

    if sales_summary.empty and cost_df.empty:
        return pd.DataFrame(columns=columns)

    product_cost_df = cost_df.loc[
        (cost_df["cost_type"] == "产品成本")
        & (cost_df["product_sku"].fillna("").astype(str).str.strip() != "")
    ]
    direct_cost = (
        product_cost_df.groupby("product_sku", as_index=False)
        .agg(direct_cost=("amount", "sum"))
        .rename(columns={"product_sku": "产品名称/SKU"})
    )

    sku_names = set(direct_cost["产品名称/SKU"].astype(str).tolist())
    if not sales_summary.empty:
        sku_names.update(sales_summary["产品名称/SKU"].astype(str).tolist())

    base = pd.DataFrame({"产品名称/SKU": sorted(sku_names)})
    if not sales_summary.empty:
        base = base.merge(sales_summary, on="产品名称/SKU", how="left")
    else:
        for col in [
            "杯卖数量",
            "瓶卖数量",
            "试饮数量",
            "销售总量",
            "杯装售价",
            "瓶装售价",
            "杯装收入",
            "瓶装收入",
            "销售收入",
        ]:
            base[col] = 0

    base = base.merge(direct_cost, on="产品名称/SKU", how="left")
    numeric_cols = [
        "杯卖数量",
        "瓶卖数量",
        "销售总量",
        "杯装收入",
        "瓶装收入",
        "销售收入",
        "direct_cost",
    ]
    for col in numeric_cols:
        if col not in base.columns:
            base[col] = 0
        base[col] = pd.to_numeric(base[col], errors="coerce").fillna(0.0)

    total_cost = float(cost_df["amount"].sum()) if not cost_df.empty else 0.0
    direct_cost_total = float(base["direct_cost"].sum())
    shared_cost = max(total_cost - direct_cost_total, 0.0)
    total_revenue = float(base["销售收入"].sum())
    total_sales_qty = float(base["销售总量"].sum())

    def allocation_share(row: pd.Series) -> float:
        if total_revenue > 0:
            return float(row["销售收入"]) / total_revenue
        if total_sales_qty > 0:
            return float(row["销售总量"]) / total_sales_qty
        return 0.0

    base["产品直接成本"] = base["direct_cost"]
    base["分摊费用"] = base.apply(lambda row: shared_cost * allocation_share(row), axis=1)
    base["单品总成本"] = base["产品直接成本"] + base["分摊费用"]

    def split_unit_cost(row: pd.Series, target: str) -> float:
        cup_qty = float(row["杯卖数量"])
        bottle_qty = float(row["瓶卖数量"])
        sku_cost = float(row["单品总成本"])
        cup_revenue = float(row["杯装收入"])
        bottle_revenue = float(row["瓶装收入"])
        revenue_total = cup_revenue + bottle_revenue
        qty_total = cup_qty + bottle_qty

        if target == "cup":
            if cup_qty <= 0:
                return 0.0
            share = cup_revenue / revenue_total if revenue_total > 0 else cup_qty / qty_total
            return sku_cost * share / cup_qty

        if bottle_qty <= 0:
            return 0.0
        share = (
            bottle_revenue / revenue_total
            if revenue_total > 0
            else bottle_qty / qty_total
        )
        return sku_cost * share / bottle_qty

    base["杯装单位成本"] = base.apply(lambda row: split_unit_cost(row, "cup"), axis=1)
    base["瓶装单位成本"] = base.apply(lambda row: split_unit_cost(row, "bottle"), axis=1)
    base["单品毛利"] = base["销售收入"] - base["单品总成本"]
    base["单品毛利率"] = base.apply(
        lambda row: (
            f"{float(row['单品毛利']) / float(row['销售收入']):.1%}"
            if float(row["销售收入"]) > 0
            else "0.0%"
        ),
        axis=1,
    )

    money_cols = [
        "销售收入",
        "产品直接成本",
        "分摊费用",
        "单品总成本",
        "杯装单位成本",
        "瓶装单位成本",
        "单品毛利",
    ]
    for col in money_cols:
        base[col] = pd.to_numeric(base[col], errors="coerce").fillna(0.0).round(2)

    return base[columns].sort_values("销售收入", ascending=False).reset_index(drop=True)


def calculate_cost_metrics(
    sales_summary: pd.DataFrame, cost_df: pd.DataFrame
) -> dict[str, float]:
    total_revenue = (
        float(sales_summary["销售收入"].sum()) if not sales_summary.empty else 0.0
    )
    total_cost = float(cost_df["amount"].sum()) if not cost_df.empty else 0.0
    gross_profit = total_revenue - total_cost
    gross_margin = gross_profit / total_revenue if total_revenue > 0 else 0.0
    roi = gross_profit / total_cost if total_cost > 0 else 0.0
    input_output = total_revenue / total_cost if total_cost > 0 else 0.0
    return {
        "total_revenue": round(total_revenue, 2),
        "total_cost": round(total_cost, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_margin": gross_margin,
        "roi": roi,
        "input_output": input_output,
    }


def build_cost_alerts(
    metrics: dict[str, float], sales_summary: pd.DataFrame, cost_df: pd.DataFrame
) -> list[str]:
    alerts: list[str] = []
    if sales_summary.empty:
        alerts.append("当前场次暂无销售记录，费用可先录入，但毛利率和ROI无法形成有效判断。")
    elif float(metrics["total_revenue"]) <= 0:
        alerts.append("当前场次已有销量但售价未录入，需先设置杯装/瓶装售价后再看毛利率和ROI。")

    if cost_df.empty:
        alerts.append("当前场次暂无费用明细，单场总成本暂为 0。")
    if float(metrics["total_cost"]) > 0 and float(metrics["total_revenue"]) > 0:
        if metrics["gross_margin"] < 0:
            alerts.append("当前场次毛利为负，建议复盘产品成本、运费和现场人工费用。")
        if metrics["roi"] < 0.2:
            alerts.append("当前场次 ROI 低于 20%，需要关注费用投放是否过高。")

    missing_cost_skus = []
    if not sales_summary.empty and not cost_df.empty:
        product_cost_skus = set(
            cost_df.loc[cost_df["cost_type"] == "产品成本", "product_sku"]
            .dropna()
            .astype(str)
            .tolist()
        )
        missing_cost_skus = [
            sku
            for sku in sales_summary["产品名称/SKU"].astype(str).tolist()
            if sku not in product_cost_skus
        ]
    if missing_cost_skus:
        alerts.append(
            f"{'、'.join(missing_cost_skus[:3])} 有销量但未录入产品成本，单品成本会偏低。"
        )

    return alerts or ["当前费用和销售数据暂无明显异常。"]


def build_cost_excel(
    *,
    cost_df: pd.DataFrame,
    sales_summary: pd.DataFrame,
    cost_summary: pd.DataFrame,
    product_cost_summary: pd.DataFrame,
    price_df: pd.DataFrame,
    metrics: dict[str, float],
) -> bytes:
    output = BytesIO()
    metrics_df = pd.DataFrame(
        [
            {
                "销售收入": metrics["total_revenue"],
                "单场活动总成本": metrics["total_cost"],
                "单场毛利": metrics["gross_profit"],
                "单场毛利率": f"{metrics['gross_margin']:.1%}",
                "投入产出比": round(metrics["input_output"], 2),
                "ROI": f"{metrics['roi']:.1%}",
            }
        ]
    )
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        metrics_df.to_excel(writer, sheet_name="单场成本汇总", index=False)
        cost_df.to_excel(writer, sheet_name="费用明细", index=False)
        sales_summary.to_excel(writer, sheet_name="销售收入关联", index=False)
        product_cost_summary.to_excel(writer, sheet_name="单品成本核算", index=False)
        cost_summary.to_excel(writer, sheet_name="费用分类汇总", index=False)
        price_df.to_excel(writer, sheet_name="售价设置", index=False)
    return output.getvalue()


def infer_activity_format(location: str) -> str:
    text = str(location).lower()
    if any(key in text for key in ["商场", "商圈", "银泰", "万达", "购物", "mall"]):
        return "商场/商圈"
    if any(key in text for key in ["超市", "便利", "盒马", "山姆", "会员店"]):
        return "商超/零售"
    if any(key in text for key in ["酒吧", "餐", "咖啡", "bistro", "bar"]):
        return "餐饮/酒吧"
    if any(key in text for key in ["市集", "集市", "展", "节", "快闪"]):
        return "市集/展会/快闪"
    if any(key in text for key in ["社区", "小区", "园区", "写字楼", "办公"]):
        return "社区/园区"
    return "其他活动"


def collect_filter_options(
    sales_df: pd.DataFrame, cost_df: pd.DataFrame, inventory_df: pd.DataFrame
) -> tuple[list[str], list[str], date, date]:
    cities: list[str] = []
    skus: list[str] = DEFAULT_SKUS.copy()
    date_values: list[pd.Timestamp] = []

    for df in [sales_df, cost_df, inventory_df]:
        if not df.empty and "city" in df:
            cities.extend(
                item for item in df["city"].dropna().astype(str).unique() if item.strip()
            )
        if not df.empty and "activity_date" in df:
            parsed_dates = pd.to_datetime(df["activity_date"], errors="coerce").dropna()
            date_values.extend(parsed_dates.tolist())

    if not sales_df.empty:
        skus.extend(
            sku
            for sku in sales_df["product_sku"].dropna().astype(str).unique()
            if sku.strip()
        )
    if not cost_df.empty:
        skus.extend(
            sku
            for sku in cost_df["product_sku"].dropna().astype(str).unique()
            if sku.strip()
        )
    if not inventory_df.empty:
        skus.extend(
            sku
            for sku in inventory_df.loc[
                inventory_df["item_category"] == "起泡酒产品库存", "item_name"
            ]
            .dropna()
            .astype(str)
            .unique()
            if sku.strip()
        )

    today = date.today()
    if date_values:
        start_date = min(date_values).date()
        end_date = max(date_values).date()
    else:
        start_date = today
        end_date = today

    return sorted(set(cities)), list(dict.fromkeys(skus)), start_date, end_date


def filter_by_analytics_scope(
    df: pd.DataFrame,
    *,
    selected_cities: list[str],
    selected_skus: list[str],
    start_date: date,
    end_date: date,
    sku_column: str | None = None,
    keep_shared_cost: bool = False,
) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    filtered = df.copy()
    if selected_cities and "city" in filtered:
        filtered = filtered.loc[filtered["city"].astype(str).isin(selected_cities)]

    if "activity_date" in filtered:
        parsed_dates = pd.to_datetime(filtered["activity_date"], errors="coerce")
        filtered = filtered.loc[
            (parsed_dates.dt.date >= start_date) & (parsed_dates.dt.date <= end_date)
        ]

    if sku_column and selected_skus and sku_column in filtered:
        sku_series = filtered[sku_column].fillna("").astype(str)
        if keep_shared_cost:
            filtered = filtered.loc[(sku_series == "") | sku_series.isin(selected_skus)]
        else:
            filtered = filtered.loc[sku_series.isin(selected_skus)]

    return filtered.copy()


def build_event_profit_summary(
    sales_df: pd.DataFrame, cost_df: pd.DataFrame, price_df: pd.DataFrame
) -> pd.DataFrame:
    columns = [
        "城市",
        "活动日期",
        "活动地点",
        "活动形式",
        "杯卖数量",
        "瓶卖数量",
        "试饮数量",
        "销售总量",
        "销售收入",
        "单场活动总成本",
        "单场毛利",
        "单场毛利率",
        "投入产出比",
        "ROI",
        "试饮转化率",
        "杯卖占比",
        "瓶卖占比",
        "活动标签",
    ]
    if sales_df.empty and cost_df.empty:
        return pd.DataFrame(columns=columns)

    price_map = get_price_map(price_df)
    sales_group = pd.DataFrame(columns=["city", "activity_date", "location"])
    if not sales_df.empty:
        sales_work = sales_df.copy()
        sales_work["cup_price"] = sales_work["product_sku"].apply(
            lambda sku: price_map.get(str(sku), {}).get("cup_price", 0.0)
        )
        sales_work["bottle_price"] = sales_work["product_sku"].apply(
            lambda sku: price_map.get(str(sku), {}).get("bottle_price", 0.0)
        )
        sales_work["revenue"] = (
            sales_work["cup_qty"] * sales_work["cup_price"]
            + sales_work["bottle_qty"] * sales_work["bottle_price"]
        )
        sales_work["sales_qty"] = sales_work["cup_qty"] + sales_work["bottle_qty"]
        sales_group = (
            sales_work.groupby(["city", "activity_date", "location"], as_index=False)
            .agg(
                cup_qty=("cup_qty", "sum"),
                bottle_qty=("bottle_qty", "sum"),
                tasting_qty=("tasting_qty", "sum"),
                sales_qty=("sales_qty", "sum"),
                revenue=("revenue", "sum"),
            )
        )

    cost_group = pd.DataFrame(columns=["city", "activity_date", "location"])
    if not cost_df.empty:
        cost_group = (
            cost_df.groupby(["city", "activity_date", "location"], as_index=False)
            .agg(total_cost=("amount", "sum"))
        )

    base = pd.concat(
        [
            sales_group[["city", "activity_date", "location"]],
            cost_group[["city", "activity_date", "location"]],
        ],
        ignore_index=True,
    ).drop_duplicates()
    if base.empty:
        return pd.DataFrame(columns=columns)

    base = base.merge(sales_group, on=["city", "activity_date", "location"], how="left")
    base = base.merge(cost_group, on=["city", "activity_date", "location"], how="left")

    for col in [
        "cup_qty",
        "bottle_qty",
        "tasting_qty",
        "sales_qty",
        "revenue",
        "total_cost",
    ]:
        base[col] = pd.to_numeric(base[col], errors="coerce").fillna(0.0)

    base["gross_profit"] = base["revenue"] - base["total_cost"]
    base["gross_margin_value"] = base.apply(
        lambda row: row["gross_profit"] / row["revenue"]
        if row["revenue"] > 0
        else 0.0,
        axis=1,
    )
    base["roi_value"] = base.apply(
        lambda row: row["gross_profit"] / row["total_cost"]
        if row["total_cost"] > 0
        else 0.0,
        axis=1,
    )
    base["input_output_value"] = base.apply(
        lambda row: row["revenue"] / row["total_cost"]
        if row["total_cost"] > 0
        else 0.0,
        axis=1,
    )
    base["conversion_value"] = base.apply(
        lambda row: row["sales_qty"] / row["tasting_qty"]
        if row["tasting_qty"] > 0
        else 0.0,
        axis=1,
    )
    base["cup_share_value"] = base.apply(
        lambda row: row["cup_qty"] / row["sales_qty"]
        if row["sales_qty"] > 0
        else 0.0,
        axis=1,
    )
    base["bottle_share_value"] = base.apply(
        lambda row: row["bottle_qty"] / row["sales_qty"]
        if row["sales_qty"] > 0
        else 0.0,
        axis=1,
    )

    base["activity_form"] = base["location"].apply(infer_activity_format)
    base["activity_label"] = (
        base["city"].astype(str)
        + " | "
        + base["activity_date"].astype(str)
        + " | "
        + base["location"].astype(str)
    )

    result = base.rename(
        columns={
            "city": "城市",
            "activity_date": "活动日期",
            "location": "活动地点",
            "activity_form": "活动形式",
            "cup_qty": "杯卖数量",
            "bottle_qty": "瓶卖数量",
            "tasting_qty": "试饮数量",
            "sales_qty": "销售总量",
            "revenue": "销售收入",
            "total_cost": "单场活动总成本",
            "gross_profit": "单场毛利",
            "gross_margin_value": "单场毛利率",
            "input_output_value": "投入产出比",
            "roi_value": "ROI",
            "conversion_value": "试饮转化率",
            "cup_share_value": "杯卖占比",
            "bottle_share_value": "瓶卖占比",
            "activity_label": "活动标签",
        }
    )

    for col in ["销售收入", "单场活动总成本", "单场毛利"]:
        result[col] = result[col].round(2)
    return result[columns].sort_values("单场毛利", ascending=False).reset_index(drop=True)


def summarize_dimension_profit(event_summary: pd.DataFrame, dimension: str) -> pd.DataFrame:
    columns = [
        dimension,
        "活动场次",
        "销售收入",
        "总成本",
        "总毛利",
        "平均单场毛利",
        "毛利率",
        "ROI",
        "试饮转化率",
        "销售总量",
    ]
    if event_summary.empty or dimension not in event_summary:
        return pd.DataFrame(columns=columns)

    summary = (
        event_summary.groupby(dimension, as_index=False)
        .agg(
            活动场次=("活动标签", "count"),
            销售收入=("销售收入", "sum"),
            总成本=("单场活动总成本", "sum"),
            总毛利=("单场毛利", "sum"),
            销售总量=("销售总量", "sum"),
            试饮数量=("试饮数量", "sum"),
        )
    )
    summary["平均单场毛利"] = summary["总毛利"] / summary["活动场次"].where(
        summary["活动场次"] != 0, 1
    )
    summary["毛利率"] = summary.apply(
        lambda row: row["总毛利"] / row["销售收入"]
        if row["销售收入"] > 0
        else 0.0,
        axis=1,
    )
    summary["ROI"] = summary.apply(
        lambda row: row["总毛利"] / row["总成本"] if row["总成本"] > 0 else 0.0,
        axis=1,
    )
    summary["试饮转化率"] = summary.apply(
        lambda row: row["销售总量"] / row["试饮数量"]
        if row["试饮数量"] > 0
        else 0.0,
        axis=1,
    )
    for col in ["销售收入", "总成本", "总毛利", "平均单场毛利"]:
        summary[col] = summary[col].round(2)
    return summary[columns].sort_values("平均单场毛利", ascending=False).reset_index(
        drop=True
    )


def build_sku_insight_summary(
    sales_df: pd.DataFrame,
    cost_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    price_df: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "产品名称/SKU",
        "杯卖数量",
        "瓶卖数量",
        "销售总量",
        "试饮数量",
        "销售收入",
        "单品总成本",
        "单品毛利",
        "单品毛利率",
        "发货到现场",
        "动销率",
        "利润贡献占比",
        "试饮转化率",
    ]
    if sales_df.empty and cost_df.empty:
        return pd.DataFrame(columns=columns)

    sales_summary = summarize_event_sales_for_cost(sales_df, price_df)
    product_cost_summary = build_product_cost_summary(sales_summary, cost_df)
    if product_cost_summary.empty:
        return pd.DataFrame(columns=columns)

    shipment = pd.DataFrame(columns=["产品名称/SKU", "发货到现场"])
    if not inventory_df.empty:
        shipment_df = inventory_df.loc[
            (inventory_df["item_category"] == "起泡酒产品库存")
            & (inventory_df["flow_type"] == "城市仓库发货到现场")
        ]
        if not shipment_df.empty:
            shipment = (
                shipment_df.groupby("item_name", as_index=False)
                .agg(发货到现场=("quantity", "sum"))
                .rename(columns={"item_name": "产品名称/SKU"})
            )

    result = product_cost_summary.merge(shipment, on="产品名称/SKU", how="left")
    if "试饮数量" not in result.columns:
        if not sales_summary.empty and "试饮数量" in sales_summary.columns:
            result = result.merge(
                sales_summary[["产品名称/SKU", "试饮数量"]],
                on="产品名称/SKU",
                how="left",
            )
        else:
            result["试饮数量"] = 0
    result["发货到现场"] = pd.to_numeric(
        result["发货到现场"], errors="coerce"
    ).fillna(0.0)
    result["动销率"] = result.apply(
        lambda row: row["销售总量"] / row["发货到现场"]
        if row["发货到现场"] > 0
        else 0.0,
        axis=1,
    )
    total_profit = float(result["单品毛利"].sum())
    result["利润贡献占比"] = result["单品毛利"].apply(
        lambda profit: profit / total_profit if total_profit > 0 else 0.0
    )
    result["单品毛利率"] = result.apply(
        lambda row: row["单品毛利"] / row["销售收入"]
        if row["销售收入"] > 0
        else 0.0,
        axis=1,
    )
    result["试饮转化率"] = result.apply(
        lambda row: row["销售总量"] / row["试饮数量"]
        if row["试饮数量"] > 0
        else 0.0,
        axis=1,
    )
    for col in ["销售收入", "单品总成本", "单品毛利"]:
        result[col] = pd.to_numeric(result[col], errors="coerce").fillna(0.0).round(2)
    return result[columns].sort_values("单品毛利", ascending=False).reset_index(drop=True)


def build_conversion_summary(sales_df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    columns = [
        dimension,
        "杯卖数量",
        "瓶卖数量",
        "试饮数量",
        "销售总量",
        "杯卖转化率",
        "瓶卖转化率",
        "总转化率",
        "瓶卖占比",
    ]
    if sales_df.empty or dimension not in sales_df:
        return pd.DataFrame(columns=columns)

    summary = (
        sales_df.groupby(dimension, as_index=False)
        .agg(
            杯卖数量=("cup_qty", "sum"),
            瓶卖数量=("bottle_qty", "sum"),
            试饮数量=("tasting_qty", "sum"),
        )
    )
    summary["销售总量"] = summary["杯卖数量"] + summary["瓶卖数量"]
    summary["杯卖转化率"] = summary.apply(
        lambda row: row["杯卖数量"] / row["试饮数量"]
        if row["试饮数量"] > 0
        else 0.0,
        axis=1,
    )
    summary["瓶卖转化率"] = summary.apply(
        lambda row: row["瓶卖数量"] / row["试饮数量"]
        if row["试饮数量"] > 0
        else 0.0,
        axis=1,
    )
    summary["总转化率"] = summary.apply(
        lambda row: row["销售总量"] / row["试饮数量"]
        if row["试饮数量"] > 0
        else 0.0,
        axis=1,
    )
    summary["瓶卖占比"] = summary.apply(
        lambda row: row["瓶卖数量"] / row["销售总量"]
        if row["销售总量"] > 0
        else 0.0,
        axis=1,
    )
    return summary[columns].sort_values("总转化率", ascending=False).reset_index(
        drop=True
    )


def calculate_cost_sales_correlation(event_summary: pd.DataFrame) -> tuple[float, str]:
    if event_summary.empty or len(event_summary) < 2:
        return 0.0, "样本少于 2 场，暂不能判断成本投入与销量的相关性。"
    if event_summary["单场活动总成本"].nunique() < 2 or event_summary["销售总量"].nunique() < 2:
        return 0.0, "成本或销量没有明显变化，暂不能形成有效相关性判断。"

    corr = float(event_summary["单场活动总成本"].corr(event_summary["销售总量"]))
    if corr >= 0.6:
        text = f"相关系数 {corr:.2f}，成本投入增加通常伴随销量提升，可继续验证高投放场景。"
    elif corr <= -0.3:
        text = f"相关系数 {corr:.2f}，成本投入增加没有带来销量提升，需要复盘费用结构。"
    else:
        text = f"相关系数 {corr:.2f}，成本投入与销量关系不强，应优先看点位和SKU组合。"
    return corr, text


def format_percent_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    display_df = df.copy()
    for col in columns:
        if col in display_df:
            display_df[col] = display_df[col].apply(format_percent)
    return display_df


def generate_business_insights(
    event_summary: pd.DataFrame,
    city_summary: pd.DataFrame,
    format_summary: pd.DataFrame,
    sku_summary: pd.DataFrame,
    conversion_summary: pd.DataFrame,
    correlation_text: str,
) -> dict[str, list[str]]:
    insights = {
        "核心结论": [],
        "数据拆解": [],
        "风险提示": [],
        "优化建议": [],
    }

    if event_summary.empty:
        insights["核心结论"].append("当前筛选范围内暂无可分析数据，请先录入销售、售价和费用。")
        insights["风险提示"].append("没有销售收入或费用数据时，无法判断盈利性和ROI。")
        return insights

    total_revenue = float(event_summary["销售收入"].sum())
    total_cost = float(event_summary["单场活动总成本"].sum())
    total_profit = float(event_summary["单场毛利"].sum())
    total_events = len(event_summary)
    margin = total_profit / total_revenue if total_revenue > 0 else 0.0
    roi = total_profit / total_cost if total_cost > 0 else 0.0
    insights["核心结论"].append(
        f"筛选范围共 {total_events} 场活动，销售收入 {format_money(total_revenue)}，总成本 {format_money(total_cost)}，总毛利 {format_money(total_profit)}，毛利率 {format_percent(margin)}，ROI {format_percent(roi)}。"
    )

    if not city_summary.empty:
        top_city = city_summary.iloc[0]
        insights["核心结论"].append(
            f"盈利性最好的城市是 {top_city['城市']}，平均单场毛利 {format_money(top_city['平均单场毛利'])}，ROI {format_percent(top_city['ROI'])}。"
        )
    if not format_summary.empty:
        top_format = format_summary.iloc[0]
        insights["核心结论"].append(
            f"表现最好的活动形式是 {top_format['活动形式']}，平均单场毛利 {format_money(top_format['平均单场毛利'])}，试饮转化率 {format_percent(top_format['试饮转化率'])}。"
        )
    if not sku_summary.empty:
        top_sku = sku_summary.iloc[0]
        insights["核心结论"].append(
            f"利润贡献主力 SKU 是 {top_sku['产品名称/SKU']}，单品毛利 {format_money(top_sku['单品毛利'])}，利润贡献占比 {format_percent(top_sku['利润贡献占比'])}。"
        )

    best_event = event_summary.iloc[0]
    insights["数据拆解"].append(
        f"单场盈利排行第一为 {best_event['城市']} / {best_event['活动地点']} / {best_event['活动日期']}，毛利 {format_money(best_event['单场毛利'])}，销售总量 {format_int(best_event['销售总量'])}。"
    )
    insights["数据拆解"].append(correlation_text)
    if not conversion_summary.empty:
        best_conversion = conversion_summary.iloc[0]
        insights["数据拆解"].append(
            f"试饮转化最高的 SKU 是 {best_conversion['product_sku']}，总转化率 {format_percent(best_conversion['总转化率'])}，瓶卖占比 {format_percent(best_conversion['瓶卖占比'])}。"
        )

    negative_events = event_summary.loc[event_summary["单场毛利"] < 0]
    if not negative_events.empty:
        insights["风险提示"].append(
            f"有 {len(negative_events)} 场活动毛利为负，优先复盘费用最高或销量最低的场次。"
        )
    no_revenue_events = event_summary.loc[
        (event_summary["销售总量"] > 0) & (event_summary["销售收入"] <= 0)
    ]
    if not no_revenue_events.empty:
        insights["风险提示"].append(
            f"有 {len(no_revenue_events)} 场活动已有销量但销售收入为 0，需补齐 SKU 售价。"
        )
    low_sku = pd.DataFrame()
    if not sku_summary.empty:
        low_sku = sku_summary.loc[
            (sku_summary["销售总量"] > 0)
            & ((sku_summary["单品毛利率"] < 0.2) | (sku_summary["动销率"] < 0.3))
        ]
    if not low_sku.empty:
        insights["风险提示"].append(
            f"{'、'.join(low_sku['产品名称/SKU'].head(3).astype(str).tolist())} 毛利率或动销率偏低，需要优化定价、试饮话术或备货量。"
        )
    if not insights["风险提示"]:
        insights["风险提示"].append("当前筛选范围未发现明显亏损、低动销或售价缺失风险。")

    if not city_summary.empty:
        profitable_city = city_summary.iloc[0]["城市"]
        insights["优化建议"].append(
            f"市场拓展优先选择 {profitable_city}，复制其高毛利点位、人员配置和SKU组合。"
        )
    if not sku_summary.empty:
        main_sku = sku_summary.iloc[0]["产品名称/SKU"]
        insights["优化建议"].append(
            f"新品开发优先围绕 {main_sku} 的口味、容量或礼盒组合做延展，并用同类点位小规模A/B测试。"
        )
    if not format_summary.empty:
        best_format_name = format_summary.iloc[0]["活动形式"]
        insights["优化建议"].append(
            f"活动资源优先投向 {best_format_name}，低ROI活动形式先降低物料和临时人工投入。"
        )
    insights["优化建议"].append(
        "对低转化SKU，先调整试饮后成交话术、买赠门槛和陈列位置，再决定是否减少备货。"
    )

    return insights


def build_alerts(summary: pd.DataFrame) -> list[str]:
    if summary.empty:
        return ["当前场次暂无录入数据。"]

    alerts: list[str] = []
    total_sales = int(summary["销售总量"].sum())
    total_tasting = int(summary["试饮数量"].sum())

    if total_tasting >= 20 and total_sales == 0:
        alerts.append("试饮累计已达到 20 人次以上，但销售为 0，需要现场复盘话术和成交动作。")

    if total_tasting and total_sales:
        conversion = total_sales / total_tasting
        if conversion < 0.15 and total_tasting >= 30:
            alerts.append(
                f"试饮转化率约 {conversion:.1%}，低于 15%，建议强化试饮后的成单引导。"
            )

    if total_sales:
        top_row = summary.iloc[0]
        top_share_text = str(top_row["销售占比"]).replace("%", "")
        try:
            top_share = float(top_share_text) / 100
        except ValueError:
            top_share = 0
        if top_share >= 0.6 and len(summary) >= 2:
            alerts.append(
                f"{top_row['产品名称/SKU']} 占全场销量 {top_row['销售占比']}，备货和陈列需要向该SKU倾斜。"
            )

    zero_sales = summary.loc[
        (summary["试饮数量"] > 0) & (summary["销售总量"] == 0), "产品名称/SKU"
    ].tolist()
    if zero_sales:
        alerts.append(f"{'、'.join(zero_sales)} 有试饮但暂无成交，需要关注口味反馈和价格接受度。")

    return alerts or ["当前数据暂无明显异常，继续保持录入节奏。"]


def build_inventory_alerts(
    city_inventory: pd.DataFrame, event_inventory: pd.DataFrame, selected_city: str
) -> list[str]:
    alerts: list[str] = []

    if not event_inventory.empty:
        negative_site = event_inventory.loc[
            event_inventory["当前现场库存"] < 0, "库存项目"
        ].tolist()
        if negative_site:
            alerts.append(
                f"当前场次 {'、'.join(negative_site[:3])} 现场库存为负，需要核对发货、消耗或退回记录。"
            )

        high_loss = event_inventory.loc[
            (event_inventory["库存类型"] == "物料库存")
            & (event_inventory["发货到现场"] > 0)
            & (event_inventory["现场消耗"] / event_inventory["发货到现场"] >= 0.8),
            "库存项目",
        ].tolist()
        if high_loss:
            alerts.append(
                f"当前场次 {'、'.join(high_loss[:3])} 消耗率达到 80% 以上，下次活动需提前增加备货。"
            )

    if not city_inventory.empty and selected_city:
        selected_city_stock = city_inventory.loc[city_inventory["城市"] == selected_city]
        negative_city = selected_city_stock.loc[
            selected_city_stock["城市仓当前库存"] < 0, "库存项目"
        ].tolist()
        low_city = selected_city_stock.loc[
            selected_city_stock["状态"] == "低库存预警", "库存项目"
        ].tolist()
        if negative_city:
            alerts.append(
                f"{selected_city} 城市仓 {'、'.join(negative_city[:3])} 库存为负，需要先做盘点调整。"
            )
        if low_city:
            alerts.append(
                f"{selected_city} 城市仓 {'、'.join(low_city[:3])} 已触发低库存预警，建议补货或调拨。"
            )

    return alerts or ["当前库存数据暂无明显异常。"]


def format_int(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "0"


def format_money(value: Any) -> str:
    try:
        return f"¥{float(value):,.2f}"
    except (TypeError, ValueError):
        return "¥0.00"


def format_percent(value: Any) -> str:
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return "0.0%"


def can_save(city: str, location: str, sku: str) -> bool:
    return bool(city.strip() and location.strip() and sku.strip() and sku != "新增SKU")


def require_manager_access(page_name: str) -> bool:
    if page_name not in PROTECTED_PAGES:
        return True
    if st.session_state.get("manager_authenticated", False):
        return True

    st.warning("请输入管理密码后继续。")
    with st.form(f"manager_auth_{page_name}"):
        password = st.text_input("管理密码", type="password", placeholder="请输入管理密码")
        submitted = st.form_submit_button("进入管理页面")

    if submitted:
        if password == MANAGER_PASSWORD:
            st.session_state["manager_authenticated"] = True
            st.rerun()
        else:
            st.session_state["auth_error"] = "无权限访问，此功能仅对管理层开放"
            st.session_state["redirect_to_sales"] = True
            st.rerun()

    return False


def render_css() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 980px;
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }
        div[data-testid="stButton"] > button {
            min-height: 3.4rem;
            border-radius: 0.5rem;
            font-size: 1.05rem;
            font-weight: 700;
            width: 100%;
        }
        div[data-testid="stFormSubmitButton"] > button {
            min-height: 3.2rem;
            border-radius: 0.5rem;
            font-size: 1.02rem;
            font-weight: 700;
            width: 100%;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.65rem;
        }
        @media (max-width: 640px) {
            .block-container {
                padding-left: 0.75rem;
                padding-right: 0.75rem;
            }
            div[data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sales_page() -> None:
    df_all = load_records()

    if "last_saved" in st.session_state:
        st.success(st.session_state.pop("last_saved"))

    st.subheader("场次信息")
    city_col, date_col = st.columns(2)
    with city_col:
        selected_city = st.selectbox("城市", CITY_OPTIONS, index=0)
        city = selected_city
        if selected_city == "其他":
            city = st.text_input("自定义城市", placeholder="例如：宁波").strip()

    with date_col:
        activity_date = st.date_input("活动日期", value=date.today())

    location_options = build_location_options(df_all, city)
    selected_location = st.selectbox("活动地点", location_options)
    if selected_location == "新增活动地点":
        location = st.text_input("新增活动地点", placeholder="例如：杭州湖滨银泰A区").strip()
    else:
        location = selected_location

    st.divider()

    st.subheader("快速录入")
    sku_options = build_product_options(df_all)
    selected_sku = st.selectbox("产品名称/SKU", sku_options)
    if selected_sku == "新增SKU":
        product_sku = st.text_input(
            "新增产品名称/SKU", placeholder="例如：OKKISS 荔枝起泡酒 275ml"
        ).strip()
    else:
        product_sku = selected_sku

    save_disabled = not can_save(city, location, product_sku)
    cup_col, bottle_col, tasting_col = st.columns(3)
    with cup_col:
        if st.button("杯卖 +1", disabled=save_disabled, use_container_width=True):
            append_record(
                city=city,
                activity_date=activity_date,
                location=location,
                product_sku=product_sku,
                cup_qty=1,
                bottle_qty=0,
                tasting_qty=0,
            )
            st.session_state["last_saved"] = f"已保存：{product_sku} 杯卖 +1"
            st.rerun()

    with bottle_col:
        if st.button("瓶卖 +1", disabled=save_disabled, use_container_width=True):
            append_record(
                city=city,
                activity_date=activity_date,
                location=location,
                product_sku=product_sku,
                cup_qty=0,
                bottle_qty=1,
                tasting_qty=0,
            )
            st.session_state["last_saved"] = f"已保存：{product_sku} 瓶卖 +1"
            st.rerun()

    with tasting_col:
        if st.button("试饮 +1", disabled=save_disabled, use_container_width=True):
            append_record(
                city=city,
                activity_date=activity_date,
                location=location,
                product_sku=product_sku,
                cup_qty=0,
                bottle_qty=0,
                tasting_qty=1,
            )
            st.session_state["last_saved"] = f"已保存：{product_sku} 试饮 +1"
            st.rerun()

    with st.expander("批量补录", expanded=False):
        with st.form("batch_entry", clear_on_submit=True):
            batch_col_1, batch_col_2, batch_col_3 = st.columns(3)
            with batch_col_1:
                cup_qty = st.number_input("杯卖数量", min_value=0, step=1, value=0)
            with batch_col_2:
                bottle_qty = st.number_input("瓶卖数量", min_value=0, step=1, value=0)
            with batch_col_3:
                tasting_qty = st.number_input("试饮数量", min_value=0, step=1, value=0)
            note = st.text_input("备注", placeholder="例如：晚高峰补录")
            submitted = st.form_submit_button("保存本次录入", disabled=save_disabled)

            if submitted:
                total_input = int(cup_qty) + int(bottle_qty) + int(tasting_qty)
                if total_input <= 0:
                    st.warning("请至少填写 1 个杯卖、瓶卖或试饮数量。")
                else:
                    append_record(
                        city=city,
                        activity_date=activity_date,
                        location=location,
                        product_sku=product_sku,
                        cup_qty=int(cup_qty),
                        bottle_qty=int(bottle_qty),
                        tasting_qty=int(tasting_qty),
                        note=note,
                    )
                    st.session_state["last_saved"] = f"已保存：{product_sku} 本次补录"
                    st.rerun()

    if save_disabled:
        st.info("请先补全城市、活动日期、活动地点和产品名称/SKU。")

    st.divider()

    df_all = load_records()
    df_event = current_event_records(df_all, city, activity_date, location)
    summary = summarize_records(df_event)

    st.subheader("本场统计")
    total_cups = int(df_event["cup_qty"].sum()) if not df_event.empty else 0
    total_bottles = int(df_event["bottle_qty"].sum()) if not df_event.empty else 0
    total_tasting = int(df_event["tasting_qty"].sum()) if not df_event.empty else 0
    total_sales = total_cups + total_bottles

    metric_cols = st.columns(4)
    metric_cols[0].metric("销售总量", format_int(total_sales))
    metric_cols[1].metric("杯卖数量", format_int(total_cups))
    metric_cols[2].metric("瓶卖数量", format_int(total_bottles))
    metric_cols[3].metric("试饮数量", format_int(total_tasting))

    st.markdown("**全场畅销 TOP3**")
    top3 = summary.head(3)
    if top3.empty:
        st.info("录入后自动生成 TOP3。")
    else:
        top_cols = st.columns(3)
        for index, (_, row) in enumerate(top3.iterrows()):
            top_cols[index].metric(
                f"TOP{index + 1}",
                str(row["产品名称/SKU"]),
                f"销售总量 {format_int(row['销售总量'])}",
            )

    st.markdown("**单产品销量排行**")
    st.dataframe(summary, use_container_width=True, hide_index=True)

    alerts = build_alerts(summary)
    st.markdown("**现场提醒**")
    for alert in alerts:
        st.write(f"- {alert}")

    st.divider()

    st.subheader("数据导出")
    csv_data = df_event.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        "导出当前场次CSV",
        data=csv_data,
        file_name=f"OKKISS_{city}_{activity_date.isoformat()}_{location}.csv",
        mime="text/csv",
        use_container_width=True,
        disabled=df_event.empty,
    )
    st.caption(f"自动保存文件：{DATA_FILE}")

    with st.expander("查看最近录入", expanded=False):
        recent_cols = [
            "created_at",
            "city",
            "activity_date",
            "location",
            "product_sku",
            "cup_qty",
            "bottle_qty",
            "tasting_qty",
            "note",
        ]
        recent_records = df_event.sort_values("created_at", ascending=False).head(30)
        st.dataframe(recent_records[recent_cols], use_container_width=True, hide_index=True)


def render_inventory_page() -> None:
    sales_df = load_records()
    inventory_df = load_inventory_movements()

    if "inventory_saved" in st.session_state:
        st.success(st.session_state.pop("inventory_saved"))

    st.subheader("库存场次信息")
    city_col, date_col = st.columns(2)
    with city_col:
        selected_city = st.selectbox("库存城市", CITY_OPTIONS, index=0, key="inventory_city")
        city = selected_city
        if selected_city == "其他":
            city = st.text_input("自定义库存城市", placeholder="例如：宁波").strip()

    with date_col:
        activity_date = st.date_input("库存活动日期", value=date.today())

    location_options = build_inventory_location_options(sales_df, inventory_df, city)
    selected_location = st.selectbox("库存活动地点", location_options)
    if selected_location == "新增活动地点":
        location = st.text_input("新增库存活动地点", placeholder="例如：杭州湖滨银泰A区").strip()
    else:
        location = selected_location

    st.divider()

    st.subheader("库存流水录入")
    with st.form("inventory_entry", clear_on_submit=True):
        item_col, flow_col = st.columns(2)
        with item_col:
            item_category = st.radio(
                "库存类型",
                ["起泡酒产品库存", "物料库存"],
                horizontal=True,
            )
            item_options = build_inventory_item_options(inventory_df, item_category)
            selected_item = st.selectbox("库存项目", item_options)
            if selected_item == "新增库存项目":
                item_name = st.text_input(
                    "新增库存项目",
                    placeholder="例如：OKKISS 荔枝起泡酒 275ml / 品鉴杯",
                ).strip()
            else:
                item_name = selected_item

            default_unit_value = default_unit(item_category, item_name)
            default_unit_index = (
                UNIT_OPTIONS.index(default_unit_value)
                if default_unit_value in UNIT_OPTIONS
                else 0
            )
            unit = st.selectbox("单位", UNIT_OPTIONS, index=default_unit_index)

        with flow_col:
            flow_type = st.radio("记录流程", FLOW_TYPES)
            adjustment_area = WAREHOUSE_AREA
            if flow_type == "库存盘点调整":
                adjustment_area = st.radio(
                    "调整库存位置", [WAREHOUSE_AREA, SITE_AREA], horizontal=True
                )
                quantity = st.number_input(
                    "调整数量（可填负数）",
                    min_value=-100000,
                    max_value=100000,
                    step=1,
                    value=0,
                )
            else:
                quantity = st.number_input(
                    "数量",
                    min_value=1,
                    max_value=100000,
                    step=1,
                    value=1,
                )
            note = st.text_input("备注", placeholder="例如：A场活动发货 / 损耗登记")

        needs_site_location = flow_type in [
            "城市仓库发货到现场",
            "现场实际消耗",
            "未卖完/未使用退回仓库",
        ] or (flow_type == "库存盘点调整" and adjustment_area == SITE_AREA)
        save_disabled = not city.strip() or not item_name.strip() or (
            needs_site_location and not location.strip()
        )
        submitted = st.form_submit_button("保存库存流水", disabled=save_disabled)

        if submitted:
            if int(quantity) == 0:
                st.warning("库存数量不能为 0。")
            else:
                effective_location = location if needs_site_location else WAREHOUSE_AREA
                append_inventory_movement(
                    city=city,
                    activity_date=activity_date,
                    location=effective_location,
                    item_category=item_category,
                    item_name=item_name,
                    unit=unit,
                    flow_type=flow_type,
                    quantity=int(quantity),
                    adjustment_area=adjustment_area,
                    note=note,
                )
                st.session_state["inventory_saved"] = (
                    f"已保存库存流水：{item_name} {flow_type} {format_int(quantity)}{unit}"
                )
                st.rerun()

    if not city.strip() or not location.strip():
        st.info("发货、现场消耗、退回和现场盘点调整需要先补全城市与活动地点。")

    st.divider()

    inventory_df = load_inventory_movements()
    city_inventory = summarize_city_inventory(inventory_df)
    event_inventory = summarize_event_inventory(inventory_df, city, activity_date, location)
    material_loss = summarize_material_loss(event_inventory)

    selected_city_inventory = city_inventory.loc[city_inventory["城市"] == city]
    city_product_qty = (
        int(
            selected_city_inventory.loc[
                selected_city_inventory["库存类型"] == "起泡酒产品库存",
                "城市仓当前库存",
            ].sum()
        )
        if not selected_city_inventory.empty
        else 0
    )
    event_product_qty = (
        int(
            event_inventory.loc[
                event_inventory["库存类型"] == "起泡酒产品库存", "当前现场库存"
            ].sum()
        )
        if not event_inventory.empty
        else 0
    )
    event_material_count = (
        int((event_inventory["库存类型"] == "物料库存").sum())
        if not event_inventory.empty
        else 0
    )
    warning_count = (
        int((selected_city_inventory["状态"] != "正常").sum())
        if not selected_city_inventory.empty
        else 0
    )

    st.subheader("库存看板")
    metric_cols = st.columns(4)
    metric_cols[0].metric(f"{city} 城市仓产品库存", format_int(city_product_qty))
    metric_cols[1].metric("当前现场产品库存", format_int(event_product_qty))
    metric_cols[2].metric("当前现场物料项目", format_int(event_material_count))
    metric_cols[3].metric("城市仓预警项目", format_int(warning_count))

    st.markdown("**当前场次实时库存**")
    if event_inventory.empty:
        st.info("录入发货、消耗或退回后自动生成当前场次库存。")
    else:
        st.dataframe(event_inventory, use_container_width=True, hide_index=True)

    st.markdown("**单场活动物料损耗率**")
    if material_loss.empty:
        st.info("当前场次暂无物料发货或消耗数据。")
    else:
        st.dataframe(material_loss, use_container_width=True, hide_index=True)

    st.markdown("**各城市库存分布与预警**")
    if city_inventory.empty:
        st.info("录入城市仓补货或期初库存后自动生成城市库存分布。")
    else:
        st.dataframe(city_inventory, use_container_width=True, hide_index=True)

    alerts = build_inventory_alerts(city_inventory, event_inventory, city)
    st.markdown("**库存提醒**")
    for alert in alerts:
        st.write(f"- {alert}")

    st.divider()

    st.subheader("库存数据导出")
    inventory_csv = inventory_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        "导出库存流水CSV",
        data=inventory_csv,
        file_name="OKKISS_inventory_movements.csv",
        mime="text/csv",
        use_container_width=True,
        disabled=inventory_df.empty,
    )
    st.caption(f"自动保存文件：{INVENTORY_FILE}")

    with st.expander("查看最近库存流水", expanded=False):
        recent_cols = [
            "created_at",
            "city",
            "activity_date",
            "location",
            "item_category",
            "item_name",
            "unit",
            "flow_type",
            "quantity",
            "warehouse_delta",
            "site_delta",
            "consumed_qty",
            "returned_qty",
            "note",
        ]
        recent_movements = inventory_df.sort_values("created_at", ascending=False).head(50)
        st.dataframe(recent_movements[recent_cols], use_container_width=True, hide_index=True)


def render_cost_page() -> None:
    sales_df = load_records()
    inventory_df = load_inventory_movements()
    cost_df = load_cost_records()
    price_df = load_price_settings()

    if "price_saved" in st.session_state:
        st.success(st.session_state.pop("price_saved"))
    if "cost_saved" in st.session_state:
        st.success(st.session_state.pop("cost_saved"))

    st.subheader("成本核算场次")
    city_col, date_col = st.columns(2)
    with city_col:
        selected_city = st.selectbox("费用城市", CITY_OPTIONS, index=0, key="cost_city")
        city = selected_city
        if selected_city == "其他":
            city = st.text_input("自定义费用城市", placeholder="例如：宁波").strip()
    with date_col:
        activity_date = st.date_input("费用活动日期", value=date.today())

    location_options = build_cost_location_options(sales_df, inventory_df, cost_df, city)
    selected_location = st.selectbox("费用活动地点", location_options)
    if selected_location == "新增活动地点":
        location = st.text_input("新增费用活动地点", placeholder="例如：杭州湖滨银泰A区").strip()
    else:
        location = selected_location

    sku_options = build_cost_sku_options(sales_df, cost_df, price_df)

    with st.expander("销售价格设置（用于毛利率与ROI）", expanded=False):
        with st.form("price_setting_form"):
            price_sku_selected = st.selectbox("设置售价的SKU", sku_options)
            if price_sku_selected == "新增SKU":
                price_sku = st.text_input(
                    "新增售价SKU", placeholder="例如：OKKISS 荔枝起泡酒 275ml"
                ).strip()
            else:
                price_sku = price_sku_selected

            current_prices = get_price_map(price_df).get(
                price_sku, {"cup_price": 0.0, "bottle_price": 0.0}
            )
            price_col_1, price_col_2 = st.columns(2)
            with price_col_1:
                cup_price = st.number_input(
                    "杯装售价",
                    min_value=0.0,
                    step=1.0,
                    value=float(current_prices["cup_price"]),
                )
            with price_col_2:
                bottle_price = st.number_input(
                    "瓶装售价",
                    min_value=0.0,
                    step=1.0,
                    value=float(current_prices["bottle_price"]),
                )

            price_submitted = st.form_submit_button(
                "保存SKU售价", disabled=not price_sku.strip()
            )
            if price_submitted:
                upsert_price_setting(price_sku, float(cup_price), float(bottle_price))
                st.session_state["price_saved"] = (
                    f"已保存售价：{price_sku} 杯装 {format_money(cup_price)}，瓶装 {format_money(bottle_price)}"
                )
                st.rerun()

        if price_df.empty:
            st.info("尚未设置售价。没有售价时，销售收入、毛利率和ROI会按 0 计算。")
        else:
            st.dataframe(price_df, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("费用明细录入")
    with st.form("cost_entry_form", clear_on_submit=True):
        cost_col_1, cost_col_2 = st.columns(2)
        with cost_col_1:
            cost_type = st.radio("费用类型", COST_TYPES)
            product_sku = ""
            if cost_type == "产品成本":
                cost_subtype = "产品采购成本"
                cost_sku_selected = st.selectbox("成本关联SKU", sku_options)
                if cost_sku_selected == "新增SKU":
                    product_sku = st.text_input(
                        "新增成本SKU", placeholder="例如：OKKISS 荔枝起泡酒 275ml"
                    ).strip()
                else:
                    product_sku = cost_sku_selected
            elif cost_type == "物料采购费":
                cost_subtype = st.selectbox(
                    "物料采购项目", MATERIAL_ITEMS + ["其他物料"]
                )
            elif cost_type == "运费":
                cost_subtype = st.selectbox("运费明细", FREIGHT_SUBTYPES)
            else:
                cost_subtype = st.selectbox("其他杂费明细", OTHER_COST_SUBTYPES)

        with cost_col_2:
            default_qty = 1.0
            unit_price = st.number_input(
                "单价/单次金额",
                min_value=0.0,
                max_value=1000000.0,
                step=1.0,
                value=0.0,
            )
            quantity = st.number_input(
                "数量/次数",
                min_value=0.0,
                max_value=1000000.0,
                step=1.0,
                value=default_qty,
            )
            amount = float(unit_price) * float(quantity)
            st.metric("本条费用金额", format_money(amount))
            note = st.text_input("费用备注", placeholder="例如：仓库到现场打车送货")

        cost_disabled = (
            not city.strip()
            or not location.strip()
            or float(unit_price) <= 0
            or float(quantity) <= 0
            or (cost_type == "产品成本" and not product_sku.strip())
        )
        submitted = st.form_submit_button("保存费用明细", disabled=cost_disabled)
        if submitted:
            append_cost_record(
                city=city,
                activity_date=activity_date,
                location=location,
                cost_type=cost_type,
                cost_subtype=cost_subtype,
                product_sku=product_sku,
                unit_price=float(unit_price),
                quantity=float(quantity),
                note=note,
            )
            st.session_state["cost_saved"] = (
                f"已保存费用：{cost_type} / {cost_subtype}，金额 {format_money(amount)}"
            )
            st.rerun()

    if not city.strip() or not location.strip():
        st.info("请先补全城市、活动日期和活动地点，再录入费用明细。")

    st.divider()

    sales_df = load_records()
    cost_df = load_cost_records()
    price_df = load_price_settings()
    event_sales_df = current_event_records(sales_df, city, activity_date, location)
    event_cost_df = current_event_cost_records(cost_df, city, activity_date, location)
    sales_summary = summarize_event_sales_for_cost(event_sales_df, price_df)
    cost_summary = summarize_cost_by_type(event_cost_df)
    product_cost_summary = build_product_cost_summary(sales_summary, event_cost_df)
    metrics = calculate_cost_metrics(sales_summary, event_cost_df)

    st.subheader("单场成本核算")
    metric_cols = st.columns(4)
    metric_cols[0].metric("销售收入", format_money(metrics["total_revenue"]))
    metric_cols[1].metric("单场活动总成本", format_money(metrics["total_cost"]))
    metric_cols[2].metric("单场毛利", format_money(metrics["gross_profit"]))
    metric_cols[3].metric("单场毛利率", format_percent(metrics["gross_margin"]))

    roi_cols = st.columns(2)
    roi_cols[0].metric("投入产出比", f"{metrics['input_output']:.2f}")
    roi_cols[1].metric("ROI", format_percent(metrics["roi"]))

    st.markdown("**成本-销量对应关系**")
    if product_cost_summary.empty:
        st.info("当前场次暂无销售或费用数据，录入后自动生成成本-销量对应关系。")
    else:
        st.dataframe(product_cost_summary, use_container_width=True, hide_index=True)

    st.markdown("**费用分类汇总**")
    if cost_summary.empty:
        st.info("当前场次暂无费用明细。")
    else:
        st.dataframe(cost_summary, use_container_width=True, hide_index=True)

    st.markdown("**销售收入关联表**")
    if sales_summary.empty:
        st.info("当前场次暂无销售记录。")
    else:
        st.dataframe(sales_summary, use_container_width=True, hide_index=True)

    alerts = build_cost_alerts(metrics, sales_summary, event_cost_df)
    st.markdown("**成本提醒**")
    for alert in alerts:
        st.write(f"- {alert}")

    st.divider()

    st.subheader("成本数据导出")
    excel_data = build_cost_excel(
        cost_df=event_cost_df,
        sales_summary=sales_summary,
        cost_summary=cost_summary,
        product_cost_summary=product_cost_summary,
        price_df=price_df,
        metrics=metrics,
    )
    st.download_button(
        "导出当前场次成本明细Excel",
        data=excel_data,
        file_name=f"OKKISS_cost_{city}_{activity_date.isoformat()}_{location}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        disabled=event_cost_df.empty and sales_summary.empty,
    )
    st.caption(f"费用明细自动保存文件：{COST_FILE}")

    with st.expander("查看最近费用明细", expanded=False):
        recent_cols = [
            "created_at",
            "city",
            "activity_date",
            "location",
            "cost_type",
            "cost_subtype",
            "product_sku",
            "unit_price",
            "quantity",
            "amount",
            "note",
        ]
        recent_costs = cost_df.sort_values("created_at", ascending=False).head(50)
        st.dataframe(recent_costs[recent_cols], use_container_width=True, hide_index=True)


def render_insights_page() -> None:
    sales_df = load_records()
    cost_df = load_cost_records()
    inventory_df = load_inventory_movements()
    price_df = load_price_settings()

    city_options, sku_options, default_start, default_end = collect_filter_options(
        sales_df, cost_df, inventory_df
    )

    st.subheader("盈利分析筛选")
    filter_col_1, filter_col_2 = st.columns(2)
    with filter_col_1:
        selected_cities = st.multiselect(
            "筛选城市",
            city_options,
            default=city_options,
            key="insight_cities",
        )
    with filter_col_2:
        selected_skus = st.multiselect(
            "筛选SKU",
            sku_options,
            default=sku_options,
            key="insight_skus",
        )

    date_range = st.date_input(
        "筛选时间范围",
        value=(default_start, default_end),
        key="insight_date_range",
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = default_start
        end_date = default_end

    sales_scope = filter_by_analytics_scope(
        sales_df,
        selected_cities=selected_cities,
        selected_skus=selected_skus,
        start_date=start_date,
        end_date=end_date,
        sku_column="product_sku",
    )
    cost_scope = filter_by_analytics_scope(
        cost_df,
        selected_cities=selected_cities,
        selected_skus=selected_skus,
        start_date=start_date,
        end_date=end_date,
        sku_column="product_sku",
        keep_shared_cost=True,
    )
    inventory_scope = filter_by_analytics_scope(
        inventory_df,
        selected_cities=selected_cities,
        selected_skus=selected_skus,
        start_date=start_date,
        end_date=end_date,
        sku_column="item_name",
    )

    event_summary = build_event_profit_summary(sales_scope, cost_scope, price_df)
    city_summary = summarize_dimension_profit(event_summary, "城市")
    format_summary = summarize_dimension_profit(event_summary, "活动形式")
    sku_summary = build_sku_insight_summary(
        sales_scope, cost_scope, inventory_scope, price_df
    )
    conversion_by_sku = build_conversion_summary(sales_scope, "product_sku")
    conversion_by_city = build_conversion_summary(sales_scope, "city")
    correlation_value, correlation_text = calculate_cost_sales_correlation(event_summary)
    insights = generate_business_insights(
        event_summary,
        city_summary,
        format_summary,
        sku_summary,
        conversion_by_sku,
        correlation_text,
    )

    st.divider()

    st.subheader("经营结论")
    for section, items in insights.items():
        st.markdown(f"**{section}**")
        for item in items:
            st.write(f"- {item}")

    st.divider()

    total_revenue = float(event_summary["销售收入"].sum()) if not event_summary.empty else 0
    total_cost = (
        float(event_summary["单场活动总成本"].sum()) if not event_summary.empty else 0
    )
    total_profit = float(event_summary["单场毛利"].sum()) if not event_summary.empty else 0
    total_sales = int(event_summary["销售总量"].sum()) if not event_summary.empty else 0
    margin = total_profit / total_revenue if total_revenue > 0 else 0.0

    metric_cols = st.columns(4)
    metric_cols[0].metric("销售收入", format_money(total_revenue))
    metric_cols[1].metric("总成本", format_money(total_cost))
    metric_cols[2].metric("总毛利", format_money(total_profit))
    metric_cols[3].metric("毛利率", format_percent(margin))
    st.metric("筛选范围销售总量", format_int(total_sales))

    st.divider()

    st.subheader("各城市单场活动盈利排行")
    if event_summary.empty:
        st.info("当前筛选范围暂无活动盈利数据。")
    else:
        event_chart_data = event_summary.head(15)
        event_chart = (
            alt.Chart(event_chart_data)
            .mark_bar()
            .encode(
                x=alt.X("单场毛利:Q", title="单场毛利"),
                y=alt.Y("活动标签:N", sort="-x", title="活动"),
                color=alt.Color("城市:N", title="城市"),
                tooltip=[
                    "城市",
                    "活动日期",
                    "活动地点",
                    "活动形式",
                    alt.Tooltip("销售收入:Q", format=",.2f"),
                    alt.Tooltip("单场活动总成本:Q", format=",.2f"),
                    alt.Tooltip("单场毛利:Q", format=",.2f"),
                    alt.Tooltip("ROI:Q", format=".1%"),
                ],
            )
            .properties(height=360)
        )
        st.altair_chart(event_chart, use_container_width=True)
        event_display = format_percent_columns(
            event_summary,
            ["单场毛利率", "ROI", "试饮转化率", "杯卖占比", "瓶卖占比"],
        )
        st.dataframe(event_display, use_container_width=True, hide_index=True)

    st.markdown("**城市盈利汇总**")
    if city_summary.empty:
        st.info("当前筛选范围暂无城市汇总数据。")
    else:
        city_chart = (
            alt.Chart(city_summary)
            .mark_bar()
            .encode(
                x=alt.X("城市:N", sort="-y", title="城市"),
                y=alt.Y("平均单场毛利:Q", title="平均单场毛利"),
                color=alt.Color("ROI:Q", title="ROI"),
                tooltip=[
                    "城市",
                    "活动场次",
                    alt.Tooltip("销售收入:Q", format=",.2f"),
                    alt.Tooltip("总毛利:Q", format=",.2f"),
                    alt.Tooltip("平均单场毛利:Q", format=",.2f"),
                    alt.Tooltip("ROI:Q", format=".1%"),
                ],
            )
            .properties(height=260)
        )
        st.altair_chart(city_chart, use_container_width=True)
        st.dataframe(
            format_percent_columns(city_summary, ["毛利率", "ROI", "试饮转化率"]),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("**活动形式盈利汇总**")
    if format_summary.empty:
        st.info("当前筛选范围暂无活动形式汇总数据。")
    else:
        format_chart = (
            alt.Chart(format_summary)
            .mark_bar()
            .encode(
                x=alt.X("活动形式:N", sort="-y", title="活动形式"),
                y=alt.Y("平均单场毛利:Q", title="平均单场毛利"),
                tooltip=[
                    "活动形式",
                    "活动场次",
                    alt.Tooltip("平均单场毛利:Q", format=",.2f"),
                    alt.Tooltip("试饮转化率:Q", format=".1%"),
                ],
            )
            .properties(height=260)
        )
        st.altair_chart(format_chart, use_container_width=True)
        st.dataframe(
            format_percent_columns(format_summary, ["毛利率", "ROI", "试饮转化率"]),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.subheader("不同SKU毛利率与动销率对比")
    if sku_summary.empty:
        st.info("当前筛选范围暂无SKU盈利数据。")
    else:
        sku_chart = (
            alt.Chart(sku_summary)
            .mark_circle(opacity=0.78)
            .encode(
                x=alt.X("动销率:Q", axis=alt.Axis(format=".0%"), title="动销率"),
                y=alt.Y("单品毛利率:Q", axis=alt.Axis(format=".0%"), title="单品毛利率"),
                size=alt.Size("销售收入:Q", title="销售收入"),
                color=alt.Color("产品名称/SKU:N", title="SKU"),
                tooltip=[
                    "产品名称/SKU",
                    "销售总量",
                    "发货到现场",
                    alt.Tooltip("销售收入:Q", format=",.2f"),
                    alt.Tooltip("单品毛利:Q", format=",.2f"),
                    alt.Tooltip("单品毛利率:Q", format=".1%"),
                    alt.Tooltip("动销率:Q", format=".1%"),
                    alt.Tooltip("利润贡献占比:Q", format=".1%"),
                ],
            )
            .properties(height=360)
        )
        st.altair_chart(sku_chart, use_container_width=True)
        sku_display = format_percent_columns(
            sku_summary,
            ["单品毛利率", "动销率", "利润贡献占比", "试饮转化率"],
        )
        st.dataframe(sku_display, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("杯卖/瓶卖/试饮转化率分析")
    conversion_view = st.radio(
        "转化率查看维度", ["按SKU", "按城市"], horizontal=True, key="conversion_view"
    )
    if conversion_view == "按SKU":
        conversion_chart_df = conversion_by_sku.rename(columns={"product_sku": "维度"})
    else:
        conversion_chart_df = conversion_by_city.rename(columns={"city": "维度"})

    if conversion_chart_df.empty:
        st.info("当前筛选范围暂无试饮转化数据。")
    else:
        conversion_chart = (
            alt.Chart(conversion_chart_df)
            .mark_bar()
            .encode(
                x=alt.X("总转化率:Q", axis=alt.Axis(format=".0%"), title="总转化率"),
                y=alt.Y("维度:N", sort="-x", title=conversion_view),
                color=alt.Color("瓶卖占比:Q", title="瓶卖占比"),
                tooltip=[
                    "维度",
                    "杯卖数量",
                    "瓶卖数量",
                    "试饮数量",
                    alt.Tooltip("杯卖转化率:Q", format=".1%"),
                    alt.Tooltip("瓶卖转化率:Q", format=".1%"),
                    alt.Tooltip("总转化率:Q", format=".1%"),
                    alt.Tooltip("瓶卖占比:Q", format=".1%"),
                ],
            )
            .properties(height=320)
        )
        st.altair_chart(conversion_chart, use_container_width=True)
        st.dataframe(
            format_percent_columns(
                conversion_chart_df,
                ["杯卖转化率", "瓶卖转化率", "总转化率", "瓶卖占比"],
            ),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.subheader("成本投入与销量相关性")
    st.write(f"- {correlation_text}")
    if event_summary.empty:
        st.info("当前筛选范围暂无可用于相关性分析的场次。")
    else:
        corr_chart = (
            alt.Chart(event_summary)
            .mark_circle(size=95, opacity=0.78)
            .encode(
                x=alt.X("单场活动总成本:Q", title="单场活动总成本"),
                y=alt.Y("销售总量:Q", title="销售总量"),
                color=alt.Color("城市:N", title="城市"),
                shape=alt.Shape("活动形式:N", title="活动形式"),
                tooltip=[
                    "城市",
                    "活动日期",
                    "活动地点",
                    "活动形式",
                    "销售总量",
                    alt.Tooltip("单场活动总成本:Q", format=",.2f"),
                    alt.Tooltip("单场毛利:Q", format=",.2f"),
                ],
            )
            .properties(height=340)
        )
        st.altair_chart(corr_chart, use_container_width=True)
        st.caption(f"成本-销量相关系数：{correlation_value:.2f}")


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    render_css()

    st.title(APP_TITLE)
    if "active_page" not in st.session_state:
        st.session_state["active_page"] = "销售录入"
    if st.session_state.pop("redirect_to_sales", False):
        st.session_state["active_page"] = "销售录入"
    if "auth_error" in st.session_state:
        st.error(st.session_state.pop("auth_error"))

    active_page = st.radio(
        "功能模块",
        PAGE_OPTIONS,
        horizontal=True,
        key="active_page",
    )

    if not require_manager_access(active_page):
        return

    if active_page == "销售录入":
        render_sales_page()
    elif active_page == "库存管理":
        render_inventory_page()
    elif active_page == "费用与成本":
        render_cost_page()
    elif active_page == "盈利分析与洞察":
        render_insights_page()


if __name__ == "__main__":
    main()
