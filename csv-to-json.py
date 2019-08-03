import argparse
import os
import sys
import csv
import json
import datetime
import dateutil.parser as date_parser
import codecs

# Parse Arguements
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', help='CSV input file', required=True)
args = parser.parse_args()
file=args.file

# Preflight Checks
if not os.path.exists(file):
    sys.exit("Cannot find "+file)

# Helper functions
def check_in_list(item, list):
    if item in list:
        list.remove(item)
        return True
    else:
        print("Error, not in list")
        return False

def choose_csv_column(hacker_tracker_field, csv_columns_left):
    output = ""
    while output == "":
        print("\nColumns left: "+str(csv_columns_left))
        user_input = str(input("Which column is "+hacker_tracker_field+"? ") or "")
        if check_in_list(user_input, csv_columns_left):
            output = user_input
            return (output, csv_columns_left)

def convert_to_isotime(text):
    date = date_parser.parse(text)
    return date.isoformat()

def set_endtime(iso_start_time, duration):
    print(duration)
    date_time_start = datetime.datetime.strptime(iso_start_time, '%Y-%m-%dT%H:%M:%S')
    end_time = date_time_start + datetime.timedelta(minutes=int(duration))
    return end_time.isoformat()

def get_speaker_id(speakers_list, speaker_handle, speaker_id, conference_code):
    # return speaker id if we already have it
    for speaker in speakers_list:
        if speaker['name'] == speaker_handle:
            return speakers_list, speaker['id']

    # Else just make a new one
    # Most of this is blank. Because Skytalks
    speaker_id += 1
    new_speaker_json = {}
    new_speaker_json.update({"name": speaker_handle})
    new_speaker_json.update({ "updated_at": datetime.datetime.now().isoformat()})
    new_speaker_json.update({"description": ""})
    new_speaker_json.update({"title": ""})
    new_speaker_json.update({"id": speaker_id})
    new_speaker_json.update({"twitter": ""})
    new_speaker_json.update({"conference": conference_code})
    new_speaker_json.update({"link": ""})
    speakers_list.append(new_speaker_json)
    return speakers_list, speaker_id

# Lets chew in the CSV
csv_columns=[]
list_of_events=[]
with open(file) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            for item in row:
                csv_columns.append(item)
            print(f'Column names are {", ".join(csv_columns)}')
            line_count += 1
        else:
            event_json={}
            for i in range(0,len(csv_columns)):
                event_json.update({csv_columns[i]: row[i]})
            list_of_events.append(event_json)
            line_count += 1

# Alrighty then. Now to line up with the inputs hacker tracker needs
csv_columns_left = csv_columns
print("Set global values")
conference_code = str(input("Conference Code [DC27]: ") or "DC27")
event_type = int(input("Event Type [9]: ") or "9")
location = str(input("Location [Bally’s Las Vegas - Jubilee Tower 2nd floor]: ") or "Bally’s Las Vegas - Jubilee Tower 2nd floor")

print('\n\n')
print("Choose which CSV column headers to set to which Hacker Tracker Option")
start_date, csv_columns_left = choose_csv_column("start_date", csv_columns_left)
duration, csv_columns_left = choose_csv_column("duration (in minutes)", csv_columns_left)
title, csv_columns_left = choose_csv_column("title", csv_columns_left)
speakers, csv_columns_left = choose_csv_column("speakers", csv_columns_left)
description, csv_columns_left = choose_csv_column("description", csv_columns_left)

'''
# Hardcoded Skytalks Values
conference_code = "DC27"
event_type = "9"
location = "Bally’s Las Vegas - Jubilee Tower 2nd floor"
start_date = "Day-Time"
duration = "Duration"
title = "Talk Title"
speakers = "Speaker(s)"
description = "Talk Description"
'''
# And finally, let's make some JSON
schedule = []
speakers_list = []
id = 1337
current_speaker_id = 7331
for event in list_of_events:
    # Check for empty keys caused by newlines
    print(event)
    if event[title] == "":
        pass
    else:
        hacker_tracker_event_json = {}
        hacker_tracker_event_json.update({"start_date": str(convert_to_isotime(event[start_date]))})
        hacker_tracker_event_json.update({"id": id})
        hacker_tracker_event_json.update({"description": event[description]})
        hacker_tracker_event_json.update({"location": location})
        hacker_tracker_event_json.update({"link": ""})
        # hacker_tracker_event_json.update({"speakers": event[speakers].splitlines()})
        this_event_speakers=[]
        for speaker in event[speakers].splitlines():
            speakers_list, speaker_to_append = get_speaker_id(speakers_list, speaker, current_speaker_id, conference_code)
            this_event_speakers.append(speaker_to_append)
            if current_speaker_id < speaker_to_append:
                current_speaker_id = speaker_to_append
        hacker_tracker_event_json.update({"speakers": this_event_speakers})
        hacker_tracker_event_json.update({"end_date": str(set_endtime(convert_to_isotime(event[start_date]), event[duration]))})
        hacker_tracker_event_json.update({"conference": conference_code})
        hacker_tracker_event_json.update({"event_type": int(event_type)})
        hacker_tracker_event_json.update({"includes": ""})
        hacker_tracker_event_json.update({"title": event[title]})
        hacker_tracker_event_json.update({"updated_at": datetime.datetime.now().isoformat()})

        schedule.append(hacker_tracker_event_json)
        id += 1

hacker_tracker_schedule_json = {}
hacker_tracker_schedule_json.update({"Schedule": schedule})
print(json.dumps(hacker_tracker_schedule_json, indent=2, ensure_ascii=False))

hacker_tracker_speakers_json = {}
hacker_tracker_speakers_json.update({"speakers": speakers_list})
print(json.dumps(hacker_tracker_speakers_json, indent=2, ensure_ascii=False))

# Let's write this sucker to a file
with codecs.open('events.json', 'w', 'utf-8') as events_file:
    events_file.write(json.dumps(hacker_tracker_schedule_json, indent=2, ensure_ascii=False))
with codecs.open('speakers.json', 'w', 'utf-8') as speakers_file:
    speakers_file.write(json.dumps(hacker_tracker_speakers_json, indent=2, ensure_ascii=False))