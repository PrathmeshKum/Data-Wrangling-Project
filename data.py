import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
import schema
import cerberus
from collections import defaultdict

OSM_PATH = "SLC.osm"
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

           
# Defining names for all the csv files required to be created

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"


# lower_colon matches tags with colon present in them
# problemchars matches tags with problematic characters present in them
# These are required whie shaping way or node tags

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema


# Defining the fields in each csv file which is given in the schema file
# Same order must be maintained while creating tables using SQL

NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


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
    if m:
        for a in mapping:
            if a == m.group():
                name = re.sub(street_type_re, mapping[a], name)
    
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

          
 
# Cleans and shapes node or way XML element
# Checks whether the tag is node or way
# Then leaves them if they have problematic characters
# Sets values 'value','id','type' & 'key' depending on if they have lower colon or not
# Further, updates 'value' according to street address and postal code cleaning process
# way_node, way_tag, node_tag and their attributes are returned 
        

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):

    node_attribs = {} 
    way_attribs = {}
    way_nodes = []
    tags = []
    
    if element.tag == 'node':
        for attribute in NODE_FIELDS:
   
            node_attribs[attribute] = element.attrib[attribute]
        
        for TAG in element.iter("tag"):
            if PROBLEMCHARS.match(TAG.attrib['k']):
                continue
            
            else:
                node_tag = {}
                node_tag['value'] = TAG.attrib['v']
                node_tag['id'] = element.attrib['id']

                if LOWER_COLON.match(TAG.attrib['k']):
                    
                    node_tag['type'] = TAG.attrib['k'].split(':',1)[0]
                    node_tag['key'] = TAG.attrib['k'].split(':',1)[1]
                
                    if node_tag['type'] == "addr" and node_tag['key'] == "street":
                        node_tag['value'] = update_name(TAG.attrib['v'], mapping)
                
                    elif node_tag['type'] == "addr" and node_tag['key'] == "postcode":
                        node_tag['value'] = update_postalcode(TAG.attrib['v']) 
                        
        
                else:
                    node_tag['type'] = 'regular'
                    node_tag['key'] = TAG.attrib['k']
                
                

            tags.append(node_tag)
        
        return {'node': node_attribs, 'node_tags': tags}



 
    elif element.tag == 'way':
        for attribute in WAY_FIELDS:
            way_attribs[attribute] = element.attrib[attribute]
        
         
        for TAG in element.iter("tag"):
            if PROBLEMCHARS.match(TAG.attrib['k']):
                continue
            
        
            else:
                way_tag = {}
                way_tag['id'] = element.attrib['id']
                way_tag['value'] = TAG.attrib['v']
            
            
                if LOWER_COLON.match(TAG.attrib['k']):
                    
                    way_tag['type'] = TAG.attrib['k'].split(':',1)[0]
                    way_tag['key'] = TAG.attrib['k'].split(':',1)[1]
                
                    if way_tag['type'] == "addr" and way_tag['key'] == "street":
                        way_tag['value'] = update_name(TAG.attrib['v'], mapping)
                    
                    elif way_tag['type'] == "addr" and way_tag['key'] == "postcode":
                        way_tag['value'] = update_postalcode(TAG.attrib['v'])

                         
                else:
                    way_tag['type'] = 'regular'
                    way_tag['key'] = TAG.attrib['k']
                        
            tags.append(way_tag)
        
            
        position = 0
        
        for TAG in element.iter("nd"):
            
                nd={}
                nd['node_id'] = TAG.attrib['ref']
                nd['id'] = element.attrib['id']
                nd['position'] = position
                position += 1
                
                way_nodes.append(nd)
        
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #

# Yield element if it is the right type of tag

def get_element(osm_file, tags=('node', 'way', 'relation')):
    

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


# Raise ValidationError if element does not match schema            
            
def validate_element(element, validator, schema=SCHEMA):
    
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))

        
#Extend csv.DictWriter to handle Unicode input
        
class UnicodeDictWriter(csv.DictWriter, object):
    

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #

# Iteratively process each XML element and write to csv(s)

def process_map(file_in, validate):
    

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=False)
