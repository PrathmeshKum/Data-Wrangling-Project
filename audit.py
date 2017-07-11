# Audit File:

import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

OSMFILE = 'SLC.osm'
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)


# Set of standard words for the address tags

expected = ["Avenue,", "Boulevard", "Broadway", "Circle", "Court", "Drive", "Driveway", "East", "Highway", 
        "Lane", "North", "Park", "Parkway", "Place", "Plaza", "Road", "South", "Square", "Street", "West"]

        
# Set of different words which will be replaced by ones in the expected set
# when encountered in the address tags 

mapping = {"Ave": "Avenue", "Ave.": "Avenue", "Cir": "Circle", "Ct": "Court", "Dr": "Drive",
           "E": "East", "E.": "East", "Hwy": "Highway", "N": "North", "N.": "North", "Pkwy": "Parkway",
           "Rd.": "Road", "rd.": "Road", "Rd": "Road", "Rd.": "Road", "rd.": "Road", "Rd": "Road",
           "S": "South", "S.": "South", "Sq.": "Square", "St": "Street", "st": "Street",
           "St.": "Street", "St,": "Street", "ST": "Street", "Street.": "Street", "street": "Street",
           "W": "West", "W.": "West", "Blvd": "Boulevard"}

 
# Checks whether the last word in the address tags require to be replaced            
           
def audit_street_type(street_types, street_name):

    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)


# Adds postal codes in the list to check for cleaning            
            
def audit_postalcode(postalcodes, postalcode):
    
    postalcodes[postalcode].add(postalcode)
    return postalcodes 
            
 
           
# Returns tag asscociated with street address     
    
def is_street_name(elem):     

    return (elem.attrib['k'] == "addr:street")
  
# Returns tag associated with postal codes
    
def is_postalcode(elem):
    
    return (elem.attrib['k'] == "addr:postcode" or elem.attrib['k'] == "postal_code")    
    

    
# Checks for all tags whether street address is asscociated with it
# If so, then checks whether the last word in that address is in proper
# format and then returns dictionary of words which need replacement
    
def audit(osmfile):

    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types


# Checks for all tags whether postal code is asscociated with it
# If so, then adds to dictionary and returns for cleaning purposes.
    
def audit_postal(osmfile):
    
    osm_file=open(osmfile, 'r')
    postalcodes = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_postalcode(tag):
                    postalcodes = audit_postalcode(postalcodes, tag.attrib["v"])
    osm_file.close()
    return postalcodes
 
    
# Substitutes the last words in the street address collected
# with the ones defined in the mapping list   
    
def update_name(name, mapping):

    m = street_type_re.search(name)
    if m not in expected:
        if m.group() in mapping.keys():
            name = re.sub(m.group(), mapping[m.group()], name)
    
    return name


# Extracts the 5 digit postal code present and updates it
# 1st condition if only 5 digits are present
# 2nd codition if 9 digits are present
# 3rd condition if state code UT is present  
    
def update_postalcode(postalcode):
    
      if len(postalcode) == 5:
          
          re.findall(r'^\d{5}', postalcode)
          updated_postalcode = postalcode
          return updated_postalcode
    
      elif len(postalcode) == 9:
          updated_postalcode = re.findall(r'(^\d{5})-\d{4}$', postalcode)[0]
          return updated_postalcode
          
      else:
          
          updated_postalcode =re.findall(r'\d{5}', postalcode)[0]  
          return updated_postalcode 
            
        
        

# Function for excecuting the street address cleaning
# Prints the old and new results for the user        
        
def test():
    st_types = audit(OSMFILE)
    pprint.pprint(st_types)

    for st_type, ways in st_types.iteritems():
        for name in ways:
            better_name = update_name(name, mapping)
            print name, "=>", better_name

    postal_types = audit_postal(OSMFILE)
    pprint.pprint(postal_types)

    for postal_type, ways in postal_types.iteritems():
        for name in ways:
            better_name = update_postalcode(name)
            print name, "=>", better_name
            
    
if __name__ == '__main__':
    test()
            
