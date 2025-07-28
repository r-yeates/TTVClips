import logging

# Set up the logger
logger = logging.getLogger("TTVClips")
logger.setLevel(logging.DEBUG)

# Create a file handler with UTF-8 encoding and set its level to DEBUG
file_handler = logging.FileHandler('config/app.log', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

# Create a formatter and attach it to the file handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)

# Define custom print functions
def print_header(header_text):
    # Clean text for logging (remove Unicode characters that might cause issues)
    clean_text = header_text.replace('✓', '[SUCCESS]').replace('✗', '[FAILED]')
    logger.info(clean_text)
    print(f"\u001b[34m[TTVClips][INFO]\u001b[0m {header_text}")

def print_error(error_text):
    clean_text = error_text.replace('✓', '[SUCCESS]').replace('✗', '[FAILED]')
    logger.error(clean_text)
    print(f"\u001b[31m[TTVClips][ERROR]\u001b[0m {error_text}")

def print_success(success_text):
    clean_text = success_text.replace('✓', '[SUCCESS]').replace('✗', '[FAILED]')
    logger.info(clean_text)
    print(f"\u001b[32m[TTVClips][SUCCESS]\u001b[0m {success_text}")

