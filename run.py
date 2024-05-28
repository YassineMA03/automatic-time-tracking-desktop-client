import csv
import time
from datetime import datetime, timezone,timedelta
import pytz
from helpers import get_active_window_title
from models import Activity, TimeEntry
import pandas as pd
import math
import unidecode
def main():
    memoire_initiale = set()
    temps_usage_initial={} 
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
    first_start=True
    try:
        while True:
            activities, actual_activity, actual_time_entry_start_time = resume_activity(activities,
                                                                                        actual_activity,
                                                                                        actual_time_entry_start_time)
            if len(activities):
                current_date = datetime.now(pytz.timezone("Europe/Paris")).date()
                separator = ["Activity", "Time spent day : " + current_date.strftime('%Y-%m-%d')]
                data=[]
                temps_usage_combined={}
                memoire=set()   
            
                if last_activity_date != current_date:
                    activities = []
                    actual_activity = get_active_window_title()
                    actual_time_entry_start_time = datetime.now(pytz.timezone("Europe/Paris"))
                    last_activity_date = None  # Variable to store the date of the last activity
                    if first_start:
                        cnt=find_index(current_date.strftime('%Y-%m-%d'))[0]
                        #print(cnt)
                        changes_needed=find_index(current_date.strftime('%Y-%m-%d'))[1]
                        if changes_needed:
                            with open('sauvegardeDay'+str(cnt)+'.csv', 'r', newline='') as file:
                                    # Create a CSV reader object
                                    csv_reader = csv.reader(file)
                                            
                                    # Skip the header line (first line)
                                    next(csv_reader)
                                            
                                    # Read and process the remaining lines
                                    for row in csv_reader:
                                        # Access the second column (index 1)
                                        activity_title=row[0]
                                        time_spent = parse_duration_string(row[1])
                                        memoire_initiale.add(activity_title)
                                        temps_usage_initial[activity_title]=time_spent
                                        #print(row[0],time_spent,row[1])
                                        #print('################')
                        first_start=False
                    else:
                        cnt+=1
                        cnt%=7
                        memoire_initiale=set()
                        temps_usage_initial={}
                        changes_needed=False
                    last_activity_date = current_date
                if changes_needed:
                    for element in memoire_initiale:
                        memoire.add(element)
                    for key in temps_usage_initial:
                        temps_usage_combined[key]=temps_usage_initial[key]   
                
                                    
                for activity in activities:
                    
                    if activity.window_title is not None:   
                            title = activity.window_title.strip()
                            title=unidecode.unidecode(title)
                            new_title=''
                            for word in title.split(' -')[-1].split():
                                new_title+=''.join(e for e in word if e.isalnum())
                                new_title+=' '
                            
                            if new_title not in memoire:
                                memoire.add(new_title)
                                temps_usage_combined[new_title]=activity.get_time_spent()
                                
                            else:
                                temps_usage_combined[new_title]+=activity.get_time_spent()

                # Pour remplir le fichier du jour en question
                with open('sauvegardeDay'+str(cnt)+'.csv', "w", encoding="utf-8", newline='') as resume:
                    csv_writer = csv.writer(resume)
                    csv_writer.writerow(separator)
                    for key, value in temps_usage_combined.items():
                        csv_writer.writerow([key, value])

            time.sleep(1)
            #print('################################')
    except KeyboardInterrupt:
        activities, actual_activity, actual_time_entry_start_time = resume_activity(activities,
                                                                                    actual_activity,
                                                                                    actual_time_entry_start_time)
        

def parse_duration_string(duration_str):
    # Split the string into hours, minutes, seconds, and milliseconds
    parts = duration_str.split(':')
    hours, minutes, seconds = (int(parts[0]),int(parts[1]),math.floor(float(parts[2])))
    #seconds, milliseconds = map(int, parts[2].split('.'))
    if len(parts[2].split('.'))==2:
        milliseconds=int(parts[2].split('.')[1])//1000
    else:
        milliseconds=0
    # Create a timedelta object
    #print(hours,minutes,seconds,milliseconds)
    duration = timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)

    return duration
def find_index(date):
    new_date=date.split()[0]
    dates=[]
    for i in range(7):
        try: 
            with open('sauvegardeDay'+str(i)+'.csv', newline='', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                #print(next(csv_reader))
                content = next(csv_reader)
                #print('length of content is: '+str(len(content)))
                date_content=content[1].split(' : ')
                saving_date = date_content[-1]
                dates.append((saving_date,i))
        except (IndexError,StopIteration) as e:
                if len(dates)==0:
                    return (i,False) #false means that the page is empty
                else:
                    mx_date = sorted(dates, key=lambda x: x[0])[-1]
                    if mx_date[0]==date:
                        return (mx_date[1],True) # True means that the page contains already some information
                    else:
                        return ((mx_date[1]+1)%7,False) # False means that we don't need the content of this page
    mx_date = sorted(dates, key=lambda x: x[0])[-1]
    if mx_date[0]==new_date:
        return (mx_date[1],True) # True means that the page contains already some information
    else:
        return ((mx_date[1]+1)%7,False) # False means that we don't need the content of this page

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