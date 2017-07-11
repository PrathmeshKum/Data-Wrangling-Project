import xml.etree.cElementTree as ET
import pprint

# This function parses file and searches unique ID of users
# If this UID is present in the set, then add to it
# Number of different users in the file is returned

def process_map(filename):
    users = set()
    for _, element in ET.iterparse(filename):
        if 'uid' in element.attrib.keys():
            users.add(element.attrib['uid'])
        
    return users

users_num = process_map('SLC.osm') 
    
pprint.pprint(len(users_num))