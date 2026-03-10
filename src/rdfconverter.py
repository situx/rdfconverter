from rdflib import Graph, URIRef, Literal, RDF, RDFS, OWL, XSD
import argparse
import pandas as pd
import geopandas as gpd
import os
import os.path
import json


def resolveWildcardPath(thepath):
    result = []
    if "/*" not in thepath:
        result.append(thepath)
        return result
    print(thepath)
    normpath = thepath.replace("*", "")
    if os.path.exists(normpath):
        files = os.listdir(normpath)
        for file in files:
            print(file)
            if file.endswith(".ttl") or file.endswith(".owl") or file.endswith(".ttl") or file.endswith(".n3") or file.endswith(".nt"):
                result.append(normpath + file)
    return result

class RDFConverter:

    def detectColumnType(self,resultmap,columnname=""):
        intcount,doublecount,datecount,uricount = 0,0,0,0
        stringcount,tokencount=0,0
        uniquestrings=set()
        for res in resultmap:
            if res not in resultmap or resultmap[res] is None or resultmap[res] == "":
                continue
            resstr=str(resultmap[res])
            uniquestrings.add(resstr)
            tokencount+=1
            if resstr.isdigit():
                intcount += 1
                continue
            try:
                float(resstr)
                doublecount += 1
                continue
            except:
                pass
            if resstr.startswith("http"):
                uricount+=1
                continue
            stringcount+=1
        bcheck=self.checkForBooleanAsString(uniquestrings)
        if bcheck!=False:
            return {"range": "xsd:boolean","prop":"data", "valuemapping":bcheck, "unique": (tokencount == len(uniquestrings)),"category":False}
        if intcount == len(resultmap):
            return {"range": "xsd:integer","prop":"data", "unique": (tokencount == len(uniquestrings)),"category":False}
        if doublecount == len(resultmap):
            return {"range": "xsd:double","prop":"data", "unique": (tokencount == len(uniquestrings)),"category":False}
        if datecount == len(resultmap):
            return {"type": "range", "prop":"data","xsdtype": "xsd:date", "unique": (tokencount == len(uniquestrings)),"category":False}
        if uricount == len(resultmap):
            return {"range": "xsd:anyURI", "prop":"data","xsdtype": "xsd:anyURI", "unique": (tokencount == len(uniquestrings)),"category":False}
        return {"range":"xsd:string","prop":"data","unique":(stringcount==len(uniquestrings)),"category":(stringcount <= len(uniquestrings))}



    def checkForBooleanAsString(self,uniquestrings):
        if len(uniquestrings)>2:
            return False
        pairs=[["yes","no"],["true","false"],["ja","nein"],["oui","non"],["on","off"],["Y","N"],["J","N"]]
        for pair in pairs:
            if (pair[0] in uniquestrings and pair[1] in uniquestrings) or (pair[0].upper() in uniquestrings and pair[1].upper() in uniquestrings):
                return {pair[0]:True,pair[1]:False}
        return False


    def addPropertyToGraph(self,row,x,g,ns,curid,thecls,lang,curcol):
        subclass=False
        if row!=None and x not in row:
            return [g,False]
        if row is None:
            if "value" in curcol:
                thevalue=curcol["value"]
            else:
                thevalue=""
        else:
            thevalue=row[x]
        if "propiri" in curcol:
            theiri = URIRef(curcol["propiri"])
        else:
            theiri = URIRef(ns + x)
        if curcol["prop"]=="data":
            if "sepchar" in curcol:
                spl=thevalue.split(curcol["sepchar"])
            else:
                spl=[thevalue]
            unit=None
            unitprop="http://www.ontology-of-units-of-measure.org/resource/om-2/hasUnit"
            unithasvalue = "http://www.ontology-of-units-of-measure.org/resource/om-2/hasValue"
            if "unit" in curcol:
                unit=str(curcol["unit"]).replace("om:","http://www.ontology-of-units-of-measure.org/resource/om-2/").replace("qudt:","http://qudt.org/schema/qudt#")
            for sp in spl:
                if unit!=None:
                    g.add((theiri, RDF.type,OWL.ObjectProperty))
                    g.add((theiri, RDFS.label, Literal(str(x), lang="en")))
                    valueinstanceiri=curid+str("_")+str(theiri[theiri.rfind("/")+1:])+"_value"
                    g.add((URIRef(curid), theiri, URIRef(valueinstanceiri)))
                    g.add((URIRef(valueinstanceiri),RDF.type,URIRef("http://www.ontology-of-units-of-measure.org/resource/om-2/Measure")))
                    g.add((URIRef(valueinstanceiri), RDFS.label,Literal("Value Result of "+str(theiri[theiri.rfind("/")+1:])+" for "+str(curid))))
                    g.add((URIRef(valueinstanceiri), URIRef(unitprop),URIRef(unit)))
                    g.add((URIRef(valueinstanceiri), URIRef(unithasvalue), Literal(sp, datatype=URIRef(curcol["range"].replace("xsd:", "http://www.w3.org/2001/XMLSchema#")))))
                else:
                    g.add((theiri, RDF.type,OWL.DatatypeProperty))
                    g.add((theiri, RDFS.label, Literal(str(x), lang="en")))
                    g.add((URIRef(curid), theiri, Literal(sp, datatype=URIRef(
                        curcol["range"].replace("xsd:", "http://www.w3.org/2001/XMLSchema#")))))
        if curcol["prop"]=="obj":
            g.add((theiri, RDF.type, OWL.ObjectProperty))
            g.add((theiri, RDFS.label, Literal(str(x), lang="en")))
            g.add((URIRef(curid), theiri, URIRef(thevalue)))
        if curcol["prop"]=="anno":
            g.add((theiri, RDF.type, OWL.AnnotationProperty))
            g.add((theiri, RDFS.label, Literal(str(x), lang="en")))
            g.add((URIRef(curid),theiri, Literal(thevalue, datatype=XSD.string)))
        if curcol["prop"] == "subclass":
            if "valuemapping" in curcol and row[x] in curcol["valuemapping"]:
                g.add((URIRef(curcol["valuemapping"][thevalue]), RDFS.subClassOf, thecls))
                #g.add((URIRef(curcol["valuemapping"][row[x]]), RDFS.subClassOf, OWL.Class))
                g.add((URIRef(curid), RDF.type, URIRef(curcol["valuemapping"][thevalue])))
                g.add((URIRef(curcol["valuemapping"][thevalue]),RDFS.label,Literal(thevalue,lang=lang)))
                subclass=True
        return [g,subclass]


    def processColumns(self,prefix,seencols,x,curid,g,row,idcol,attns,thecls,lang,typemap):
        for x in typemap["columns"]:
            # print("CConfig: "+str(x))
            subclass = False
            intypemap = False
            if "ignore" in typemap["columns"][x] and typemap["columns"][x]["ignore"] == True:
                seencols.add(x)
                continue
            if x == "geometry":
                g.add((URIRef(curid), URIRef("http://www.opengis.net/ont/geosparql#hasGeometry"), URIRef(curid + "_geom")))
                g.add((URIRef("http://www.opengis.net/ont/geosparql#hasGeometry"), RDF.type, OWL.ObjectProperty))
                g.add((URIRef(curid + "_geom"), RDF.type, URIRef("http://www.opengis.net/ont/sf#" + str(row[x].type))))
                g.add((URIRef("http://www.opengis.net/ont/sf#" + str(row[x].type)), RDF.type, OWL.Class))
                g.add((URIRef("http://www.opengis.net/ont/sf#" + str(row[x].type)), RDFS.subClassOf,
                    URIRef("http://www.opengis.net/ont/geosparql#Geometry")))
                g.add((URIRef("http://www.opengis.net/ont/geosparql#Geometry"), RDF.type, OWL.Class))
                g.add((URIRef(curid + "_geom"), RDFS.label, Literal("Geometry of " + str(curid), lang="en")))
                g.add((URIRef("http://www.opengis.net/ont/geosparql#asWKT"), RDF.type, OWL.DatatypeProperty))
                if "epsg" in typemap:
                    g.add((URIRef(curid + "_geom"), URIRef("http://www.opengis.net/ont/geosparql#asWKT"),
                        Literal("<http://www.opengis.net/def/crs/EPSG/0/" + str(typemap["epsg"]) + "> " + str(row[x]),
                                datatype="http://www.opengis.net/ont/geosparql#wktLiteral")))
                else:
                    g.add((URIRef(curid + "_geom"), URIRef("http://www.opengis.net/ont/geosparql#asWKT"),
                        Literal(str(row[x]), datatype="http://www.opengis.net/ont/geosparql#wktLiteral")))
            if "collection" in typemap["columns"][x] and typemap["columns"][x]["collection"] == True and "columns" in typemap["columns"][x]:
                if "propiri" in typemap["columns"][x]:
                    theiri = URIRef(typemap["columns"][x]["propiri"])
                else:
                    theiri = URIRef(attns + x)
                if prefix!="":
                    res = processColumns(str(prefix) + "." + str(x), seencols, x, str(curid)+"_"+str(x), g, row, idcol,attns, thecls, lang, typemap["columns"][x])
                    g.add((URIRef(curid),URIRef(theiri),URIRef(str(curid)+"_"+str(x))))
                    g.add((URIRef(curid), URIRef(theiri), URIRef(str(curid) + "_" + str(x)),RDFS.label,Literal(str(curid)+"_"+str(x))))
                else:
                    res=processColumns(str(x),seencols,x,str(curid)+"_"+str(x),g,row,idcol,attns,thecls,lang,typemap["columns"][x])
                    g.add((URIRef(curid), URIRef(theiri), URIRef(str(curid)+"_"+str(x))))
                    g.add((URIRef(str(curid) + "_" + str(x)),RDFS.label,Literal(str(curid)+"_"+str(x))))
                g=res["graph"]
                seencols=res["seencols"]
            if x in typemap["columns"] and x != idcol and x != "geometry":
                intypemap = True
                curcol = typemap["columns"][x]
                res = self.addPropertyToGraph(row, x, g, attns, curid, thecls, lang, curcol)
                g = res[0]
                subclass = res[1]
                seencols.add(x)
        return {"graph":g,"subclass":subclass,"seencols":seencols}

    def convertToRDF(self,df,typemap,autotypemap,g,geosparql=True):
        #print(df)
        idcol=None
        dns=None
        attns=None
        if "id" in typemap:
            idcol=typemap["id"]
        if "namespace" in typemap:
            dns=typemap["namespace"]
        else:
            dns="http://purl.org/suni/data/"
        if "attnamespace" in typemap:
            attns=typemap["attnamespace"]
        else:
            attns="http://purl.org/suni/"
        if "nsprefix" in typemap:
            nsprefix=typemap["nsprefix"]
        elif "namespace" in typemap:
            nsprefix=typemap["namespace"][typemap["namespace"].rfind("/")+1:]
        else:
            nsprefix="suni"
        if "attnamespace" in typemap:
            attnsprefix = typemap["attnamespace"][typemap["attnamespace"].rfind("/") + 1:].replace("#","")
        else:
            attnsprefix="sunid"
        g.bind(nsprefix,dns)
        g.bind(attnsprefix, attns)
        g.bind("sf","http://www.opengis.net/ont/sf#")
        g.bind("om","http://www.ontology-of-units-of-measure.org/resource/om-2/")
        g.bind("qudt","http://qudt.org/schema/qudt#")
        if "language" in typemap:
            lang=typemap["language"]
        else:
            lang="en"
        if "class" in typemap:
            cls=typemap.get("class")
        else:
            cls="http://www.w3.org/ns/prov#Entity"
        if isinstance(cls,dict):
            thecls = URIRef(typemap.get("class").get("uri"))
            g.add((thecls, RDF.type, OWL.Class))
            if "labels" in typemap["class"]:
                for lan in typemap["class"]["labels"]:
                    g.add((thecls, RDFS.label, Literal(typemap["class"]["labels"][lan],lang=lan)))
        else:
            thecls = URIRef(typemap.get("class"))
            g.add((thecls, RDF.type, OWL.Class))
        rootcls=typemap.get("rootclass")
        if rootcls!=None:
            if isinstance(rootcls, dict):
                rootcls = URIRef(typemap.get("rootclass").get("uri"))
                g.add((rootcls, RDF.type, OWL.Class))
                g.add((thecls, RDFS.subClassOf, URIRef(rootcls)))
                if "labels" in typemap["rootclass"]:
                    for lan in typemap["rootclass"]["labels"]:
                        g.add((thecls, RDFS.label, Literal(typemap["rootclass"]["labels"][lan], lang=lan)))
            else:
                g.add((thecls, RDFS.subClassOf, URIRef(rootcls)))
                g.add((rootcls, RDF.type, OWL.Class))
        thecols=set(df.dtypes.to_dict().keys())
        rowcount=len(df)
        counter=0
        for row in df.to_dict(orient='records'):
            if idcol==None:
                curid=dns+str(counter)
            else:
                curid=dns+str(row[idcol])
            subclass=False
            seencols=set()
            if counter%100==0:
                print("ROW: "+str(counter)+"/"+str(rowcount))
            for x in typemap["columns"]:
                subclass = False
                intypemap=False
                res=processColumns("",seencols,x,curid,g,row,idcol,attns,thecls,lang,typemap)
                seencols=res["seencols"]
            counter+=1
            notseencols=thecols.symmetric_difference(seencols)
            for x in notseencols:
                if x in autotypemap["columns"] and x != idcol and x != "geometry":
                    curcol = autotypemap["columns"][x]
                    res = self.addPropertyToGraph(row, x, g, attns, curid, thecls, lang, curcol)
                    g = res[0]
                    subclass = res[1]
            if "addcolumns" in typemap:
                for addcol in typemap["addcolumns"]:
                    curcol=typemap["addcolumns"][addcol]
                    res = self.addPropertyToGraph(None, addcol, g, attns, curid, thecls, lang, curcol)
                    g = res[0]
                    subclass = res[1]
                #print(x)
            if subclass==False:
                g.add((URIRef(curid), RDF.type, thecls))
        return g

outpath=[]
dataexports=[]
filestoprocess = []

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", nargs='*', help="the input file(s) to parse [csv,shp,geojson,gml]", action="store", required=True)
parser.add_argument("-o", "--output", nargs='*', help="the output path(s)", action="store", required=True)
parser.add_argument("-m", "--mapping", nargs='*', help="the mapping file path(s)", action="store", required=True)
args, unknown=parser.parse_known_args()
print(args)
print("The following arguments were not recognized: " + str(unknown))
if args.input == None or args.input[0] == "None" or args.input == "":
    print("No input files specified... trying to find files in the script folder")
    exit()
if args.output == None or args.output[0] == "None" or args.input == "":
    print("No output paths specified...")
    exit()
for path in args.input:
    if " " in path:
        for itemm in path.split(" "):
            filestoprocess+=resolveWildcardPath(itemm)
    else:
        filestoprocess+=resolveWildcardPath(path)

g = Graph()
subrend=None

if path.endswith(".csv"):
    df = pd.read_csv(path, sep=";")
elif path.endswith(".geojson") or path.endswith(".shp") or path.endswith(".gml") or path.endswith(".kml"):
    df=gpd.read_file(path)

ddf=df.to_dict(orient='records')
conv=RDFConverter()
autotypemap = {"columns":{}}
for column in df:
    autotypemap["columns"][column] = conv.detectColumnType(df[column].to_dict())

if os.path.exists(args.mapping[0]):
    with open(args.mapping[0],"r") as f:
        typemap=json.load(f)
with open(str(args.output[0])+"/"+str(path[0:path.rfind(".")])+"autotypemap.json","w") as f:
    json.dump(autotypemap,f,indent=2,sort_keys=True)

g=conv.convertToRDF(df,typemap,autotypemap,g,True)
print("Serializing result to: "+str(path[0:path.rfind(".")]))
g.serialize(str(args.output[0])+"/"+path[0:path.rfind(".")]+".ttl",format="turtle")

