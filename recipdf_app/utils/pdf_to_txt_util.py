#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from pdfminer.high_level import extract_text


def replace_fractions(text):
    """
    Replace common Unicode fraction characters with their plain text equivalents.
    """
    fractions = {
        "½": "1/2",
        "¼": "1/4",
        "¾": "3/4",
        "⅓": "1/3",
        "⅔": "2/3",
        "⅛": "1/8",
        "⅜": "3/8",
        "⅝": "5/8",
        "⅞": "7/8",
    }
    for uni_frac, replacement in fractions.items():
        text = text.replace(uni_frac, replacement)
    return text


def convert_pdf_to_markdown(pdf_path, markdown_path):
    """
    Extract text from the PDF, replace fractions, and save as a Markdown file.
    """
    try:
        # Extract the text from the PDF file
        text = extract_text(pdf_path)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to extract text from PDF:\n{e}")
        return

    # Replace fraction characters
    text = replace_fractions(text)

    # If needed, you can add more conversion logic here to better format the text as Markdown.
    # For now, the script saves the plain text (with replaced fractions) as a Markdown file.
    try:
        with open(markdown_path, 'w', encoding='utf-8') as md_file:
            md_file.write(text)
        messagebox.showinfo("Success", f"Markdown file saved to:\n{markdown_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save markdown file:\n{e}")


def main():
    # Set up a basic tkinter root and hide the main window.
    root = tk.Tk()
    root.withdraw()

    # Prompt the user to select a PDF file.
    pdf_path = filedialog.askopenfilename(
        title="Select a PDF file",
        filetypes=[("PDF Files", "*.pdf")]
    )
    if not pdf_path:
        return  # Exit if no file is selected

    # Prompt the user to specify the output Markdown file.
    markdown_path = filedialog.asksaveasfilename(
        title="Save as Markdown",
        defaultextension=".md",
        filetypes=[("Markdown Files", "*.md"), ("All Files", "*.*")]
    )
    if not markdown_path:
        return  # Exit if no output path is specified

    # Convert the selected PDF to Markdown.
    convert_pdf_to_markdown(pdf_path, markdown_path)


if __name__ == "__main__":
    main()
