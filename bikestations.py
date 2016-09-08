# -*- coding: utf-8 -*-
"""
Created on Tue Apr 07 15:11:49 2014
@author: Maurizio Napolitano <napo@fbk.eu>
The MIT License (MIT)
Copyright (c) 2016 Fondazione Bruno Kessler http://fbk.eu
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
#from __future__ import unicode_literals
#from builtins import str
from pysqlite2 import dbapi2 as sqlite3   
import requests, datetime
class Bikestations():
    url = "https://os.smartcommunitylab.it/core.mobility/bikesharing/trento"
    wgs84 = 4326
    db = "bikestations.sqlite"
    def __init__(self):
        self.con=sqlite3.connect(self.db)        
        self.con.enable_load_extension(True)
        self.cur = self.con.cursor()
        self.cur.execute('SELECT load_extension("mod_spatialite")');
        geo = self.cur.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='geometry_columns';").fetchall()[0][0]
        if (geo == 0):
            self.cur.execute('SELECT InitSpatialMetadata();')
        createstations = '''
        CREATE TABLE if not exists stations (id INTEGER NOT NULL, name TEXT, address TEXT, latitude REAL, longitude REAL, slots INTEGER);
        '''
        addgeometry = "SELECT AddGeometryColumn('stations', 'geometry', %s, 'POINT', 'XY');" % self.wgs84
        createbikesuse= '''
        CREATE TABLE if not exists bikeuse (id INTEGER PRIMARY KEY ASC, idstation INTEGER, bikes INTEGER, slots INTEGER, day TEXT);
        '''
        self.cur.execute(createstations);
        self.cur.execute(addgeometry);
        self.cur.execute(createbikesuse);
        cname = self.cur.execute('select count(name) from stations').fetchone()[0]
        if cname == 0:
            r = requests.get(self.url)
            data =  r.json()
            for datum in data: 
                idstation = datum['id']
                address = datum['address']
                slots = datum['slots']
                name = datum['name']
                latitude = datum['position'][0]
                longitude = datum['position'][1]
                geometryfromtext = "GeomFromText('POINT(%s %s)', %s)" % (latitude, longitude,self.wgs84)
                insertsql = '''
                INSERT INTO stations VALUES (%s,'%s','%s', %s, %s, %s, %s);
                ''' % (idstation,name,address,latitude,longitude,slots,geometryfromtext)
                self.cur.execute(insertsql)
        self.con.commit()
            
    def addbikes(self):
        r = requests.get("https://os.smartcommunitylab.it/core.mobility/bikesharing/trento")
        data =  r.json()
        for datum in data:
            idstation = datum["id"]
            bikes = datum["bikes"]
            slots = datum["slots"]
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            insertsql = '''
            INSERT INTO bikeuse (idstation, bikes, slots, day) VALUES (%s,%s,%s,'%s')
            ''' % (idstation, bikes,slots,date)
            self.cur.execute(insertsql)
        self.con.commit()

