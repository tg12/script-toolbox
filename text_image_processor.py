# Description: This script is used to extract text from images using pytesseract and PIL
# Author: James Sawyer
# Email: githubtools@jamessawyer.co.uk
# Website: http://www.jamessawyer.co.uk/

# Import the necessary libraries
from PIL import Image
import pytesseract
import os
import pandas as pd

# Set the directory containing the images
image_dir = '/Users/james/Desktop'

# Get a list of all the image files in the directory
image_files = [
    f for f in os.listdir(image_dir) if os.path.isfile(
        os.path.join(
            image_dir,
            f))]

# Create an empty Pandas dataframe to store the results
df = pd.DataFrame(columns=['filename', 'text'])

# Iterate over the list of image files
for file in image_files:
    try:
        # print the file name
        print ("Processing file: " + file)
        # Open the image and convert it to grayscale
        image = Image.open(os.path.join(image_dir, file))
        image = image.convert('L')

        # Apply Otsu's thresholding method to convert the image to black and
        # white
        threshold = 150
        image = image.point(lambda p: p > threshold and 255)

        # Use pytesseract to apply OCR to the image and extract the text
        text = pytesseract.image_to_string(image).rstrip()

        # split the text on newline characters and process each line separately
        lines = text.split('\n')

        # join the lines into a single string
        single_string = ' \n '.join(lines)


        # Store the text and filename in the dataframe
        df = df.append({'filename': file, 'text': single_string}, ignore_index=True)
    except BaseException as e:
        print ("Error processing file: " + file)
        print (e)
        pass

# Print the dataframe to the console
print(df)
