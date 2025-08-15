import streamlit as st 
import pandas as pd 
import numpy as np
import pickle
import plotly.express as px 
import plotly.graph_objects as go
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

# ---- set konfigurasi halaman ----
st.set_page_config(
    page_title='Dashboard Analisis Penjualan',
    # page_icon='',
    layout='wide',
    initial_sidebar_state='expanded'
)

# -- fungsi untuk memuat data --
@st.cache_data
def load_data():
    return pd.read_csv("data/superstore.csv")

# load data penjualan
df_sales = load_data()
df_sales.columns = df_sales.columns.str.lower().str.replace(' ', '_') # mengubah nama kolomnya agar snake case
df_sales['order_date'] = pd.to_datetime(df_sales['order_date'])

# load model -- nanti

# judul dashboard 
st.title("DASHBOARD RETAIL SUPERSTORE")
st.markdown("Dashboard interaktif ini menyediakan gambaran umum performa dan trend penjualan.")

st.markdown("---") # garis pembatas 

# Langsung set halaman ke Overview Dashboard
pilihan_halaman = "Overview Dashboard"

if pilihan_halaman == "Overview Dashboard":
    st.subheader("Overview Dashboard")
    # Tambahkan seluruh kode overview dashboard di sini
    st.write("Ringkasan Performa Penjualan")

# filter global (muncul untuk halaman overview dashboard)
if pilihan_halaman == "Overview Dashboard":
    st.sidebar.markdown("### Filter Dashboard")
    min_date = df_sales['order_date'].min().date()
    max_date = df_sales['order_date'].max().date()

    date_range = st.sidebar.date_input(
        "Pilih Rentang Tanggal",
        value=(min_date,max_date),
        min_value=min_date,
        max_value=max_date
    )

    if len(date_range) == 2:
        start_date_filter = pd.to_datetime(date_range[0])
        end_date_filter = pd.to_datetime(date_range[1])
        filtered_df = df_sales[(df_sales['order_date'] >= start_date_filter) &
                               (df_sales['order_date'] <= end_date_filter)]
    else: 
        # kalau filter date-nya belum tuntas
        filtered_df = df_sales 

# Filter segment pelanggan
selected_segments = st.sidebar.multiselect(
    "Pilih Segment Pelanggan:",
    options=df_sales['segment'].unique().tolist(),
    default=df_sales['segment'].unique().tolist()
)

filtered_df = filtered_df[filtered_df['segment'].isin(selected_segments)]

    # filter berdasarkan  
selected_regions = st.sidebar.multiselect(
        "Pilih Region:",
        options=df_sales['region'].unique().tolist(),
        default=df_sales['region'].unique().tolist()
    )

filtered_df = filtered_df[filtered_df['region'].isin(selected_regions)]

# filter kategori produk 
selected_categories = st.sidebar.multiselect(
        "Pilih Kategori Produk:",
        options=df_sales['category'].unique().tolist(),
        default=df_sales['category'].unique().tolist()
    )

filtered_df = filtered_df[filtered_df['category'].isin(selected_categories)]

# --- METRIK UTAMA ---
total_sales = filtered_df['sales'].sum() if 'sales' in filtered_df else 0
total_profit = filtered_df['profit'].sum() if 'profit' in filtered_df else 0
total_orders = filtered_df['order_id'].nunique()
total_customers = filtered_df['customer_id'].nunique()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Penjualan", f"${total_sales:,.2f}")
col2.metric("Total Profit", f"${total_profit:,.2f}")
col3.metric("Total Pesanan", total_orders)
col4.metric("Total Pelanggan", total_customers)

# Membuat dua kolom untuk visualisasi
col_vis1, col_vis2 = st.columns(2)

# Visualisasi Jumlah Pelanggan per Segment 
with col_vis1:
    st.write("##### Distribusi Jumlah Pelanggan per Segment")
    customers_by_segment = filtered_df.groupby('segment')['customer_id'].nunique().reset_index(name='Jumlah Pelanggan')
    
    fig_customers = px.pie(
        customers_by_segment,
        names='segment',  
        values='Jumlah Pelanggan',
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    # Tampilkan persentase 
    fig_customers.update_traces(
        textinfo='percent+value', 
        hovertemplate='%{value} pelanggan (%{percent})<extra></extra>'  
    )
    st.plotly_chart(fig_customers, use_container_width=True)

# Visualisasi Jumlah Pesanan per Segment 
with col_vis2:
    st.write("##### Distribusi Jumlah Pesanan per Segment")
    orders_by_segment = filtered_df.groupby('segment')['order_id'].nunique().reset_index(name='Jumlah Pesanan')
    
    fig_orders = px.pie(
        orders_by_segment,
        names='segment',
        values='Jumlah Pesanan',
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_orders.update_traces(
        textinfo='percent+value',
        hovertemplate='%{value} pesanan (%{percent})<extra></extra>'
    )
    st.plotly_chart(fig_orders, use_container_width=True)

# Tipe pengiriman yang paling sering digunakan
ship_counts = (
    filtered_df.groupby("ship_mode")["order_id"]
    .nunique()  # hitung jumlah order 
    .reset_index()
    .rename(columns={"order_id": "jumlah_pesanan"})
)

# Buat Pie Chart
fig_ship_pie = px.pie(
    ship_counts,
    names="ship_mode",
    values="jumlah_pesanan",
    title="Tipe Pengiriman yang Paling Sering Digunakan",
    hole=0.4  
)

# Tampilkan label angka + persentase
fig_ship_pie.update_traces(
    textinfo='value+percent',
    textfont_size=14
)

st.plotly_chart(fig_ship_pie, use_container_width=True)

# Tren penjualan bulanan
sales_monthly = filtered_df.groupby(filtered_df['order_date'].dt.to_period('M')).sum(numeric_only=True).reset_index()
sales_monthly['order_date'] = sales_monthly['order_date'].astype(str)

fig_sales = px.line(
    sales_monthly,
    x='order_date',
    y='sales',
    title="Tren Penjualan Bulanan",
    text='sales'  # Menampilkan angka
)

# Atur format angka
fig_sales.update_traces(
    texttemplate='%{text:.2s}',  
    textposition='top center'
)
st.plotly_chart(fig_sales, use_container_width=True)

# Tren Penjualan Tahunan
filtered_df['order_date'] = pd.to_datetime(filtered_df['order_date'])

# Agregasi per tahun
sales_yearly = (
    filtered_df
    .assign(year=filtered_df['order_date'].dt.year)
    .groupby('year', as_index=False)
    .agg({'sales': 'sum'})
)

# Line chart 
fig_sales_year = px.line(
    sales_yearly,
    x='year',          
    y='sales',
    title="Tren Penjualan Tahunan",
    markers=True,
    text='sales'
)
fig_sales_year.update_traces(
    texttemplate='%{text:,.0f}',
    textposition='top center'
)

st.plotly_chart(fig_sales_year, use_container_width=True)

# Penjualan dan Profit berdasarkan Segment, Region, Tipe Pengiriman dan Kategori
st.subheader("Performa Penjualan dan Profit Lebih Detail")

# membuat 2 tabs
tab1, tab2 = st.tabs(["Penjualan per Tipe Pengiriman", "Penjualan per Region"])

# Data penjualan berdasarkan ship mode
sales_by_ship = filtered_df.groupby('ship_mode')['sales'].sum().reset_index()

# Chart ship mode
with tab1:
    fig_ship = px.bar(
        sales_by_ship,
        x='ship_mode',
        y='sales',
        title='Total Penjualan per Tipe Pengiriman',
        color='ship_mode',
        text='sales'  
    )

    # Format angka
    fig_ship.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    st.plotly_chart(fig_ship, use_container_width=True)

# Data penjualan berdasarkan region
sales_by_region = filtered_df.groupby('region')['sales'].sum().reset_index()

# Chart region
with tab2:
    fig_region = px.bar(
        sales_by_region,
        x='region',
        y='sales',
        title="Total Penjualan per Region",
        color='region',
        text='sales' 
    )
    fig_region.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    st.plotly_chart(fig_region, use_container_width=True)

# Profit dan Sales per segment
segment_stats = (
    filtered_df.groupby('segment')
    .agg({"profit": "sum", "sales": "sum"})
    .reset_index()
    .sort_values(by="sales", ascending=False)
)

# Ubah ke format long untuk plotly
segment_long = segment_stats.melt(
    id_vars="segment",
    value_vars=["profit", "sales"],
    var_name="Metric",
    value_name="Value"
)

# Visualisasi
fig_segment = px.bar(
    segment_long,
    x="segment",
    y="Value",
    color="Metric",
    barmode="group",
    text=segment_long["Value"],  # angka asli
    title="Profit & Penjualan per Segment"
)

# Tampilkan angka lengkap di atas bar
fig_segment.update_traces(
    texttemplate='%{text:,.0f}',  # format angka ribuan penuh
    textposition='outside'
)

fig_segment.update_layout(
    yaxis_title="Total",
    xaxis_title="Segment",
    legend_title="Metric"
)

st.plotly_chart(fig_segment, use_container_width=True)

# Profit & Penjualan per Region
region_stats = (
    filtered_df.groupby('region')
    .agg({"profit": "sum", "sales": "sum"})
    .reset_index()
    .sort_values(by="sales", ascending=False)
)

# Ubah ke format long untuk plotly
region_long = region_stats.melt(
    id_vars="region",
    value_vars=["profit", "sales"],
    var_name="Metric",
    value_name="Value"
)

# Visualisasi
fig_region = px.bar(
    region_long,
    x="region",
    y="Value",
    color="Metric",
    barmode="group",
    text=region_long["Value"],  
    title="Profit & Penjualan per Region"
)

# Tampilkan angka di bar
fig_region.update_traces(
    texttemplate='%{text:,.0f}',  # format angka ribuan 
    textposition='outside'
)

fig_region.update_layout(
    yaxis_title="Total",
    xaxis_title="Wilayah"
)

st.plotly_chart(fig_region, use_container_width=True)

# Profit dan Sales per kategori
category_stats = (
    filtered_df.groupby('category')
    .agg({"profit": "sum", "sales": "sum"})
    .reset_index()
    .sort_values(by="sales", ascending=False)
)

# Ubah ke format long untuk plotly
category_long = category_stats.melt(
    id_vars="category",
    value_vars=["profit", "sales"],
    var_name="Metric",
    value_name="Value"
)

# Visualisasi
fig_category = px.bar(
    category_long,
    x="category",
    y="Value",
    color="Metric",
    barmode="group",
    text=category_long["Value"],  
    title="Profit & Penjualan per Kategori"
)

# Tampilkan angka di atas bar
fig_category.update_traces(
    texttemplate='%{text:,.0f}',  
    textposition='outside'
)

fig_category.update_layout(
    yaxis_title="Total",
    xaxis_title="Kategori"
)

st.plotly_chart(fig_category, use_container_width=True)

# Top 10 Produk berdasarkan profit dan penjualan
prod_stats = (
    filtered_df
    .groupby("product_name", as_index=False)
    .agg({"sales": "sum", "profit": "sum"})
)

# Ambil top 10 berdasarkan sales
top10_products = prod_stats.nlargest(10, "sales")

# Urutkan dari terbesar ke terkecil 
top10_products = top10_products.sort_values("sales", ascending=True)  

# Ubah ke format long
top10_long = top10_products.melt(
    id_vars="product_name",
    value_vars=["sales", "profit"],
    var_name="Metric",
    value_name="Value"
)

# Plot horizontal bar chart
fig = px.bar(
    top10_long,
    y="product_name",
    x="Value",
    color="Metric",
    barmode="group",
    text=top10_long["Value"],
    title="Top 10 Produk Terlaris berdasarkan Sales & Profit"
)

# Angka 
fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')

fig.update_layout(
    yaxis_title="Produk",
    xaxis_title="Total",
    margin=dict(l=350, r=100, t=40, b=20),  
    height=700,  
    legend_title_text="Metrik"
)

st.plotly_chart(fig, use_container_width=True)