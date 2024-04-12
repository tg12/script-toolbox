""" Description:
This script extracts metadata from image files and returns it as a pandas dataframe. It uses the piexif library to extract metadata from the images, and the geopy library to convert GPS coordinates to place names.

Disclaimer: The information and content provided by me, is for informational purposes only. All content provided is the property of @James12396379, and any use or distribution of this content should include proper attribution to @James12396379.

 """

# Author: James Sawyer
# Email: githubtools@jamessawyer.co.uk
# Website: http://www.jamessawyer.co.uk/
# Twitter: https://twitter.com/James12396379

import os

import pandas as pd
import piexif
from geopy.geocoders import Nominatim
from PIL import Image
from tabulate import tabulate


# allows Pillow to open and manipulate images in the HEIF (i.e. HEIC) format
from pillow_heif import register_heif_opener
register_heif_opener()


def extract_metadata(dir_path):
    """
    Extracts the metadata from all the image files in the specified directory and
    returns it as a pandas dataframe.

    Args:
        dir_path (str): The path to the directory containing the image files.

    Returns:
        pandas.DataFrame: A dataframe containing the metadata of all the image files.
    """
    metadata_list = []
    for file in os.listdir(dir_path):
        print("[+] Processing {}".format(file))
        if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png") or file.endswith(".tiff") or file.endswith(".bmp") or file.endswith(".gif") or file.endswith(
                ".webp") or file.endswith(".psd") or file.endswith(".raw") or file.endswith(".cr2") or file.endswith(".nef") or file.endswith(".heic") or file.endswith(".sr2"):
            print("[+] Extracting metadata from {}".format(file))
            try:
                with Image.open(os.path.join(dir_path, file)) as img:
                    exif_data = piexif.load(img.info["exif"])
                    print("[+] Metadata extracted from {}".format(file))

                    # Extract GPS latitude, longitude, and altitude data
                    gps_latitude = exif_data['GPS'][piexif.GPSIFD.GPSLatitude]
                    gps_latitude_ref = exif_data['GPS'][piexif.GPSIFD.GPSLatitudeRef]
                    gps_longitude = exif_data['GPS'][piexif.GPSIFD.GPSLongitude]
                    gps_longitude_ref = exif_data['GPS'][piexif.GPSIFD.GPSLongitudeRef]
                    gps_altitude = exif_data['GPS'][piexif.GPSIFD.GPSAltitude]
                    gps_altitude_ref = exif_data['GPS'][piexif.GPSIFD.GPSAltitudeRef]

                    # Convert GPS latitude and longitude data to decimal degrees
                    gps_latitude_decimal = gps_to_decimal(
                        gps_latitude, gps_latitude_ref)
                    gps_longitude_decimal = gps_to_decimal(
                        gps_longitude, gps_longitude_ref)

                    metadata = {
                        'filename': file,
                        'gps_latitude': gps_latitude_decimal,
                        'gps_longitude': gps_longitude_decimal,
                        'gps_altitude': gps_altitude,
                        'gps_altitude_ref': gps_altitude_ref,
                        'make': exif_data['0th'][piexif.ImageIFD.Make],
                        'model': exif_data['0th'][piexif.ImageIFD.Model],
                        'software': exif_data['0th'][piexif.ImageIFD.Software],
                        'datetime': exif_data['0th'][piexif.ImageIFD.DateTime],
                        # 'exposure_time': exif_data['Exif'][piexif.ExifIFD.ExposureTime],
                        # 'f_number': exif_data['Exif'][piexif.ExifIFD.FNumber],
                        # 'iso_speed_ratings': exif_data['Exif'][piexif.ExifIFD.ISOSpeedRatings],
                        # 'focal_length': exif_data['Exif'][piexif.ExifIFD.FocalLength],
                        # 'focal_length_in_35mm_film': exif_data['Exif'][piexif.ExifIFD.FocalLengthIn35mmFilm],
                        # 'exposure_mode': exif_data['Exif'][piexif.ExifIFD.ExposureMode],
                        # 'white_balance': exif_data['Exif'][piexif.ExifIFD.WhiteBalance],
                        # 'metering_mode': exif_data['Exif'][piexif.ExifIFD.MeteringMode],
                        # 'flash': exif_data['Exif'][piexif.ExifIFD.Flash],
                        # 'exposure_program': exif_data['Exif'][piexif.ExifIFD.ExposureProgram],
                        # 'exif_version': exif_data['Exif'][piexif.ExifIFD.ExifVersion],
                        # 'date_time_original': exif_data['Exif'][piexif.ExifIFD.DateTimeOriginal],
                        # 'date_time_digitized': exif_data['Exif'][piexif.ExifIFD.DateTimeDigitized],
                        # 'components_configuration': exif_data['Exif'][piexif.ExifIFD.ComponentsConfiguration],
                        # 'compressed_bits_per_pixel': exif_data['Exif'][piexif.ExifIFD.CompressedBitsPerPixel],
                        # 'shutter_speed_value': exif_data['Exif'][piexif.ExifIFD.ShutterSpeedValue],
                        # 'aperture_value': exif_data['Exif'][piexif.ExifIFD.ApertureValue],
                        # 'brightness_value': exif_data['Exif'][piexif.ExifIFD.BrightnessValue],
                        # 'exposure_bias_value': exif_data['Exif'][piexif.ExifIFD.ExposureBiasValue],
                        # 'max_aperture_value': exif_data['Exif'][piexif.ExifIFD.MaxApertureValue],
                        # 'subject_distance': exif_data['Exif'][piexif.ExifIFD.SubjectDistance],
                        # 'metering_mode': exif_data['Exif'][piexif.ExifIFD.MeteringMode],
                        # 'light_source': exif_data['Exif'][piexif.ExifIFD.LightSource],
                        # 'flash': exif_data['Exif'][piexif.ExifIFD.Flash],
                        # 'focal_length': exif_data['Exif'][piexif.ExifIFD.FocalLength],
                        # 'subject_area': exif_data['Exif'][piexif.ExifIFD.SubjectArea],

                    }

                    print("-----------------------------")

                    metadata_list.append(metadata)
            except Exception as e:
                print("[!] Error processing {}: {}".format(file, str(e)))

    # Convert the metadata list to a pandas dataframe
    metadata_df = pd.DataFrame(metadata_list)

    return metadata_df


def gps_to_decimal(coord, ref):
    """
    Converts GPS coordinates to decimal degrees.

    Args:
        coord (tuple): A tuple containing the GPS coordinates.
        ref (str): The reference direction (e.g., N, S, E, W).

    Returns:
        float: The GPS coordinates in decimal degrees.
    """
    decimal = coord[0][0] / coord[0][1] + coord[1][0] / \
        (60 * coord[1][1]) + coord[2][0] / (3600 * coord[2][1])
    if ref in ['S', 'W']:
        decimal *= -1
    return decimal


def get_place_name(latitude, longitude):
    location = geolocator.reverse(f"{latitude}, {longitude}", exactly_one=True)
    if location is None:
        return None
    else:
        return location.address


if __name__ == "__main__":
    # Define the directory containing the image files
    dir_path = "PATH_TO_IMAGE_FILES"
    # Extract the metadata from the image files
    metadata_df = extract_metadata(dir_path)
    print("[+] Metadata extracted from all image files")
    print(metadata_df.columns)
    geolocator = Nominatim(user_agent="exif_location")
    metadata_df['place_name'] = metadata_df.apply(
        lambda row: get_place_name(
            row['gps_latitude'], row['gps_longitude']), axis=1)

    # Print the dataframe
    print(tabulate(metadata_df, headers="keys", tablefmt="psql"))
