import json


search_fields_mapper = {
        'topic': 'sobre {}',
        'subtopics': 'sobre {}',
        'tags': 'relacionadas con {}',
        'author': 'de {}',
        'deputy': 'firmadas por {}',
        'startdate': 'desde {}',
        'enddate': 'hasta {}',
        'status': 'que estén {}',
        'place': 'en {}',
        'type': 'que sean {}',
        'reference': 'con referencia {}',
        'text': 'que contengan "{}"',
        'ignoretagless': ''
        }

def _rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)

def _parse_date(date):
    split_date = date.split('-')
    return "{}/{}/{}".format(
            split_date[2],
            split_date[1],
            split_date[0]
            ).strip()

def _parse_deputyname(name):
    split_name = name.split(',')
    return "{} {}".format(
            split_name[1],
            split_name[0]
            ).strip()

def _parse_field(key, value):
    if key == 'deputy':
        value = _parse_deputyname(value)
    if key == 'startdate' or key == 'enddate':
        value = _parse_date(value)
    if type(value) is list:
        value = ', '.join(value)
        if len(value.split(",")) > 1:
            value = _rreplace(value, ", ", " y ", 1)
    return search_fields_mapper[key].format(value)

def make_sentence(search):
    search_dict = json.loads(search)
    sentence = ''
    if "subtopics" in search_dict.keys():
        if search_dict['subtopics'] == []:
            del search_dict['subtopics']
        else:
            del search_dict['topic']
    for key, value in search_dict.items():
        if key == 'knowledgebase' or key == 'ignoretagless':
            continue
        if value:
            sentence = sentence + ' ' + _parse_field(key, value) + ','
    return sentence[0:len(sentence)-1] + "."

