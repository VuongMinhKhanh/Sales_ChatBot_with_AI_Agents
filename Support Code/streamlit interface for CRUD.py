import streamlit as st
import weaviate
import os
import re
import difflib
import requests
from bs4 import BeautifulSoup

os.environ["OPENAI_API_KEY"] = ""
os.environ["WCD_DEMO_URL"] = ""
os.environ["WCD_DEMO_AD_KEY"] = ""

weaviate_client = weaviate.Client(
    url=os.environ["WCD_DEMO_URL"],
    auth_client_secret=weaviate.auth.AuthApiKey(api_key=os.environ["WCD_DEMO_AD_KEY"]),
    additional_headers={"X-OpenAI-Api-Key": os.environ.get("OPENAI_API_KEY")}
)
collection_name = "TestCollection"
collection = weaviate_client.collections.get(collection_name)

# Function to scrape product details from a given link
def scrape_product_details(product_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(product_url, headers=headers)
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.content, 'html.parser')

    product_details = {
        "name": soup.find('h1').get_text(strip=True) if soup.find('h1') else "",
        "price": soup.find('b', class_='bk-product-price').get_text(strip=True) if soup.find('b', class_='bk-product-price') else "",
        "availability": "In stock" if "còn" in soup.get_text().lower() else "Out of stock",
        "introduction": soup.find('div', class_='dd_nb').get_text(strip=True) if soup.find('div', class_='dd_nb') else "",
        "details": soup.find('div', id='content_tab_bottom').get_text(strip=True) if soup.find('div', id='content_tab_bottom') else "",
        "main_image": soup.find('img', class_='bk-product-image')['src'] if soup.find('img', class_='bk-product-image') else "",
        "gallery_links": [img['src'] for img in soup.find_all('div', id='content_tab_bottom')[0].find_all('img') if img.get('src')] if soup.find_all('div', id='content_tab_bottom') else []
    }
    return product_details

# Initialize session state
if 'new_product' not in st.session_state:
    st.session_state['new_product'] = {}
if 'gallery_links' not in st.session_state:
    st.session_state['gallery_links'] = []

st.title("Weaviate ChatBot Product Manager")

operation = st.sidebar.selectbox("Choose Operation", ["Create Product", "Update Product"])

if operation == "Create Product":
    st.sidebar.header("Create New Product")
    new_product_url = st.sidebar.text_input("Enter Product URL to Scrape Details:")
    if st.sidebar.button("Scrape Product Details") and new_product_url:
        product_details = scrape_product_details(new_product_url)
        st.session_state['new_product'] = product_details
        st.session_state['gallery_links'] = product_details.get("gallery_links", [])

    st.header("New Product Details")
    product = st.session_state['new_product']

    new_ten = st.text_input("Tên *", product.get("name", ""))
    new_gia = st.text_input("Giá *", product.get("price", ""))
    new_link_anh = st.text_input("Link ảnh *", product.get("main_image", ""))
    new_link_san_pham = st.text_input("Link sản phẩm *", new_product_url)
    new_tinh_trang = st.selectbox("Tình trạng *", ["In stock", "Out of stock"], index=0 if product.get("availability") == "In stock" else 1)
    new_gioi_thieu = st.text_area("Giới thiệu", product.get("introduction", ""))
    new_chi_tiet = st.text_area("Chi tiết", product.get("details", ""))

    st.subheader("Gallery Links")
    updated_gallery_links = []
    for i, link in enumerate(st.session_state['gallery_links']):
        updated_gallery_links.append(st.text_input(f"Tập link ảnh {i+1}", value=link, key=f"gallery_link_{i}"))

    if st.button("Add Another Gallery Link"):
        st.session_state['gallery_links'].append("")

    if st.button("Create Product"):
        if not new_ten or not new_gia or not new_link_anh or not new_link_san_pham:
            st.error("All required fields must be filled.")
        else:
            row_index = 0  # Replace with dynamic max row logic if needed
            data_objects = [
                {"text": f"Tên: {new_ten}", "row": row_index, "column": "Tên"},
                {"text": f"Giá: {new_gia}", "row": row_index, "column": "Giá"},
                {"text": f"Tình trạng: {'1.0' if new_tinh_trang == 'In stock' else '0.0'}", "row": row_index, "column": "Tình trạng"},
                {"text": new_gioi_thieu, "row": row_index, "column": "Giới thiệu"},
                {"text": new_chi_tiet, "row": row_index, "column": "Chi tiết"},
                {"text": f"Link ảnh: {new_link_anh}", "row": row_index, "column": "Link ảnh"},
                {"text": f"Link sản phẩm: {new_link_san_pham}", "row": row_index, "column": "Link sản phẩm"},
            ]
            for link in updated_gallery_links:
                if link.strip():
                    data_objects.append({"text": link.strip(), "row": row_index, "column": "Tập link ảnh"})

            try:
                for obj in data_objects:
                    pass
    if 'gallery_links' not in st.session_state:
        st.session_state['gallery_links'] = []

    # Editable product fields
    new_product = st.session_state['new_product']
    new_gallery_links = st.session_state['gallery_links']

    new_ten = st.text_input("Tên *", new_product.get("name", ""))
    new_gia = st.text_input("Giá *", new_product.get("price", ""))
    new_link_anh = st.text_input("Link ảnh *", new_product.get("main_image", ""))
    new_link_san_pham = st.text_input("Link sản phẩm *", new_product_url)
    new_tinh_trang = st.selectbox("Tình trạng *", ["In stock", "Out of stock"], index=0 if new_product.get("availability") == "In stock" else 1)
    new_gioi_thieu = st.text_area("Giới thiệu", new_product.get("introduction", ""))
    new_chi_tiet = st.text_area("Chi tiết", new_product.get("details", ""))

    # Gallery Links
    st.subheader("Gallery Links")
    for index, link in enumerate(new_gallery_links):
        new_gallery_links[index] = st.text_input(f"Tập link ảnh {index + 1}", value=link, key=f"gallery_link_{index}")

    # Button to add more gallery links
    add_link = st.button("Add Another Gallery Link")
    if add_link:
        new_gallery_links.append("")
        st.session_state['gallery_links'] = new_gallery_links

    # Button to create the product
    if st.button("Create Product"):
        if not new_ten or not new_gia or not new_link_anh or not new_link_san_pham or not new_tinh_trang:
            st.error("All fields except gallery links must be filled out before creating a product.")
        else:
            # Prepare the data to be inserted into Weaviate
            data_objects = [
                {"text": new_ten, "row": 0, "column": "Tên", "chunk_index": 0},
                {"text": new_gia, "row": 0, "column": "Giá", "chunk_index": 1},
                {"text": "1.0" if new_tinh_trang == "In stock" else "0.0", "row": 0, "column": "Tình trạng", "chunk_index": 2},
                {"text": new_gioi_thieu, "row": 0, "column": "Giới thiệu", "chunk_index": 3},
                {"text": new_chi_tiet, "row": 0, "column": "Chi tiết", "chunk_index": 4},
                {"text": new_link_anh, "row": 0, "column": "Link ảnh", "chunk_index": 5},
            ]
            for i, link in enumerate(new_gallery_links):
                if link:
                    data_objects.append({"text": link, "row": 0, "column": "Tập link ảnh", "chunk_index": 6 + i})

            try:
                for data_object in data_objects:
                    weaviate_client.data_object.create(data_object, class_name=collection_name)
                st.success("Product created successfully!")
            except Exception as e:
                st.error(f"An error occurred while creating the product: {e}")

# Close Weaviate client
weaviate_client.close()
