import pypdf
from loguru import logger


def extract_text_from_pdf(pdf_input) -> str:
    """
    Extracts and returns all text data from the given PDF.
    Accepts either a file path (str) or a file-like object (e.g., from Streamlit's uploader).

    Args:
        pdf_input (str or file-like): The path to the PDF file or a file-like object.

    Returns:
        str: The concatenated text extracted from all pages of the PDF.
    """
    logger.info("Extracting text from PDF")
    text = ""
    try:
        # If pdf_input is a string, treat it as a file path
        if isinstance(pdf_input, str):
            file_obj = open(pdf_input, "rb")
            close_file = True
        else:
            # Otherwise, assume it is a file-like object
            file_obj = pdf_input
            file_obj.seek(0)
            close_file = False

        reader = pypdf.PdfReader(file_obj)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        if close_file:
            file_obj.close()
    except Exception as e:
        print(f"Error reading PDF: {e}")
    logger.info("Done extracting text.")
    return text.strip()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pdf_extractor.py <pdf_file_path>")
    else:
        pdf_path = sys.argv[1]
        extracted_text = extract_text_from_pdf(pdf_path)
        print("Extracted Text:")
        print(extracted_text)
