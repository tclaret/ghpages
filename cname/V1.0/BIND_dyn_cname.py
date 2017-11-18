#!/usr/bin/python 
from shutil import copyfile
from flask import Flask, request, jsonify, json, url_for
from flask_restful import reqparse, abort, Api, Resource
from flask_httpauth import HTTPBasicAuth
from configobj import ConfigObj
import flask_httpauth
import os
import re
import sys

FichierConf="BIND_dyn_cname.conf"
config = ConfigObj(FichierConf)
auth_zones=config["zones"]
DEBUG=True
auth = HTTPBasicAuth()
app = Flask(__name__)
api = Api(app)
#users= config['users']
users = {
    "tclaret": "tclaret",
    "titi": "toto"
}

@auth.get_password
def get_password(username):
    if username in users:
        return users.get(username)
    return None

def validate(zone):
    config = ConfigObj(FichierConf)
    auth_zones=config["zones"]
    if zone in auth_zones:
        return True
    return False

def identifyZone(Resource):
    i = Resource.index(".")
    zone=Resource[i+1:]
    return zone

def mustEndWithDot(cname):
    t=cname[::-1]
    if (t[0] != "." ):
        cname = cname + "."
    return cname

    
class Fonc2(Resource):
    def post(self):
        json_data = request.get_json(force=True)
        cname=json_data['canonical']
        value=json_data['name']
        print ( cname + "  " + value)
        os.system('echo', " put cname > f.out" )
        return jsonify(canonical=cname,name=value)



def write(Record,zone):
    f = open(zone + ".cnames","a")
    f.write(Record)
    f.close()

def readAll():
    auth_zones=config["zones"]
    lines=[]
    for zone in auth_zones:
        if(os.path.isfile(zone + ".cnames")):
            f = open(zone + ".cnames", 'r')
            for line in f:
                lines.append(line)
            f.close()
    return lines

class Fonc1(Resource):
    @auth.login_required
    def post(self):
        json_data = request.get_json(force=True)
        cname=json_data['canonical']
        value=json_data['name']
        zone=identifyZone(cname)
        if DEBUG : 
            print "Fonc1"
            print "POST"
            print ( cname + "  " + value)
        #TTL="150" + "   "
        TTL=""
        CLASS="IN"
        TYPE="CNAME"
        cname=mustEndWithDot(cname)
        ResourceRecord=(TTL + value + 10*" " + CLASS + 15*" " + TYPE + 5*" "  +  cname + "\n")
        # ajouter controle du controle
        write(ResourceRecord,zone)
        return jsonify(canonical=cname,name=value)

    def get(self):
        if DEBUG : 
            print "Fonc1"
            print "GET"
        print readAll() 
        return jsonify( readAll() )

    def delete(self):
        json_data = request.get_json(force=True)
        value=json_data['name']
        if DEBUG : 
            print "Fonc1"
            print "DELETE"
            print value
        auth_zones=config["zones"]
        lines=[]
        for zone in auth_zones:
            if(os.path.isfile(zone + ".cnames")):
                print "FILE  :" + zone + ".cnames"
                tname="." + zone + ".cnames"
                #content=[]
                out = open(tname,"w") 
                for line in open(zone + ".cnames",'r'):
                    if DEBUG : 
                        print "line :" + line
                    #content.append(line)
                    t=re.search("(\w+)(\s+in)(\s+cname)(\s+\S+$)",line.lower())
                    if (t):
                        if DEBUG : 
                            print "match1:  RR de type CNAME"
                        t = re.match(t.group(1),value.lower())
                        if(t):
                            if DEBUG : 
                                print "match2   :  line matches name"
                        else:
                            if DEBUG : 
                                print "nomatch2 : " + value.lower() +" <= NO MATCH => " + line.lower()
                            out.write(line)
                            out.flush()
                    else:
                        
                        print "NoMatch1"
                        a="b"
                    src=tname
                    dst=zone + ".cnames"
                    copyfile(src, dst)

api.add_resource(Fonc1,'/api/V1.0/record:cname')
api.add_resource(Fonc2,'/api/V1.0/TXT:')


if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', debug=True)
    except :
        sys.stderr.write("[ERROR] \n" )
        sys.exit(2)
