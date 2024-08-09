from PIL import Image
import os
import argparse
import re

def get_image_files(directory):
    # List of common image file extensions
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')

    # List to store image file paths
    image_files = []

    # Walk through the directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(image_extensions):
                image_files.append(os.path.join(root, file))

    image_files=sorted(image_files, key=sorter)
    return image_files

def sorter(file_name):
    # Extract the number from the filename using regex
    match = re.search(r'(\d+)\.png$', file_name)
    return int(match.group(1)) if match else float('inf')

def generate_sprite_sheet(cell_size, image_directory, target_file, images_per_row):
    images=[Image.open(image).resize(cell_size, Image.LANCZOS) for image in get_image_files(image_directory)]

    # Get the width and height of the images (assuming all images are the same size)
    img_width, img_height = images[0].size

    # Calculate the number of rows needed
    num_images = len(images)
    num_rows = (num_images + images_per_row - 1) // images_per_row

    # Create a new blank image for the sprite sheet
    sprite_sheet_width = images_per_row * img_width
    sprite_sheet_height = num_rows * img_height
    sprite_sheet = Image.new("RGBA", (sprite_sheet_width, sprite_sheet_height))

    # Paste each image into the sprite sheet
    for index, image in enumerate(images):
        x = (index % images_per_row) * img_width
        y = (index // images_per_row) * img_height
        sprite_sheet.paste(image, (x, y))

    # Save the sprite sheet
    sprite_sheet.save(target_file)

if __name__=="__main__":
    arg_parser = argparse.ArgumentParser(prog="sprite-atlas", description="sprite-atlas")
    arg_parser.add_argument("-d", "--directory", type=str, required=True, help="source directory")
    arg_parser.add_argument("-t", "--target_file", type=str, required=True, help="target file")
    arg_parser.add_argument("-s", "--cell_size", type=int, required=False, default=256, help="cell size. defaults is 256")
    args = arg_parser.parse_args()
    generate_sprite_sheet((args.cell_size,args.cell_size), args.directory, args.target_file, 5)