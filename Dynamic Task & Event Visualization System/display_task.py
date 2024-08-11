from PIL import Image, ImageDraw, ImageFont
import ctypes
import win32con
import time
import os
import datetime
import pytz
from fetch_events_oauth import fetch_events_and_tasks
import logging

logging.basicConfig(filename='app.log', level=logging.INFO)

def format_time(dt):
    """Format datetime object to string for display."""
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def create_image_with_text(current_events, upcoming_events, current_tasks, upcoming_tasks, output_path):
    try:
        width, height = 1920, 1080
        image = Image.new('RGB', (width, height), color='black')
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.truetype('arial.ttf', size=36)
            font_small = ImageFont.truetype('arial.ttf', size=28)
        except IOError:
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Define positions and spacing
        margin = 30
        vertical_spacing = 20
        section_width = (width - 3 * margin) // 2  # Divide width for tasks and events
        center_x = width // 2
        left_x = center_x - section_width // 2
        right_x = center_x + section_width // 2 + 100  # Shift tasks further right
        y_top = margin

        # Draw Current Events on Left Side
        draw.text((left_x, y_top), 'Current Events:', fill='yellow', font=font)
        y_current_events = y_top + 40

        if current_events:
            for event in current_events:
                draw.text((left_x, y_current_events), f"Event: {event['summary']}", fill='white', font=font)
                draw.text((left_x, y_current_events + 30), f"Start: {event.get('start', 'No Start Time')}", fill='white', font=font_small)
                draw.text((left_x, y_current_events + 60), f"End: {event.get('end', 'No End Time')}", fill='white', font=font_small)
                y_current_events += 90
        else:
            draw.text((left_x, y_current_events), 'No current events', fill='red', font=font)
            y_current_events += 30

        # Draw Upcoming Events on Left Side
        draw.text((left_x, y_current_events + vertical_spacing), 'Upcoming Events:', fill='yellow', font=font)
        y_upcoming_events = y_current_events + 40 + vertical_spacing

        if upcoming_events:
            for event in upcoming_events:
                draw.text((left_x, y_upcoming_events), f"Event: {event['summary']}", fill='white', font=font)
                draw.text((left_x, y_upcoming_events + 30), f"Starts at: {event.get('start', 'No Start Time')}", fill='white', font=font_small)
                y_upcoming_events += 60
        else:
            draw.text((left_x, y_upcoming_events), 'No upcoming events', fill='red', font=font)
            y_upcoming_events += 30

        # Draw Current Tasks on Right Side
        draw.text((right_x - 100, y_top), 'Current Tasks:', fill='cyan', font=font)  # Adjusted x position
        y_current_tasks = y_top + 40

        if current_tasks:
            for task in current_tasks:
                draw.text((right_x - 100, y_current_tasks), f"Task: {task['title']}", fill='white', font=font)  # Adjusted x position
                draw.text((right_x - 100, y_current_tasks + 30), f"Due: {task.get('due', 'No Due Date')}", fill='white', font=font_small)  # Adjusted x position
                y_current_tasks += 60
        else:
            draw.text((right_x - 100, y_current_tasks), 'No current tasks', fill='red', font=font)  # Adjusted x position
            y_current_tasks += 30

        # Draw Upcoming Tasks on Right Side
        draw.text((right_x - 100, y_current_tasks + vertical_spacing), 'Upcoming Tasks:', fill='cyan', font=font)  # Adjusted x position
        y_upcoming_tasks = y_current_tasks + 40 + vertical_spacing

        if upcoming_tasks:
            for task in upcoming_tasks:
                draw.text((right_x - 100, y_upcoming_tasks), f"Task: {task['title']}", fill='white', font=font)  # Adjusted x position
                draw.text((right_x - 100, y_upcoming_tasks + 30), f"Starts at: {task.get('due', 'No Due Date')}", fill='white', font=font_small)  # Adjusted x position
                y_upcoming_tasks += 60
        else:
            draw.text((right_x - 100, y_upcoming_tasks), 'No upcoming tasks', fill='red', font=font)  # Adjusted x position
            y_upcoming_tasks += 30

        image.save(output_path)
        logging.info(f"Image saved as {output_path}")
    except Exception as e:
        logging.error(f"Error creating image: {e}")

def set_wallpaper(image_path):
    try:
        abs_path = os.path.abspath(image_path)
        ctypes.windll.user32.SystemParametersInfoW(win32con.SPI_SETDESKWALLPAPER, 0, abs_path, win32con.SPIF_UPDATEINIFILE)
        logging.info(f"Wallpaper set to {abs_path}")
    except Exception as e:
        logging.error(f"Error setting wallpaper: {e}")

def main():
    while True:
        try:
            events_and_tasks = fetch_events_and_tasks()
            now = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))

            # Separate current and upcoming events and tasks
            current_events = []
            upcoming_events = []
            current_tasks = []
            upcoming_tasks = []

            for item in events_and_tasks:
                if 'start' in item and 'end' in item:
                    start_time = datetime.datetime.fromisoformat(item.get('start', '1970-01-01T00:00:00Z'))
                    end_time = datetime.datetime.fromisoformat(item.get('end', '1970-01-01T00:00:00Z'))
                    if start_time <= now <= end_time:
                        current_events.append(item)
                    else:
                        upcoming_events.append(item)
                elif 'title' in item:
                    due_time = datetime.datetime.fromisoformat(item.get('due', '1970-01-01T00:00:00Z'))
                    if due_time <= now:
                        current_tasks.append(item)
                    else:
                        upcoming_tasks.append(item)

            create_image_with_text(current_events, upcoming_events, current_tasks, upcoming_tasks, 'wallpaper.png')
            set_wallpaper('wallpaper.png')
            
        except Exception as e:
            logging.error(f"Error: {e}")
        
        time.sleep(10)

if __name__ == '__main__':
    main()
