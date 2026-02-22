import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="POS Pro", layout="wide")

# ==============================
# HÀM FORMAT TIỀN
# ==============================
def format_vnd(value):
    return f"{value:,.0f} VND"

# ==============================
# TẠO DỮ LIỆU BAN ĐẦU
# ==============================
if not os.path.exists("products.csv"):
    df = pd.DataFrame({
        "ID": range(1, 11),
        "Tên sản phẩm": [
            "Bánh mì", "Coca Cola", "Pepsi", "Sữa tươi", "Mì gói",
            "Bánh snack", "Trà sữa", "Nước suối", "Cà phê", "Kẹo ngọt"
        ],
        "Giá": [15000,12000,11000,20000,5000,10000,30000,8000,25000,7000]
    })
    df.to_csv("products.csv", index=False)

if not os.path.exists("invoice_details.csv"):
    df = pd.DataFrame(columns=[
        "Mã hóa đơn","Sản phẩm","Số lượng","Đơn giá","Thành tiền","Thời gian"
    ])
    df.to_csv("invoice_details.csv", index=False)

products = pd.read_csv("products.csv")
invoices = pd.read_csv("invoice_details.csv")

if "cart" not in st.session_state:
    st.session_state.cart = []

# ==============================
# SIDEBAR
# ==============================
st.sidebar.title("🛒 QUẢN LÝ BÁN HÀNG")
menu = st.sidebar.radio("Menu", [
    "📦 Sản phẩm",
    "💰 Bán hàng",
    "📜 Hóa đơn",
    "📊 Thống kê"
])

# =====================================================
# 1️⃣ SẢN PHẨM
# =====================================================
if menu == "📦 Sản phẩm":

    st.header("📦 Quản lý sản phẩm")

    # 🔎 TÌM KIẾM REALTIME
    search_text = st.text_input("🔎 Nhập tên sản phẩm cần tìm")

    if search_text:
        filtered = products[
            products["Tên sản phẩm"]
            .str.lower()
            .str.contains(search_text.lower())
        ]
    else:
        filtered = products

    display_df = filtered.copy()
    display_df["Giá"] = display_df["Giá"].apply(format_vnd)

    st.dataframe(display_df, use_container_width=True)

    st.divider()
    tab1, tab2, tab3 = st.tabs(["➕ Thêm", "✏️ Sửa", "❌ Xóa"])

    # ================= ADD =================
    with tab1:
        new_name = st.text_input("Tên sản phẩm mới")
        new_price = st.number_input("Giá (VND)", min_value=0)

        if st.button("Thêm sản phẩm"):
            if new_name:
                new_id = products["ID"].max() + 1
                new_row = pd.DataFrame(
                    [[new_id,new_name,new_price]],
                    columns=products.columns
                )
                products = pd.concat([products,new_row], ignore_index=True)
                products.to_csv("products.csv", index=False)
                st.success("Đã thêm sản phẩm!")
                st.rerun()

    # ================= EDIT =================
    with tab2:
        selected_product = st.selectbox(
            "Chọn sản phẩm",
            products["Tên sản phẩm"]
        )

        product_row = products[
            products["Tên sản phẩm"] == selected_product
        ].iloc[0]

        edit_name = st.text_input(
            "Tên mới",
            value=product_row["Tên sản phẩm"]
        )

        edit_price = st.number_input(
            "Giá mới (VND)",
            min_value=0,
            value=int(product_row["Giá"])
        )

        if st.button("Cập nhật sản phẩm"):
            products.loc[
                products["Tên sản phẩm"] == selected_product,
                ["Tên sản phẩm","Giá"]
            ] = [edit_name, edit_price]

            products.to_csv("products.csv", index=False)
            st.success("Đã cập nhật!")
            st.rerun()

    # ================= DELETE =================
    with tab3:
        del_product = st.selectbox(
            "Chọn sản phẩm cần xóa",
            products["Tên sản phẩm"]
        )

        if st.button("Xóa sản phẩm"):
            products = products[
                products["Tên sản phẩm"] != del_product
            ]
            products.to_csv("products.csv", index=False)
            st.success("Đã xóa!")
            st.rerun()

# =====================================================
# 2️⃣ BÁN HÀNG
# =====================================================
elif menu == "💰 Bán hàng":

    st.header("🛒 Giỏ hàng")

    col1, col2 = st.columns([2,1])

    with col1:
        product_name = st.selectbox(
            "Chọn sản phẩm",
            products["Tên sản phẩm"]
        )

    with col2:
        qty = st.number_input("Số lượng", min_value=1, step=1)

    price = products[
        products["Tên sản phẩm"]==product_name
    ]["Giá"].values[0]

    st.info(f"Đơn giá: {format_vnd(price)}")

    if st.button("➕ Thêm vào giỏ"):
        st.session_state.cart.append({
            "Sản phẩm": product_name,
            "Số lượng": qty,
            "Đơn giá": price,
            "Thành tiền": qty*price
        })
        st.success("Đã thêm!")

    if st.session_state.cart:
        cart_df = pd.DataFrame(st.session_state.cart)
        display_cart = cart_df.copy()
        display_cart["Đơn giá"] = display_cart["Đơn giá"].apply(format_vnd)
        display_cart["Thành tiền"] = display_cart["Thành tiền"].apply(format_vnd)

        st.subheader("📋 Giỏ hàng hiện tại")
        st.dataframe(display_cart, use_container_width=True)

        total = cart_df["Thành tiền"].sum()
        st.metric("💰 Tổng tiền", format_vnd(total))

        if st.button("🧾 Thanh toán"):
            invoice_id = f"HD{len(invoices['Mã hóa đơn'].unique())+1:03}"
            now = datetime.now()

            for item in cart_df.to_dict("records"):
                invoices.loc[len(invoices)] = [
                    invoice_id,
                    item["Sản phẩm"],
                    item["Số lượng"],
                    item["Đơn giá"],
                    item["Thành tiền"],
                    now
                ]

            invoices.to_csv("invoice_details.csv", index=False)
            st.session_state.cart = []
            st.success("Thanh toán thành công!")
            st.rerun()

# =====================================================
# 3️⃣ HÓA ĐƠN
# =====================================================
elif menu == "📜 Hóa đơn":

    st.header("📜 Danh sách hóa đơn")

    if invoices.empty:
        st.warning("Chưa có hóa đơn.")
    else:
        invoice_ids = invoices["Mã hóa đơn"].unique()
        selected_id = st.selectbox("Chọn hóa đơn", invoice_ids)

        invoice_df = invoices[
            invoices["Mã hóa đơn"]==selected_id
        ]

        display_invoice = invoice_df.copy()
        display_invoice["Đơn giá"] = display_invoice["Đơn giá"].apply(format_vnd)
        display_invoice["Thành tiền"] = display_invoice["Thành tiền"].apply(format_vnd)

        st.dataframe(display_invoice, use_container_width=True)

        total = invoice_df["Thành tiền"].sum()
        st.metric("Tổng hóa đơn", format_vnd(total))

        if st.button("❌ Xóa hóa đơn"):
            invoices = invoices[
                invoices["Mã hóa đơn"]!=selected_id
            ]
            invoices.to_csv("invoice_details.csv", index=False)
            st.success("Đã xóa!")
            st.rerun()

# =====================================================
# 4️⃣ THỐNG KÊ
# =====================================================
elif menu == "📊 Thống kê":

    st.header("📊 Báo cáo")

    total_revenue = invoices["Thành tiền"].sum()
    total_invoice = invoices["Mã hóa đơn"].nunique()

    col1, col2 = st.columns(2)
    col1.metric("💰 Doanh thu", format_vnd(total_revenue))
    col2.metric("🧾 Số hóa đơn", total_invoice)

    if not invoices.empty:
        revenue_by_product = invoices.groupby(
            "Sản phẩm"
        )["Thành tiền"].sum()

        st.bar_chart(revenue_by_product)