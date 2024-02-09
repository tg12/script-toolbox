""" THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE AND
NON-INFRINGEMENT. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR ANYONE
DISTRIBUTING THE SOFTWARE BE LIABLE FOR ANY DAMAGES OR OTHER LIABILITY,
WHETHER IN CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE. """

# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0621, W1203, C0103, C0301, W1201
# C0116: Missing function or method docstring
# W0621: Redefining name %r from outer scope (line %s)
# W1203: Use % formatting in logging functions and pass the % parameters as arguments
# C0103: Constant name "%s" doesn't conform to UPPER_CASE naming style
# C0301: Line too long (%s/%s)
# W1201: Specify string format arguments as logging function parameters

import logging
import os
from pathlib import Path
from typing import Union

from PIL import Image
from PyPDF2 import PdfFileReader, PdfFileWriter

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def remove_metadata(file_path: Union[str, Path]):
    """
    Remove metadata from the given file.
    """
    try:
        extension = file_path.suffix.lower()

        if extension == ".pdf":
            # Remove metadata from PDF files
            pdf_reader = PdfFileReader(str(file_path))
            pdf_writer = PdfFileWriter()

            for page_num in range(pdf_reader.numPages):
                pdf_writer.add_page(pdf_reader.getPage(page_num))

            with open(str(file_path), "wb") as output_pdf:
                pdf_writer.write(output_pdf)

        elif extension in [".jpg", ".jpeg", ".jpe", ".jfif", ".mp4"]:
            # Remove metadata from JPEG files
            image = Image.open(str(file_path))
            image_info = image.info
            logging.info(f"Metadata in {file_path}: {image_info}")
            data = list(image.getdata())
            image_without_exif = Image.new(image.mode, image.size)
            image_without_exif.putdata(data)
            image_without_exif.save(str(file_path))

        else:
            logging.warning(f"Metadata removal is not supported for {extension} files.")

    except Exception as e:
        logging.error(f"Failed to remove metadata from {file_path}: {e}")


def main(directory_path: Union[str, Path]):
    """
    Iterate through files in the given directory and remove metadata.
    """
    try:
        directory = Path(directory_path)

        if directory.is_dir():
            for file in directory.iterdir():
                if file.is_file():
                    logging.info(f"Removing metadata from {file}")
                    remove_metadata(file)
        else:
            logging.error("Invalid directory path provided.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    directory_path = input("Enter the directory path: ")
    main(directory_path)
