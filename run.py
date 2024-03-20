"""Time Tracking App."""
import time
from datetime import datetime, timezone
from helpers import get_active_window_title
from models import Activity, TimeEntry
from unidecode import unidecode
def main():
    """Main function."""
    activities = []
    actual_activity = get_active_window_title()
    actual_time_entry_start_time = datetime.now(timezone.utc)
    print("Resume live:")
    print("")
    print("Activity\tTime Spent")
    print("________\t__________")
    actual=None
    memoire=set()
    
    fichier_sauvegarde_update=open('sauvegarde.txt',"r+", encoding="utf-8")
    fichier_sauvegarde_update.readline()
    for line in fichier_sauvegarde_update:
        ln=line.split('|')
        memoire.add(ln[0])
    fichier_sauvegarde_update.close()
    try:
        while True:
            activities, actual_activity, actual_time_entry_start_time = resume_activity(activities,
                                                                                        actual_activity,
                                                                                        actual_time_entry_start_time)       
            
            '''if len(activities):
                if actual!=activities[-1].window_title:
                    print(f"{activities[-1].window_title}\t{activities[-1].get_time_spent()}")  
                    #print(actual_activity)
                    actual = activities[-1].window_title'''
            
            if len(activities):
                memoire_generale=set()
                temps_usage_combined={}
                for activity in activities:
                    if activity.window_title!=None:
                        if activity.window_title not in memoire:
                            fichier_sauvegarde_update=open('sauvegarde.txt',"a", encoding="utf-8")
                            memoire.add(activity.window_title)
                            fichier_sauvegarde_update.write("\n"+activity.window_title +"|"+ str(activity.get_time_spent()))
                            fichier_sauvegarde_update.close()
                            
                        else:
                            fichier_sauvegarde_update=open('sauvegarde.txt',"r", encoding="utf-8")
                            lines=fichier_sauvegarde_update.read().split("\n")
                            fichier_sauvegarde_update.close()
                            for i in range(1,len(lines)):
                                ls_line=lines[i].split('|')
                                if ls_line[0]==activity.window_title:
                                        ls_line[1]=str(activity.get_time_spent())
                                        lines[i]='|'.join(ls_line)
                                        break
                            fichier_sauvegarde_update=open('sauvegarde.txt',"w", encoding="utf-8")
                            for line in lines:
                                if line !="":
                                    fichier_sauvegarde_update.write(line+"\n")
                            fichier_sauvegarde_update.close()
                # creation du fichier qui resume le temps d'usage
                for activity in activities:
                        if activity.window_title!=None:
                            if unidecode(activity.window_title).split(" -")[-1] not in memoire_generale:
                                    memoire_generale.add(unidecode(activity.window_title).split(" -")[-1])
                                    temps_usage_combined[unidecode(activity.window_title).split(" -")[-1]]=activity.get_time_spent()
                            else:
                                    temps_usage_combined[unidecode(activity.window_title).split(" -")[-1]]+=activity.get_time_spent()
                resume = open('Totale_sauvegarde.txt',"w", encoding="utf-8")
                resume.write("Activity    time usage")
                for key in temps_usage_combined:
                     resume.write("\n"+ key + " | " + str(temps_usage_combined[key]))
                resume.close()

            time.sleep(1)
    except KeyboardInterrupt:
        activities, actual_activity, actual_time_entry_start_time = resume_activity(activities,
                                                                                    actual_activity,
                                                                                    actual_time_entry_start_time)
        
        '''if len(activities):
                fichier_sauvegarde=open("sauvegarde.txt","w")
                for activity in activities:
                    fichier_sauvegarde.write("\n"+activity.window_title , activity.get_time_spent())
                fichier_sauvegarde.close()'''
        #for activity in activities:
        #    print(f"{activity.window_title}\t{activity.get_time_spent()}")


def resume_activity(activities, actual_activity, actual_time_entry_start_time):
    """Resume the actual activity."""
    current_activity = get_active_window_title()
    # Check if theres was a change in the activity
    if current_activity != actual_activity:
        # Look for if the activity exists
        for previus_activity in activities:
            if previus_activity.window_title == actual_activity:
                break
        else:
            previus_activity = None

        previus_activity_time_entry = TimeEntry(start_time=actual_time_entry_start_time,
                                                end_time=datetime.now(timezone.utc))
        # If not exist the activity, it'll be created
        if not previus_activity:
            previus_activity = Activity(actual_activity)
            activities.append(previus_activity)

        # Add the time entry for the activity
        previus_activity.add_time_entry(previus_activity_time_entry)
        # Set the new actual activity
        actual_activity = current_activity
        actual_time_entry_start_time = datetime.now(timezone.utc)
    return activities, actual_activity, actual_time_entry_start_time


if __name__ == "__main__":
    main()
