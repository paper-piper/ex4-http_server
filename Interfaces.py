import os
from PIL import Image


def parse_query_params(query_string):
    params = query_string.split('&')
    params_dict = {}
    for param in params:
        key, value = param.split('=')
        params_dict[key] = value
    return params_dict


def calculate_next(query_string):
    try:
        num = int(query_string.split('=')[1])
        response = str(num + 1)
        http_header = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"
    except (ValueError, IndexError):
        http_header = "HTTP/1.1 400 Bad Request\r\n\r\n"
        response = ""

    http_response = http_header + response
    return http_response


def calculate_area(query_string):
    try:
        parameters = parse_query_params(query_string)
        height = float(parameters['height'])
        width = float(parameters['width'])
        response = str(height * width / 2)
        http_header = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"
    except (KeyError, ValueError,):
        http_header = "HTTP/1.1 400 Bad Request\r\n\r\n"
        response = ""

    http_response = http_header + response
    return http_response


def save_image(image_paramters):
    """
    save an image in the "Images" folder
    :param image_paramters: a tuple of the image name (0) and the image bytes (1)
    :return:
    """
    image_name = image_paramters[0]
    image_bytes = image_paramters[1]
    # Create the "Images" folder if it doesn't exist
    images_folder = os.path.join(os.path.dirname(__file__), "Images")
    os.makedirs(images_folder, exist_ok=True)

    # Construct the file path for the new image
    image_path = os.path.join(images_folder, image_name)

    # Open the image using PIL
    with Image.open(io.BytesIO(image_bytes)) as img:
        # Save the image to the specified path
        img.save(image_path)

    print(f"Image saved at: {image_path}")


