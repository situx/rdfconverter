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

class BibTexToRDF:

    def bibtexToRDF(self,g,entries,ns,nsont,creatormode=None):
        typeToURI={"report":"http://purl.org/ontology/bibo/Report","incollection":"http://purl.org/ontology/bibo/Collection","inbook":"http://purl.org/ontology/bibo/BookSection","inproceedings":"http://purl.org/ontology/bibo/Proceedings","article":"http://purl.org/ontology/bibo/Article","book":"http://purl.org/ontology/bibo/Book","phdthesis":"http://purl.org/ontology/bibo/Thesis","misc":"http://purl.org/ontology/bibo/Document"}
        bibmap={}
        dsuri=None
        for entry in entries:
            bibmap[str(entry["ID"])[0:str(entry["ID"]).rfind("_")].replace("_"," ").strip()]=ns+"bib_"+str(entry["ID"])
            g.add((URIRef(ns+"bib_"+str(entry["ID"])), URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),URIRef(str(typeToURI[entry["ENTRYTYPE"]])))
            if creatormode!=None:
               g.add((URIRef(ns+"bib_"+str(entry["ID"])), URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), URIRef("http://www.w3.org/ns/dcat#Dataset")))
               dsuri=ns+"bib_"+str(entry["ID"])
            else:
                g.add((URIRef(ns+"bib_"+str(entry["ID"])), URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), URIRef(str(typeToURI[entry["ENTRYTYPE"]]))))
            g.add((URIRef(ns+"bib_"+str(entry["ID"])), URIRef("http://purl.org/dc/elements/1.1/title"), Literal(str(entry["title"]).replace("\"","'"),lang="en"))) 
            if "issn" in entry:
                g.add((URIRef(ns+"bib_"+str(entry["ID"])), URIRef("http://purl.org/ontology/bibo/issn"), Literal(str(entry["issn"]),datatype="http://www.w3.org/2001/XMLSchema#string")))
            if "eissn" in entry:
                g.add((URIRef(ns+"bib_"+str(entry["ID"]), URIRef("http://purl.org/ontology/bibo/eissn"), Literal(str(entry["eissn"]),datatype="http://www.w3.org/2001/XMLSchema#string")))
            if "isbn" in entry:
                g.add((URIRef(ns+"bib_"+str(entry["ID"])), URIRef("http://purl.org/ontology/bibo/isbn"), URIRef(str(entry["isbn"]),datatype="http://www.w3.org/2001/XMLSchema#string")))              
            if "number" in entry:
                g.add((URIRef(ns+"bib_"+str(entry["ID"])), URIRef("http://purl.org/ontology/bibo/number"), Literal(str(entry["number"]),datatype="http://www.w3.org/2001/XMLSchema#integer")))
            if "volume" in entry:
                g.add((URIRef(ns+"bib_"+str(entry["ID"])), URIRef("http://purl.org/ontology/bibo/volume"), Literal(str(entry["volume"]),datatype="http://www.w3.org/2001/XMLSchema#string")))
            if "publisher" in entry:
                if str(entry["publisher"]) in publishers:
                    g.add((URIRef(ns+"bib_"+str(entry["ID"])), URIRef("http://purl.org/dc/terms/publisher"), URIRef(publishers[str(entry["publisher"])])))
                    g.add((URIRef(publishers[str(entry["publisher"])]), URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), URIRef("http://xmlns.com/foaf/0.1/Organization")))
                    g.add((URIRef(publishers[str(entry["publisher"])]), URIRef("http://www.w3.org/2000/01/rdf-schema#label"), Literal(str(entry["publisher"]),lang="en")))
                else:
                    g.add((URIRef(ns+"bib_"+str(entry["ID"])), URIRef("http://purl.org/dc/terms/publisher"), Literal(str(entry["publisher"]))))
            if "journal" in entry:
                if entry["journal"] in issuers:
                    g.add((URIRef(ns+"bib_"+str(entry["ID"])), URIRef("http://purl.org/ontology/bibo/issuer") URIRef(issuers[str(entry["journal"])])))
                    g.add((URIRef(issuers[str(entry["journal"])]), URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), URIRef("http://purl.org/ontology/bibo/Journal")))
                    g.add((URIRef(issuers[str(entry["journal"])]),URIRef("http://www.w3.org/2000/01/rdf-schema#label"), Literal(str(entry["journal"]),lang="en")))
                else:
                    g.add((URIRef(ns+"bib_"+str(entry["ID"])), URIRef("http://purl.org/ontology/bibo/issuer"), Literal(str(entry["journal"]))))
            if "pages" in entry:
                if "--" in entry["pages"]:
                    pagestart=entry["pages"][0:entry["pages"].rfind("--")]
                    pageend=entry["pages"][entry["pages"].rfind("--")+2:]
                    g.add((URIRef(ns+"bib_"+str(entry["ID"])), URIRef("http://purl.org/ontology/bibo/pageStart"), Literal(str(pagestart),datatype="http://www.w3.org/2001/XMLSchema#integer")))
                    g.add((URIRef(ns+"bib_"+str(entry["ID"])), URIRef("http://purl.org/ontology/bibo/pageEnd"), Literal(str(pageend),datatype="http://www.w3.org/2001/XMLSchema#integer")))
            if "and" in entry["author"]:
                for author in entry["author"].split("and"):
                    if "," in author:
                        authoruri=str(author).replace(","," ").strip()
                        authoruri=authoruri.replace(" ","_")
                        authoruri=authoruri.replace("__","_")
                        authoruri=authoruri.strip()
                        g.add((URIRef(ns+"author_"+str(authoruri)), URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), URIRef("http://xmlns.com/foaf/0.1/Person")))
                        g.add((URIRef(ns+"author_"+str(authoruri)), URIRef("http://www.w3.org/2000/01/rdf-schema#label"), Literal(str(author).strip(),lang="en")))
                        g.add((URIRef(ns+"author_"+str(authoruri)), URIRef("http://xmlns.com/foaf/0.1/family_Name"), Literal(str(author)[0:str(author).rfind(',')].strip(),lang="en")))
                        g.add((URIRef(ns+"author_"+str(authoruri)), URIRef("http://xmlns.com/foaf/0.1/firstName"), Literal(str(author)[str(author).rfind(',')+1:].strip(),lang="en")))
                        g.add((URIRef(ns+"bib_"+str(entry["ID"])), URIRef("http://purl.org/dc/elements/1.1/creator"), URIRef(ns+"author_"+str(authoruri)))
            else:
                authoruri=str(entry["author"]).replace(","," ").strip()
                authoruri=authoruri.replace(" ","_")
                authoruri=authoruri.replace("__","_")
                authoruri=authoruri.strip()
                g.add((URIRef(ns+"author_"+str(authoruri)), URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), URIRef("http://xmlns.com/foaf/0.1/Person")))
                g.add((URIRef(ns+"author_"+str(authoruri)), URIRef("http://www.w3.org/2000/01/rdf-schema#label"), Literal(str(entry["author"]).strip(),lang="en")))
                g.add((URIRef(ns+"author_"+str(authoruri)), URIRef("http://xmlns.com/foaf/0.1/family_Name"), Literal(str(entry["author"])[0:str(entry["author"]).rfind(',')].strip(),lang="en")))
                g.add((URIRef(ns+"author_"+str(authoruri)), URIRef("http://xmlns.com/foaf/0.1/firstName"), Literal(str(entry["author"])[str(entry["author"]).rfind(',')+1:].strip(),lang="en")))
                g.add((URIRef(ns+"bib_"+str(entry["ID"])), URIRef("http://purl.org/dc/elements/1.1/creator"), URIRef(ns+"author_"+str(authoruri))))
            g.add((URIRef(ns+"bib_"+str(entry["ID"])), URIRef("http://purl.org/dc/elements/1.1/created"), Literal(str(entry["year"]), datatype="http://www.w3.org/2001/XMLSchema#gYear")))
            if "doi" in entry:
                g.add((URIRef(ns+"bib_"+str(entry["ID"])), URIRef("http://purl.org/ontology/bibo/doi"), Literal(str(entry["doi"]).replace("\_","_"),datatype="http://www.w3.org/2001/XMLSchema#string")))
    
        return {"triples":g,"bibmap":bibmap,"dsuri":dsuri}

    def processReference(self,g,bibmap,key,row,cururi):
        refs=row[key].split(";")
        for cref in refs:
            ref=cref.strip()
            if "," in cref:
                ref=cref[0:cref.rfind(",")].strip()
            if ref in bibmap:
                g.add((URIRef(str(cururi)),URIRef("http://purl.org/dc/terms/isReferencedBy"), URIRef(str(bibmap[ref]))))
                gotref=True
            elif ref.startswith("http"):
                g.add((URIRef(str(cururi)), URIRef("http://purl.org/dc/terms/isReferencedBy"), Literal(str(ref).strip(),datatype="http://www.w3.org/2001/XMLSchema#anyURI")))
            else:
                refnotfound.add(ref)
                g.add((URIRef(str(cururi)),URIRef("http://www.w3.org/2004/02/skos/core#note"), Literal(str(ref))))
                #print(row["DOC1_Papers"])
        if row[key] in bibmap:
            g.add((URIRef(str(cururi)), URIRef("http://purl.org/dc/terms/isReferencedBy"), URIRef(str(bibmap[row[key]]))))
            gotref=True
        elif ref.startswith("http"):
            g.add((URIRef(str(cururi)), URIRef("http://purl.org/dc/terms/isReferencedBy"), Literal(str(row[key]).strip(),datatype="http://www.w3.org/2001/XMLSchema#anyURI")))
        else:
            refnotfound.add(row[key])
            g.add((URIRef(str(cururi)),URIRef("http://www.w3.org/2004/02/skos/core#note"), Literal(str(row[key]))))
        return triples

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
        if "proplabels" in curcol and "en" in curcol["proplabels"]:
            propirilabel=str(curcol["proplabels"]["en"])
        else:
            propirilabel=str(x)
        prefix=curcol.get("prefix","")
        suffix=curcol.get("suffix","")
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
                    g.add((theiri, RDFS.label, Literal(propirilabel, lang="en")))
                    valueinstanceiri=curid+str("_")+str(theiri[theiri.rfind("/")+1:])+"_value"
                    g.add((URIRef(curid), theiri, URIRef(valueinstanceiri)))
                    g.add((URIRef(valueinstanceiri),RDF.type,URIRef("http://www.ontology-of-units-of-measure.org/resource/om-2/Measure")))
                    g.add((URIRef(valueinstanceiri), RDFS.label,Literal("Value Result of "+str(theiri[theiri.rfind("/")+1:])+" for "+str(curid))))
                    g.add((URIRef(valueinstanceiri), URIRef(unitprop),URIRef(unit)))
                    g.add((URIRef(valueinstanceiri), URIRef(unithasvalue), Literal(str(prefix)+str(sp)+str(suffix), datatype=URIRef(curcol["range"].replace("xsd:", "http://www.w3.org/2001/XMLSchema#")))))
                else:
                    g.add((theiri, RDF.type,OWL.DatatypeProperty)) 
                    g.add((theiri, RDFS.label, Literal(propirilabel, lang="en")))
                    g.add((URIRef(curid), theiri, Literal(str(prefix)+str(sp)+str(suffix), datatype=URIRef(
                        curcol["range"].replace("xsd:", "http://www.w3.org/2001/XMLSchema#")))))
        if curcol["prop"]=="obj":
            if "valuemapping" in curcol and row[x] in curcol["valuemapping"]:
                g.add((URIRef(curid), theiri, URIRef(curcol["valuemapping"][thevalue])))
                g.add((URIRef(curcol["valuemapping"][thevalue]),RDFS.label,Literal(thevalue,lang=lang)))
            elif thevalue.startswith("http"):
                g.add((theiri, RDF.type, OWL.ObjectProperty))
                g.add((theiri, RDFS.label, Literal(propirilabel, lang="en")))
                g.add((URIRef(curid), theiri, URIRef(thevalue)))
            else:
                g.add((URIRef(curid), theiri, Literal(thevalue,datatype=XSD.string)))
        if curcol["prop"]=="anno":
            g.add((theiri, RDF.type, OWL.AnnotationProperty))
            g.add((theiri, RDFS.label, Literal(propirilabel, lang="en")))
            g.add((URIRef(curid),theiri, Literal(str(prefix)+str(thevalue)+str(suffix), datatype=XSD.string)))
        if curcol["prop"] == "subclass":
            if "valuemapping" in curcol and row[x] in curcol["valuemapping"]:
                g.add((URIRef(curcol["valuemapping"][thevalue]), RDFS.subClassOf, thecls))
                #g.add((URIRef(curcol["valuemapping"][row[x]]), RDFS.subClassOf, OWL.Class))
                g.add((URIRef(curid), RDF.type, URIRef(curcol["valuemapping"][thevalue])))
                g.add((URIRef(curcol["valuemapping"][thevalue]),RDFS.label,Literal(thevalue,lang=lang)))
                subclass=True
            else:
                subclsuri=ns+thevalue.replace("/","").replace(" ","_")
                g.add((URIRef(subclsuri), RDFS.subClassOf, thecls))
                #g.add((URIRef(curcol["valuemapping"][row[x]]), RDFS.subClassOf, OWL.Class))
                g.add((URIRef(curid), RDF.type, URIRef(subclsuri)))
                g.add((URIRef(subclsuri),RDFS.label,Literal(thevalue,lang=lang)))
                subclass=True
        return [g,subclass]


    def processLatLonGeometry(g,lat,lon,typemap,curid):
        g.add((URIRef(curid), URIRef("http://www.opengis.net/ont/geosparql#hasGeometry"), URIRef(curid + "_geom")))
        g.add((URIRef("http://www.opengis.net/ont/geosparql#hasGeometry"), RDF.type, OWL.ObjectProperty))
        g.add((URIRef(curid + "_geom"), RDF.type, URIRef("http://www.opengis.net/ont/sf#Point")))
        g.add((URIRef("http://www.opengis.net/ont/sf#Point"), RDF.type, OWL.Class))
        g.add((URIRef("http://www.opengis.net/ont/sf#Point"), RDFS.subClassOf,
            URIRef("http://www.opengis.net/ont/geosparql#Geometry")))
        g.add((URIRef("http://www.opengis.net/ont/geosparql#Geometry"), RDF.type, OWL.Class))
        g.add((URIRef(curid + "_geom"), RDFS.label, Literal("Geometry of " + str(curid), lang="en")))
        g.add((URIRef("http://www.opengis.net/ont/geosparql#asWKT"), RDF.type, OWL.DatatypeProperty))
        if "epsg" in typemap:
            g.add((URIRef(curid + "_geom"), URIRef("http://www.opengis.net/ont/geosparql#asWKT"),
                Literal("<http://www.opengis.net/def/crs/EPSG/0/" + str(typemap["epsg"]) + "> POINT("+str(lon)+" "+str(lat)+")",
                        datatype="http://www.opengis.net/ont/geosparql#wktLiteral")))
        else:
            g.add((URIRef(curid + "_geom"), URIRef("http://www.opengis.net/ont/geosparql#asWKT"),
                Literal("POINT("+str(lon)+" "+str(lat)+")", datatype="http://www.opengis.net/ont/geosparql#wktLiteral")))
        return g
    
    def processColumns(self,prefix,seencols,x,curid,g,row,idcol,attns,thecls,lang,typemap):
        processedGeom=False
        for x in typemap["columns"]:
            # print("CConfig: "+str(x))
            subclass = False
            intypemap = False
            if "ignore" in typemap["columns"][x] and typemap["columns"][x]["ignore"] == True:
                seencols.add(x)
                continue
            if processedGeom==False:
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
                    processedGeom=True
                elif x=="latitude" and "longitude" in row:
                    self.processLatLonGeometry(g,row["latitude"],row["longitude"],typemap,curid)
                    processedGeom=True
                elif x=="Latitude" and "Longitude" in row:
                    self.processLatLonGeometry(g,row["Latitude"],row["Longitude"],typemap,curid)
                    processedGeom=True
                elif x=="lat" and "lon" in row:
                    self.processLatLonGeometry(g,row["lat"],row["lon"],typemap,curid)
                    processedGeom=True
            if "collection" in typemap["columns"][x] and typemap["columns"][x]["collection"] == True and "columns" in typemap["columns"][x]:
                if "propiri" in typemap["columns"][x]:
                    theiri = URIRef(typemap["columns"][x]["propiri"])
                else:
                    theiri = URIRef(attns + x)
                if prefix!="":
                    res = self.processColumns(str(prefix) + "." + str(x), seencols, x, str(curid)+"_"+str(x), g, row, idcol,attns, thecls, lang, typemap["columns"][x])
                    g.add((URIRef(curid),URIRef(theiri),URIRef(str(curid)+"_"+str(x))))
                    g.add((URIRef(curid), URIRef(theiri), URIRef(str(curid) + "_" + str(x)),RDFS.label,Literal(str(curid)+"_"+str(x))))
                else:
                    res=self.processColumns(str(x),seencols,x,str(curid)+"_"+str(x),g,row,idcol,attns,thecls,lang,typemap["columns"][x])
                    g.add((URIRef(curid), URIRef(theiri), URIRef(str(curid)+"_"+str(x))))
                    g.add((URIRef(str(curid) + "_" + str(x)),RDFS.label,Literal(str(curid)+"_"+str(x))))
                g=res["graph"]
                seencols=res["seencols"]
            if "join" in typemap["columns"][x] and typemap]["columns"][x]["join"]=true and "columns" in typemap["columns"][x]:
                thejoincol=typemap["columns"][x]
                for col in thejoincol["columns"]:
                    
                    
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
        onlyschema=False
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
            nsprefix="sunid"
        if "attnamespace" in typemap:
            attnsprefix = typemap["attnamespace"][typemap["attnamespace"].rfind("/") + 1:].replace("#","")
        else:
            attnsprefix="suni"
        if "onlyschema" in typemap and typemap["onlyschema"]==True:
            onlyschema=True
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
        clsmappings=[]
        if "classmappings" in typemap:
            clsmappings=typemap["classmappings"]
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
            if "classmappings" in typemap:
                for clsmap in typemap["classmappings"]:
                    print(clsmap)
                    g.add((URIRef(curid),RDF.type,URIRef(clsmap["uri"])))
                    if "labels" in clsmap:
                        for lab in clsmap["labels"]:
                            g.add((URIRef(curid),RDFS.label,Literal(clsmap["labels"][lab],lang=lab)))
            for x in typemap["columns"]:
                subclass = False
                intypemap=False
                res=self.processColumns("",seencols,x,curid,g,row,idcol,attns,thecls,lang,typemap)
                seencols=res["seencols"]
            counter+=1
            notseencols=thecols.symmetric_difference(seencols)
            if onlyschema==False:
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
parser.add_argument("-s", "--sepchar", nargs='*', help="csv file separator", action="store", required=False,default=";")
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
    df = pd.read_csv(path, sep=args.sepchar[0])
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
if not os.path.exists(args.output[0]):
    os.makedirs(args.output[0])
with open(str(args.output[0])+"/"+str(path[0:path.rfind(".")]).replace("/","_")+"_"+str(args.mapping[0][0:args.mapping[0].rfind(".")]).replace("/","_")+"_autotypemap.json","w") as f:
    json.dump(autotypemap,f,indent=2,sort_keys=True)

g=conv.convertToRDF(df,typemap,autotypemap,g,True)
print("Serializing result to: "+str(path[0:path.rfind(".")].replace("/","_")))
g.serialize(str(args.output[0])+"/"+path[0:path.rfind(".")].replace("/","_")+"_"+str(args.mapping[0][0:args.mapping[0].rfind(".")]).replace("/","_")+".ttl",format="turtle")

