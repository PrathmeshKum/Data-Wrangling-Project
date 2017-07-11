import xml.etree.cElementTree as ET
import re
import pprint

# lower matches tags with only lowercase letters in them
# lower_colon matches tags with colon present in them
# problemchars matches tags with problematic characters present in them

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


# This function searches all the tags in the file
# Then groups them in 4 different types 


def key_type(element, keys):

    if element.tag == "tag":
        key = element.attrib['k']
        a = re.search(lower, key)
        b = re.search(lower_colon, key)
        c= re.search(problemchars, key)
        
        
        if a is None:
            pass
        
        else:
            keys['lower']+=1
        
        if b is None:
            pass
        
        else:
            keys['lower_colon']+=1

        if c is None:
            pass
        
        else:
            keys['problemchars'] +=1
        
        if (a is None) & (b is None) & (c is None):
            keys['other']+=1
        
    return keys

 
# Returns the count of tags for each type    
    
def process_map(filename):
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)

    return keys
    
pprint.pprint(process_map('SLC.osm'))
