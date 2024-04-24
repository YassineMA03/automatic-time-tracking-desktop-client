import csv
import time
from datetime import datetime, timezone
import pytz
from helpers import get_active_window_title
from models import Activity, TimeEntry


def main():
    activities = []
    actual_activity = get_active_window_title()
    actual_time_entry_start_time = datetime.now(pytz.timezone("Europe/Paris"))
    last_activity_date = None  # Variable to store the date of the last activity
    print("Resume live:")
    print("")
    print("Activity\tTime Spent")
    print("________\t__________")
    memoire = set()
    temps_usage_combined = {}
    cnt=6
    tm=0
    try:
        while True:
            activities, actual_activity, actual_time_entry_start_time = resume_activity(activities,
                                                                                        actual_activity,
                                                                                        actual_time_entry_start_time)
            if len(activities):
                memoire_generale = set()
                data=[]
                # Check if a separator is needed based on the date
                current_date = datetime.now(pytz.timezone("Europe/Paris")).date()
                if last_activity_date != current_date:
                    activities = []
                    actual_activity = get_active_window_title()
                    actual_time_entry_start_time = datetime.now(pytz.timezone("Europe/Paris"))
                    last_activity_date = None  # Variable to store the date of the last activity
                    cnt+=1
                    cnt%=7
                    separator = ["Activity", "Time spent day : " + current_date.strftime('%Y-%m-%d')]
                    last_activity_date = current_date

                temps_usage_combined={}
                memoire=set()
                for activity in activities:
                    
                    if activity.window_title is not None:   
                            title = activity.window_title.split(" -")[-1].strip()
                            if title not in memoire:
                                memoire.add(title)
                                temps_usage_combined[title]=activity.get_time_spent()
                                
                            else:
                                temps_usage_combined[title]+=activity.get_time_spent()

                # Pour remplir le fichier du jour en question
                with open('sauvegardeDay'+str(cnt)+'.csv', "w", encoding="utf-8", newline='') as resume:
                    csv_writer = csv.writer(resume)
                    csv_writer.writerow(separator)
                    for key, value in temps_usage_combined.items():
                        csv_writer.writerow([key, value])

            time.sleep(1)
            tm+=1
    except KeyboardInterrupt:
        activities, actual_activity, actual_time_entry_start_time = resume_activity(activities,
                                                                                    actual_activity,
                                                                                    actual_time_entry_start_time)


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