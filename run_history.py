
import csv
import time
from datetime import datetime, timezone, timedelta
import pytz
from helpers import get_active_window_title
from models import Activity, TimeEntry
import pandas as pd
import math
import unidecode
from collections import defaultdict
import os

# === New: base paths (keep cross-platform) ===
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_DIR = os.path.join(CURRENT_DIR, "history")
os.makedirs(HISTORY_DIR, exist_ok=True)

def main():
    memoire_initiale = set()  # Initial set of activities
    temps_usage_initial = {}  # Initial usage time for each activity
    activities = []  # List to store activities
    actual_activity = get_active_window_title()  # Get the current active window title
    actual_time_entry_start_time = datetime.now(pytz.timezone("Europe/Paris"))  # Current time in Paris timezone
    last_activity_date = None  # Variable to store the date of the last activity
    print("Resume live:")
    print("")
    print("Activity\tTime Spent")
    print("________\t__________")
    memoire = set()  # Set to store activities for the current day
    temps_usage_combined = {}  # Dictionary to store combined usage time for each activity
    taille_sauvegarde = 30  # Number of days to keep the backup files
    cnt = 0  # Counter to keep track of the current backup file
    tm = -5  # Timer for periodic actions
    first_start = True  # Flag to check if it's the first run
    changes_needed = False  # Ensure defined before loop use

    try:
        while True:
            # Resume the current activity
            activities, actual_activity, actual_time_entry_start_time = resume_activity(activities,
                                                                                        actual_activity,
                                                                                        actual_time_entry_start_time)
            if len(activities):
                current_date = datetime.now(pytz.timezone("Europe/Paris")).date()
                separator = ["Activity", "Time spent day : " + current_date.strftime('%Y-%m-%d')]
                temps_usage_combined = {}
                memoire = set()

                if last_activity_date != current_date:
                    # Reset activities and start new day tracking
                    activities = []
                    actual_activity = get_active_window_title()
                    actual_time_entry_start_time = datetime.now(pytz.timezone("Europe/Paris"))
                    last_activity_date = None

                    if first_start:
                        # Find index for the backup file
                        idx, ch = find_index(current_date.strftime('%Y-%m-%d'), taille_sauvegarde)
                        cnt = idx
                        changes_needed = ch
                        if changes_needed:
                            # Load previous content to preserve ongoing day's data
                            sauvegarde_day = "sauvegardeDay" + str(cnt) + ".csv"
                            file_path = os.path.join(HISTORY_DIR, sauvegarde_day)
                            try:
                                with open(file_path, 'r', newline='', encoding='utf-8') as file:
                                    csv_reader = csv.reader(file)
                                    next(csv_reader)  # Skip the header line
                                    for row in csv_reader:
                                        activity_title = row[0]
                                        time_spent = parse_duration_string(row[1])
                                        memoire_initiale.add(activity_title)
                                        temps_usage_initial[activity_title] = time_spent
                            except FileNotFoundError:
                                # If file doesn't exist, no preserved state
                                pass
                        first_start = False
                    else:
                        cnt = (cnt + 1) % taille_sauvegarde
                        memoire_initiale = set()
                        temps_usage_initial = {}
                        changes_needed = False
                    last_activity_date = current_date

                if changes_needed:
                    for element in memoire_initiale:
                        memoire.add(element)
                    for key in temps_usage_initial:
                        temps_usage_combined[key] = temps_usage_initial[key]

                # Aggregate totals for activities observed in memory (preserve full titles)
                for activity in activities:
                    if activity.window_title is not None:
                        title = activity.window_title.strip()
                        # Keep full title, normalize accents only (no truncation)
                        title = unidecode.unidecode(title)

                        if title not in memoire:
                            memoire.add(title)
                            temps_usage_combined[title] = activity.get_time_spent()
                        else:
                            temps_usage_combined[title] += activity.get_time_spent()

                # Save the data for the current day into the ring file INSIDE history/
                sauvegarde_day = "sauvegardeDay" + str(cnt) + ".csv"
                file_path = os.path.join(HISTORY_DIR, sauvegarde_day)

                with open(file_path, "w", encoding="utf-8", newline='') as resume:
                    csv_writer = csv.writer(resume)
                    csv_writer.writerow(separator)
                    for key, value in temps_usage_combined.items():
                        csv_writer.writerow([key, value])

                # Periodic recap build (once per minute when tm==0)
                if tm == 0:
                    dates, all_activities, savingTable = resumeSavingFiles(taille_sauvegarde)
                    headers = ['date', 'total_daily_usage'] + list(all_activities)
                    savingData = []
                    for day in dates:
                        line = []
                        somme = 0
                        for activity_title in all_activities:
                            secs = savingTable[(day, activity_title)]
                            line.append(secs / 60)
                            somme += secs
                        somme /= 3600
                        line = [day, somme] + line
                        savingData.append(line)

                    # Write recap inside history/
                    recap_path = os.path.join(HISTORY_DIR, "recap.csv")
                    with open(recap_path, "w", encoding="utf-8", newline='') as resume:
                        csvwriter = csv.writer(resume)
                        csvwriter.writerow(headers)
                        csvwriter.writerows(savingData)

            time.sleep(1)
            tm += 1
            tm %= 60
    except KeyboardInterrupt:
        # Resume the current activity on interruption
        activities, actual_activity, actual_time_entry_start_time = resume_activity(activities,
                                                                                    actual_activity,
                                                                                    actual_time_entry_start_time)

def default_value():
    return 0

def resumeSavingFiles(taille_sauvegarde):
    """
    Reads the ring files from history/ and reconstructs (date, activity)->seconds
    to build the recap.
    """
    saving_table = defaultdict(default_value)
    dates = []
    activities = set()
    for i in range(taille_sauvegarde):
        try:
            sauvegarde_day = "sauvegardeDay" + str(i) + ".csv"
            file_path = os.path.join(HISTORY_DIR, sauvegarde_day)
            with open(file_path, newline='', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                first_line = next(csv_reader)
                saving_date = first_line[1].split(' : ')[-1]
                dates.append(saving_date)
                for row in csv_reader:
                    activity_title = row[0]
                    # Store in SECONDS (int) for recap computations
                    time_spent = math.floor(parse_duration_string(row[1]).total_seconds())
                    activities.add(activity_title)
                    saving_table[(saving_date, activity_title)] = time_spent
        except (IndexError, StopIteration, FileNotFoundError):
            return sorted(dates), activities, saving_table
    return sorted(dates), activities, saving_table

def parse_duration_string(duration_str):
    parts = duration_str.split(':')
    hours, minutes = int(parts[0]), int(parts[1])
    # Support seconds optionally having decimals
    sec_part = parts[2]
    if '.' in sec_part:
        seconds = math.floor(float(sec_part))
    else:
        seconds = int(sec_part)
    duration = timedelta(hours=hours, minutes=minutes, seconds=seconds)
    return duration

def find_index(date, taille_sauvegarde):
    new_date = date.split()[0]
    dates = []
    for i in range(taille_sauvegarde):
        try:
            sauvegarde_day = "sauvegardeDay" + str(i) + ".csv"
            file_path = os.path.join(HISTORY_DIR, sauvegarde_day)
            with open(file_path, newline='', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                content = next(csv_reader)
                date_content = content[1].split(' : ')
                saving_date = date_content[-1]
                dates.append((saving_date, i))
        except (IndexError, StopIteration, FileNotFoundError):
            if len(dates) == 0:
                return (i, False)  # False means that the page is empty
            else:
                mx_date = sorted(dates, key=lambda x: x[0])[-1]
                if mx_date[0] == date:
                    return (mx_date[1], True)  # True means that the page contains already some information
                else:
                    return ((mx_date[1] + 1) % taille_sauvegarde, False)  # False means that we don't need the content of this page
    mx_date = sorted(dates, key=lambda x: x[0])[-1]
    if mx_date[0] == date:
        return (mx_date[1], True)  # True means that the page contains already some information
    else:
        return ((mx_date[1] + 1) % taille_sauvegarde, False)  # False means that we don't need the content of this page

def resume_activity(activities, actual_activity, actual_time_entry_start_time):
    current_activity = get_active_window_title()
    if current_activity != actual_activity:
        for previous_activity in activities:
            if previous_activity.window_title == actual_activity:
                break
        else:
            previous_activity = None

        previous_activity_time_entry = TimeEntry(start_time=actual_time_entry_start_time,
                                                 end_time=datetime.now(pytz.timezone("Europe/Paris")))
        if not previous_activity:
            previous_activity = Activity(actual_activity)
            activities.append(previous_activity)

        previous_activity.add_time_entry(previous_activity_time_entry)
        actual_activity = current_activity
        actual_time_entry_start_time = datetime.now(pytz.timezone("Europe/Paris"))
    return activities, actual_activity, actual_time_entry_start_time

def write_to_csv(file_name, data):
    with open(file_name, "a", newline='', encoding="utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(data)

def read_from_csv(file_name):
    with open(file_name, "r", newline='', encoding="utf-8") as csvfile:
        csv_reader = csv.reader(csvfile)
        return list(csv_reader)

if __name__ == "__main__":
    main()
