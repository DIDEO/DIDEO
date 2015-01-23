import sys
sys.path = sys.path + ['.']

import re, codecs, uuid, datetime
import urllib2
import urllib
import traceback
import csv
import difflib
import os
from os import path

## import RDF related
from rdflib import Graph, BNode, Literal, Namespace, URIRef, RDF, RDFS, XSD

INPUTDIR = "../import_files/pddi_csv_files/"
OUT_FILE = "../data/sampleDDIs.rdf"

def readCSVfromDir(inputdir):
    data = {}

    for file in os.listdir(inputdir):
        if file.endswith(".csv"):
            reader = csv.DictReader(open(INPUTDIR + file), delimiter=',', quotechar='"')
            for row in reader:
                data[row["id"]] = row 
                ## TODO: refill dict to merge ddis if necessary
    return data


def createRDFGraph(dict_ddis):

    base = Namespace('http://purl.obolibrary.org/obo/')
    rdf = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
    owl = Namespace('http://www.w3.org/2002/07/owl#')
    xsd = Namespace('http://www.w3.org/2001/XMLSchema#')
    rdfs = Namespace('http://www.w3.org/2000/01/rdf-schema#') 
    foaf= Namespace('http://xmlns.com/foaf/0.1/')
    #drugbank = Namespace('http://bio2rdf.org/drugbank:')

    ##TODO: temporarily using the namespace the same as OWL's 
    ## it's may need change "to http://purl.obolibrary.org/obo/"
    tmp = Namespace('http://127.0.0.1:3333/')


    graph = Graph()

    graph.namespace_manager.reset()
    graph.namespace_manager.bind("base", "http://purl.obolibrary.org/obo/")
    graph.namespace_manager.bind("tmp", "http://127.0.0.1:3333/")
    graph.namespace_manager.bind("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
    

    for k,v in dict_ddis.items():
        graph.add((tmp[k], base["object"], URIRef(v["drug1"])))
        graph.add((tmp[k], base["precipitant"], URIRef(v["drug2"])))

        if v["ddiPkMechanism"]:
            graph.add((tmp[k], base["ddiPkMechanism"], Literal(v["ddiPkMechanism"])))
        if v["label"]:
            graph.add((tmp[k], rdfs["comment"], Literal(v["label"])))
        if v["managementOptions"]:
            graph.add((tmp[k], base["managementOptions"], Literal(v["managementOptions"])))
        if v["effectConcept"]:
            graph.add((tmp[k], base["effectConcept"], Literal(v["effectConcept"])))


    # display the graph
    f = codecs.open(OUT_FILE,"w","utf8")

    s = graph.serialize(format="xml",encoding="utf8")
    f.write(unicode(s,errors='replace'))
    f.close
    graph.close()


def main():

    dict_ddis = readCSVfromDir(INPUTDIR)

    createRDFGraph(dict_ddis)

if __name__ == "__main__":
    main()
