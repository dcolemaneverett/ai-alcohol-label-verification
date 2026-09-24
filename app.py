import time
import streamlit as st
from PIL import Image

from ocr import extract_text
from validators import validate_brand, validate_class_type, validate_abv, validate_net_contents, validate_warning

st.set_page_config(page_title="Alcohol Label Verification Prototype", page_icon="✅", layout="wide")
st.title("AI-Powered Alcohol Label Verification")
st.caption("Prototype decision-support tool for alcohol beverage label review. Human review remains the final authority.")

with st.sidebar:
    st.header("Application Data")
    brand = st.text_input("Brand name")
    class_type = st.text_input("Class / type")
    abv = st.text_input("Alcohol content", placeholder="Example: 45%")
    net_contents = st.text_input("Net contents", placeholder="Example: 750 mL")

st.subheader("1. Upload label image")
uploaded = st.file_uploader("Upload a PNG, JPG, or JPEG label image", type=["png", "jpg", "jpeg"])

if uploaded:
    image = Image.open(uploaded).convert("RGB")
    st.image(image, caption="Uploaded label", use_container_width=True)

    if st.button("Analyze label", type="primary"):
        start = time.perf_counter()
        with st.spinner("Reading and checking the label..."):
            extracted_text = extract_text(image)
            results = [
                validate_brand(brand, extracted_text),
                validate_class_type(class_type, extracted_text),
                validate_abv(abv, extracted_text),
                validate_net_contents(net_contents, extracted_text),
                validate_warning(extracted_text),
            ]
        elapsed = time.perf_counter() - start

        st.subheader("2. Verification Results")
        st.metric("Processing time", f"{elapsed:.2f} seconds")

        for result in results:
            icon = {"MATCH": "✅", "NEEDS REVIEW": "⚠️", "MISMATCH": "❌"}.get(result["status"], "ℹ️")
            with st.container(border=True):
                st.markdown(f"### {icon} {result['field']}: {result['status']}")
                st.write(result["reason"])

        st.subheader("3. OCR Evidence")
        st.text_area("Extracted label text", extracted_text, height=260)
        st.info("Prototype note: This tool supports compliance review. It does not approve or reject a regulatory application.")
else:
    st.info("Upload a label image to begin.")
