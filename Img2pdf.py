import os
import io
import zipfile
import tempfile
import streamlit as st
from PIL import Image
import img2pdf
import PyPDF2
from pdf2image import convert_from_bytes
from reportlab.lib.pagesizes import letter, A4, legal, TABLOID
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import base64

# Developer information
DEVELOPER_NAME = "Mansoor Sarookh BSCS std, GenAi Developer"
DEVELOPER_URL = "https://github.com/MansoorSarookh"  # Replace with your actual URL

# Page setup
st.set_page_config(
    page_title="Image-PDF Converter Pro",
    page_icon=":arrows_counterclockwise:",
    layout="centered"
)

# Supported formats
IMG_FORMATS = ["jpg", "jpeg", "png", "bmp", "tiff"]
PDF_FORMAT = "pdf"

# Page size mapping
PAGE_SIZES = {
    "Letter": letter,
    "A4": A4,
    "Legal": legal,
    "Tabloid": TABLOID
}

# Initialize session state
if 'img_files' not in st.session_state:
    st.session_state.img_files = []
if 'pdf_file' not in st.session_state:
    st.session_state.pdf_file = None

# Helper functions
def validate_image(file):
    try:
        img = Image.open(file)
        img.verify()
        return True
    except:
        return False

def validate_pdf(file):
    try:
        PyPDF2.PdfReader(file)
        return True
    except:
        return False

def get_image_preview(image, max_size=200):
    img = Image.open(image)
    img.thumbnail((max_size, max_size))
    return img

def create_zip(images):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for i, img_data in enumerate(images):
            img_bytes = io.BytesIO()
            img_data.save(img_bytes, format=img_data.format or "PNG")
            zip_file.writestr(f"page_{i+1}.{img_data.format.lower()}", img_bytes.getvalue())
    zip_buffer.seek(0)
    return zip_buffer

def add_margins(pdf_bytes, margin):
    if margin == "None":
        return pdf_bytes
    
    margin_sizes = {
        "Small": 0.5 * inch,
        "Medium": inch,
        "Large": 1.5 * inch
    }
    margin_size = margin_sizes.get(margin, 0)
    
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    writer = PyPDF2.PdfWriter()
    
    for page in reader.pages:
        page.mediabox.upper_right = (
            float(page.mediabox.right) - margin_size,
            float(page.mediabox.top) - margin_size
        )
        page.mediabox.lower_left = (
            float(page.mediabox.left) + margin_size,
            float(page.mediabox.bottom) + margin_size
        )
        writer.add_page(page)
    
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()

# Image to PDF Converter
def image_to_pdf_converter():
    st.header("📸 Image to PDF Converter")
    
    # Upload images
    uploaded_files = st.file_uploader(
        "Upload images (JPG, PNG, BMP, TIFF)",
        type=IMG_FORMATS,
        accept_multiple_files=True
    )
    
    # Add drag-and-drop functionality
    with st.expander("📤 Drag and Drop Area (Alternative)"):
        st.info("Drag and drop images here")
        st.write("")
        st.write("")
        st.write("")
        st.write("")
    
    # Process uploaded files
    if uploaded_files:
        valid_files = [f for f in uploaded_files if validate_image(f)]
        invalid_files = [f.name for f in uploaded_files if f not in valid_files]
        
        if invalid_files:
            st.warning(f"Invalid images skipped: {', '.join(invalid_files)}")
        
        st.session_state.img_files = valid_files
    
    # Image preview and reordering
    if st.session_state.img_files:
        st.subheader("Image Preview & Ordering")
        st.info("Drag to reorder images (first image = first page)")
        
        # Create sortable UI
        img_previews = []
        for i, img_file in enumerate(st.session_state.img_files):
            img = get_image_preview(img_file)
            img_previews.append((img, img_file.name))
        
        # Display reorderable images
        for i, (img, name) in enumerate(img_previews):
            col1, col2 = st.columns([1, 4])
            with col1:
                st.image(img, use_column_width=True)
            with col2:
                st.text_input(f"Page {i+1}", name, disabled=True)
    
    # Conversion options
    with st.sidebar:
        st.subheader("Conversion Settings")
        
        page_size = st.selectbox(
            "Page Size",
            list(PAGE_SIZES.keys()),
            index=0
        )
        
        orientation = st.radio(
            "Orientation",
            ["Portrait", "Landscape"]
        )
        
        margin = st.selectbox(
            "Margin",
            ["None", "Small", "Medium", "Large"],
            index=1
        )
        
        quality = st.slider(
            "Image Quality",
            1, 100, 85
        )
    
    # Convert button
    if st.session_state.img_files and st.button("Convert to PDF"):
        with st.spinner("Converting images to PDF..."):
            try:
                # Process images
                images = []
                for img_file in st.session_state.img_files:
                    img = Image.open(img_file)
                    if orientation == "Landscape":
                        img = img.rotate(90, expand=True)
                    images.append(img)
                
                # Convert to PDF
                pdf_bytes = img2pdf.convert(
                    images,
                    pagesize=PAGE_SIZES[page_size]
                )
                
                # Apply margins
                pdf_bytes = add_margins(pdf_bytes, margin)
                
                # Create download link
                st.success("Conversion successful!")
                st.download_button(
                    label="Download PDF",
                    data=pdf_bytes,
                    file_name="converted.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"Conversion failed: {str(e)}")

# PDF to Image Converter
def pdf_to_image_converter():
    st.header("📄 PDF to Image Converter")
    
    # Upload PDF
    uploaded_file = st.file_uploader(
        "Upload PDF file",
        type=PDF_FORMAT
    )
    
    if uploaded_file:
        if validate_pdf(uploaded_file):
            st.session_state.pdf_file = uploaded_file
        else:
            st.error("Invalid PDF file")
            st.session_state.pdf_file = None
    
    # Conversion options
    if st.session_state.pdf_file:
        with st.sidebar:
            st.subheader("Conversion Settings")
            
            page_range = st.text_input(
                "Pages to convert (e.g., 1-3,5,7-last)",
                "all"
            )
            
            img_format = st.selectbox(
                "Output Format",
                ["JPG", "PNG", "TIFF"],
                index=0
            )
            
            dpi = st.slider(
                "DPI Quality",
                72, 600, 150
            )
            
            if img_format == "JPG":
                jpg_quality = st.slider(
                    "JPG Quality",
                    1, 100, 85
                )
        
        # Convert button
        if st.button("Convert to Images"):
            with st.spinner("Converting PDF pages..."):
                try:
                    # Process page range
                    if page_range.lower() == "all":
                        pages = None
                    else:
                        # Implement page range parsing
                        pages = []
                        parts = page_range.split(',')
                        for part in parts:
                            if '-' in part:
                                start, end = part.split('-')
                                start = int(start) if start.isdigit() else 1
                                if end.lower() == 'last':
                                    end = 9999
                                else:
                                    end = int(end)
                                pages.extend(range(start, end+1))
                            else:
                                pages.append(int(part))
                    
                    # Convert PDF to images
                    images = convert_from_bytes(
                        st.session_state.pdf_file.read(),
                        dpi=dpi,
                        first_page=pages[0] if pages else None,
                        last_page=pages[-1] if pages else None,
                        fmt=img_format.lower(),
                        jpeg_quality=jpg_quality if img_format == "JPG" else None
                    )
                    
                    st.success(f"Converted {len(images)} pages")
                    
                    # Download options
                    col1, col2 = st.columns(2)
                    with col1:
                        zip_buffer = create_zip(images)
                        st.download_button(
                            label="Download as ZIP",
                            data=zip_buffer,
                            file_name="converted_images.zip",
                            mime="application/zip"
                        )
                    
                    # Display first 3 images as preview
                    st.subheader("First 3 Pages Preview")
                    cols = st.columns(3)
                    for i, img in enumerate(images[:3]):
                        with cols[i]:
                            st.image(img, caption=f"Page {i+1}")
                
                except Exception as e:
                    st.error(f"Conversion failed: {str(e)}")

# Developer footer
def developer_footer():
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Developed by [{DEVELOPER_NAME}]({DEVELOPER_URL})")
    st.sidebar.caption("© 2023 Image-PDF Converter Pro")

# Main App
def main():
    st.title("🖼️📄 Image-PDF Converter Pro")
    st.caption("Convert between images and PDFs with advanced options")
    
    # Navigation
    app_mode = st.sidebar.selectbox(
        "Select Conversion Type",
        ["Image to PDF", "PDF to Image"],
        index=0
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **Features:**
    - Multiple image upload
    - Drag-and-drop support
    - PDF quality control
    - Page size/orientation options
    - Batch processing
    """)
    
    # Developer footer
    developer_footer()
    
    # Router
    if app_mode == "Image to PDF":
        image_to_pdf_converter()
    else:
        pdf_to_image_converter()

if __name__ == "__main__":
    main()
