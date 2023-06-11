import pickle
import json 
import os 
from pprint import pprint
import re

from whoosh.index import create_in
from whoosh.fields import *

schema = Schema(title=TEXT(stored=True), id=ID(stored=True), content=TEXT(stored=True), author=TEXT(stored=True), citation=NUMERIC(stored=True, sortable=True), year=DATETIME(stored=True, sortable=True))

if not os.path.exists("index"):
    os.mkdir("index")
ix = create_in("index", schema)

from whoosh.index import open_dir

ix = open_dir("index")


writer = ix.writer()

with open('./mock_data/Papers.pkl', 'rb') as f:
    p_list = pickle.load(f)

print(p_list[1000]['year'])
# pprint(p_list[1000])
time = p_list[1000]['year']
m, y = time.split(' ')
m_dict = {
        'Jan' : 1,
        'Feb' : 2,
        'Mar' : 3,
        'Apr' : 4,
        'May' : 5,
        'Jun' : 6,
        'Jul' : 7,
        'Aug' : 8,
        'Sep' : 9, 
        'Oct' : 10,
        'Nov' : 11,
        'Dec' : 12
}
m = m_dict[m[:3]]
print(y, m)

from datetime import datetime

t = datetime(int(y), m, 1)
print(t)
for p in p_list:
    print(p["title"])
    # print(p[])
    time = p['year']
    m, y = time.split(' ') 
    m = m_dict[m[:3]]
    print(y, m)

    t = datetime(int(y), m, 1) 
    writer.add_document(title=p["title"], 
                        content=p["abstract"],
                        author=p["authors"],
                        id=str(p["id"]),
                        citation=p["citation"],
                        year=t)
writer.commit()
