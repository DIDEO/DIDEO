## Script createDDIsGraphfromCSV.py reads drug-drug interactions in csv and creates a sample RDF graph wihich can be used for compose competency queries
## output graph will be generate in data folder

## Author: Yifan Ning, DBMI, University of Pittsburgh
## Date: 01/23/2014

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

reload(sys) 
sys.setdefaultencoding('UTF8')

INPUTDIR = "../import_files/pddi_csv_files/"
OUT_FILE = "../data/sampleDDIs.xml"
DRUGBANK_CHEBI = "../data/ChEBI_DRUGBANK_BIO2RDF.txt"


DRUGBANK_CHEBI_EXTRA = {"http://bio2rdf.org/drugbank:DB01118":"http://purl.obolibrary.org/obo/CHEBI_2663","http://bio2rdf.org/drugbank:DB00227":"http://purl.obolibrary.org/obo/CHEBI_40303","http://bio2rdf.org/drugbank:DB01026":"http://purl.obolibrary.org/obo/CHEBI_48339","http://bio2rdf.org/drugbank:DB00897":"http://purl.obolibrary.org/obo/CHEBI_9674","http://bio2rdf.org/drugbank:DB01167":"http://purl.obolibrary.org/obo/CHEBI_6076","http://bio2rdf.org/drugbank:DB01095":"http://purl.obolibrary.org/obo/CHEBI_38561","http://bio2rdf.org/drugbank:DB00196":"http://purl.obolibrary.org/obo/CHEBI_46081","http://bio2rdf.org/drugbank:DB01098":"http://purl.obolibrary.org/obo/CHEBI_38545","http://bio2rdf.org/drugbank:DB00682":"http://purl.obolibrary.org/obo/CHEBI_10033"}

def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')

def readCSVfromDir(inputdir):
    data = {}

    for file in os.listdir(inputdir):
        if file.endswith(".csv"):
            reader = csv.DictReader(utf_8_encoder(codecs.open(INPUTDIR + file,encoding='utf8')), delimiter=',', quotechar='"')
            for row in reader:
                data[row["id"]] = row 
                ## TODO: refill dict to merge ddis if necessary
    return data


# return the dict key: Drugbank URI, value: Chebi URI

def readDrugbankChEBIMapping(path):

    dict_drugbank_chebi = {}

    with codecs.open(path,'r',encoding='utf8') as f:
        reader = csv.reader(f, delimiter=',', quotechar='"')
        for row in reader:
            dict_drugbank_chebi[row[4]] = row[1]

    for k,v in DRUGBANK_CHEBI_EXTRA.items():
        dict_drugbank_chebi[k] = v

    return dict_drugbank_chebi
    


def createRDFGraph(dict_ddis):

    obo = Namespace('http://purl.obolibrary.org/obo/')
    rdf = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
    owl = Namespace('http://www.w3.org/2002/07/owl#')
    xsd = Namespace('http://www.w3.org/2001/XMLSchema#')
    rdfs = Namespace('http://www.w3.org/2000/01/rdf-schema#') 
    foaf= Namespace('http://xmlns.com/foaf/0.1/')
    #drugbank = Namespace('http://bio2rdf.org/drugbank:')

    ##TODO: temporarily using the namespace the same as OWL's 
    ## it's may need change "to http://purl.obolibrary.org/obo/"

    graph = Graph()

    graph.namespace_manager.reset()
    graph.namespace_manager.bind("obo", "http://purl.obolibrary.org/obo/")
    graph.namespace_manager.bind("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
    
    dict_drugbank_chebi = readDrugbankChEBIMapping(DRUGBANK_CHEBI)

    for k,v in dict_ddis.items():

        ddi_label = v["object"] + "-" + v["precipitant"] + "-" + k

        if dict_drugbank_chebi.has_key(v["drug1"]):
            chebi_uri1 = dict_drugbank_chebi[v["drug1"]]
        else:
            print "Chebi URI for drug %s is missing, skip interaction %s" % (v["object"], ddi_label)
            print "drugbank URI:" + v["drug1"]
            continue

        if dict_drugbank_chebi.has_key(v["drug2"]):
            chebi_uri2 = dict_drugbank_chebi[v["drug2"]]
        else:
            print "Chebi URI for drug %s is missing, skip interaction %s" % (v["precipitant"], ddi_label)
            print "drugbank URI:" + v["drug2"]
            continue

        graph.add((obo[ddi_label], rdfs["comment"], Literal(v["source"])))

        graph.add((obo[ddi_label], RDF.type, obo["DIDEO_00000000"]))

        graph.add((obo[ddi_label], obo["DIDEO_00000011"], URIRef(chebi_uri1)))
        graph.add((URIRef(chebi_uri1), RDF.type, obo["CHEBI_24431"]))
        graph.add((URIRef(chebi_uri1), RDF.type, obo["DIDEO_00000019"]))


        graph.add((obo[ddi_label], obo["DIDEO_00000014"], URIRef(chebi_uri2)))
        graph.add((URIRef(chebi_uri2), RDF.type, obo["CHEBI_24431"]))
        graph.add((URIRef(chebi_uri2), RDF.type, obo["DIDEO_00000019"]))


        if v["ddiPkMechanism"] and v["ddiPkMechanism"].strip() != "None":
            graph.add((obo[ddi_label], obo["DIDEO_00000022"], Literal(v["ddiPkMechanism"])))

        if v["managementOptions"] and v["managementOptions"].strip() != "None":
            graph.add((obo[ddi_label], obo["DIDEO_00000007"], Literal(v["managementOptions"])))

        if v["effectConcept"] and v["effectConcept"].strip() != "None":
            graph.add((obo[ddi_label], rdfs["comment"], Literal(v["effectConcept"])))

        if v["contraindication"] and v["contraindication"].strip() != "None":
            graph.add((obo[ddi_label], obo["OAE_0000055"], Literal(v["contraindication"])))

        if v["pathway"] and v["pathway"].strip() != "None":
            graph.add((obo[ddi_label], obo["GO_0008152"], Literal(v["pathway"])))

        if v["label"] and v["label"].strip() != "None": 
            graph.add((obo[ddi_label], rdfs["comment"], Literal(v["label"])))

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
