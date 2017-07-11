import xml.etree.cElementTree as ET
import pprint


# Loops through the file and searches all tags
# These tags are grouped according to the type (like way, node)

def count_tags(filename):

    tags ={}
    for event, element in ET.iterparse(filename):
        tag= element.tag
        if tag not in tags.keys():
            tags[tag] =1
        else:
            tags[tag] += 1
    return tags
    
pprint.pprint(count_tags('SLC.osm'))