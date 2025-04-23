import tkinter as tk
from tkinter import filedialog
from pdfminer.high_level import extract_text

from utils.pdf_to_txt_util import replace_fractions


def select_file_and_extract_text(verbose=False):
    """
    Opens a file explorer to select a file and processes it into a string.
    Supports .txt, .md, and .pdf files.
    """
    # Initialize Tkinter and hide the main window.
    root = tk.Tk()
    root.withdraw()

    # Open a file explorer dialog to select a file.
    file_path = filedialog.askopenfilename(
        title="Select a File",
        filetypes=[("Supported Files", ("*.txt", "*.md", "*.pdf"))]
    )

    if not file_path:
        if verbose:
            print("No file selected.")
        return None

    file_content = ""
    if file_path.lower().endswith(".pdf"):
        if extract_text is None:
            raise ImportError("pdfminer.six is required to process PDF files. Install it using 'pip install pdfminer.six'.")
        # Extract text from the PDF and process fractions.
        if verbose:
            print("Extracting text from PDF...", end=" ")
        file_content = extract_text(file_path)
        file_content = replace_fractions(file_content)
        if verbose:
            print("done")
    else:
        # Read text or markdown files.
        with open(file_path, "r", encoding="utf-8") as file:
            file_content = file.read()

    return file_content
