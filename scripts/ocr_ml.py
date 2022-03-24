import MySQLdb
import pandas as pd
from math import pow 
import numpy as np
from sklearn import svm
from sklearn import cross_validation
from sklearn import grid_search
import pickle
import psycopg2
from bs4 import BeautifulSoup
import os.path
import urllib
from subprocess import call
import glob #módulo glob (hace listas de archivos a partir de búsquedas en directorios)
from PIL import Image
from sqlalchemy import create_engine
#from datetime import datetime
#import cStringIO   #for file-like objects
#import numpy as np
#from pandas import *
#import pandas.io.sql as psql
#from sql import *
#from config import config

user_pg = "tania"
passwd_pg = "tania.ccud"
db_pg = "mlproject"


db_pg = psycopg2.connect(host="localhost",
                         database="mlproject",
                         user=user_pg,
                         password=passwd_pg)

cur = db_pg.cursor()

sql =  """  
       CREATE TABLE public.ocred_records_raw AS \
       SELECT NULLIF(i.originalurl, i.url) as url, r.rawstr, o.* \
       FROM public.images i INNER JOIN public.specprocessorrawlabels r ON i.imgid = r.imgid \
       INNER JOIN public.omoccurrences o ON i.occid = o.occid \
       WHERE o.processingstatus IS NULL OR o.processingstatus != 'unprocessed'
       """  

cur.execute(sql)
db_pg.commit()

cur.execute("DROP INDEX IF EXISTS public.raw_occid;")
cur.execute("CREATE INDEX raw_occid ON ocred_records_raw(occid);")
db_pg.commit()

cur.close()
db_pg.close()





#from bs4 import BeautifulSoup    #importa módulo bs4 que analiza archivos XML y HTML
#dónde esta declarada la variable
def parse_title(title):    #se define la función parse_title que recibe title 
    start = title.find("bbox ") + 5   #encuentra el inicio del título y agrega "bbox " 
    end = title.find(";")  #encuentra el final del título y agrega ";" 
    if end < 0: end = len(title)   # el número de items en una secuencia
    s = title[start:end].split()  #devuelve el título concatenado 
    #print start, end, s
    return {"x0": s[0], "y0": s[1], "x1": s[2], "y1": s[3]}  #devuelve el contenido de "s" en diferentes variables 



def parse_hocr(hocr_fn): #se define función "parse_hocr" que recibe fn 
    soup = BeautifulSoup(open(hocr_fn), 'html.parser')
    #soup = BeautifulSoup(hocr_fn,'html.parser')
    #soup = BeautifulSoup(open(hocr_fn), "xml")   #recorre fn
    words_list = []  #se crea una lista

#find.all: método de búsqueda a través del DOM, recorre descendentemente la etiqueta de acuerdo al criterio de búsqueda
    for a in soup.find_all(class_="ocr_carea"):  #busca dentro de soup la clase = "ocr_carea"
        bbox_area = parse_title(a["title"]) #recorre el título de los elementos de "a" 
        lines = a.find_all(class_="ocr_line") #busca dentro de "a" la clase = "ocr_line"
        for l in lines: 
            bbox_line = parse_title(l["title"]) #recorre el título dentro de cada uno de los elemntos de line
            words = l.find_all(class_="ocrx_word") #busca dentro de "l" la clase = "ocrx_word"
            for w in words:
                bbox_word = parse_title(w["title"]) #recorre el título dentro de cada uno de los elemntos de words
                word_dict = { "area_id": a["id"],   #crea un diccionario a partir de claves que corresponden a los campos de la tabla hocr_results
                              "line_id": l["id"],
                              "word_id": w["id"],
                              "text": w.get_text(),
                              "area_x0": bbox_area["x0"],
                              "area_y0": bbox_area["y0"],
                              "area_x1": bbox_area["x1"],
                              "area_y1": bbox_area["y1"],
                              "line_x0": bbox_line["x0"],
                              "line_y0": bbox_line["y0"],
                              "line_x1": bbox_line["x1"],
                              "line_y1": bbox_line["y1"],
                              "word_x0": bbox_word["x0"],
                              "word_y0": bbox_word["y0"],
                              "word_x1": bbox_word["x1"],
                              "word_y1": bbox_word["y1"]
                            }
                words_list.append(word_dict)    #pasa los objetos de word_dict a word_list

    return words_list




dest = "/media/tania/Seagate Expansion Drive/colectores/colectores_hocr" #cambia por cada proceso  


#user = "tania"
#password = "tania.ccud"
#db = "mlproject"
#source_db = "symblichens"

db_pg = psycopg2.connect(host="localhost",
                         database="mlproject",
                         user=user_pg,
                         password=passwd_pg)


cur = db_pg.cursor()
#df_hocr_results = pd.read_sql_query("SELECT * FROM public.hocr_results", db_pg)
#por el momento sólo funciona en mysql, en postgresql aún np se puede crear 
#schm_hocr_results = get_schema(df_hocr_results, 'hocr_results', 'mysql')
#para crear la tabla hocr_results
#cur.execute(schm_hocr_results)


rec = True

while rec:
    sql = 'SELECT r.occid, r.catalogNumber, r.url \
           FROM public.ocred_records_raw r \
           LEFT JOIN public.hocr_results h \
           ON r.occid = h.occid \
           WHERE h.occid IS NULL \
           LIMIT 1'
    cur.execute(sql)  #
    rec = cur.fetchone()  #devuelve el registro resultado de la query como tupla, si no hay mas datos devuelve error
    #print rec
    occid = rec[0] #de
    catalogNumber = rec[1]
    url = rec[2]

    # Mark as processing
    cur.execute("INSERT INTO public.hocr_results (occid, processed) VALUES (%s, 1);", (occid,))
    db_pg.commit()   #
    
    #se crea carpeta images y hocr
    img_fn = url.split('/')[-1] #divide la url y devuelve el último elemento
    img_full_fn = dest + "/images/" + img_fn   #concatena dest, string, imf_fn
    hocr_full_fn = dest + "/hocr/" + img_fn.split('.')[0] #concatena dest, string, y la primera partícula que devuelve el split de img_fn 
    if not os.path.isfile(img_full_fn): #sí el path no existe en nuestro directorio, entonces: 
        try:  # run this code
            resp = urllib.urlretrieve(url, filename=img_full_fn) #gurada la imagen en la carpeta images que viene de la url definida anteriormente 
            print "Performing OCR on " + img_fn #imprime string concatenado con img_fn 
            call(["tesseract", img_full_fn, hocr_full_fn, "hocr"]) #llama el hocr
            parsed = parse_hocr(hocr_full_fn + ".hocr") #recorre el hocr, además agrega la cadena ".hocr"
            for p in parsed:   #para cada uno de los valores de parsed
                sql = "INSERT INTO hocr_results \
                       (occid, catalogNumber, area_id, line_id, word_id, text, \
                       area_x0, area_y0, area_x1, area_y1, line_x0, line_y0, \
                       line_x1, line_y1, word_x0, word_y0 ,word_x1, word_y1, \
                       processed, filename) \
                       VALUES \
                       (%s, %s, %s, %s, %s, %s, \
                       %s, %s, %s, %s, %s, %s, \
                       %s, %s, %s, %s ,%s, %s, \
                       %s, %s) \
                      "
#                cur.execute(sql, p.update({"occid":occid, "occurrenceID":occurrenceID, "processed":2}))
#                sql = """UPDATE hocr_results
#                         SET
#                         processed=2, catalogNumber=%s, area_id=%s, line_id=%s, 
#                         word_id=%s, text=%s, area_x0=%s, area_y0=%s, area_x1=%s, area_y1=%s,
#                         line_x0=%s, line_y0=%s, line_x1=%s, line_y1=%s, word_x0=%s, 
#                         word_y0=%s, word_x1=%s, word_y1=%s
#                         WHERE occid=%s
#                      """
                cur.execute(sql, (occid, catalogNumber, p["area_id"], p["line_id"], \
                            p["word_id"], p["text"], p["area_x0"], p["area_y0"], p["area_x1"], p["area_y1"], \
                            p["line_x0"], p["line_y0"], p["line_x1"], p["line_y1"], p["word_x0"], \
                            p["word_y0"], p["word_x1"], p["word_y1"], 2, img_fn))

            cur.execute("DELETE FROM hocr_results WHERE occid=%s AND processed=1", (occid,))
            db_pg.commit()
        except:
            pass   




#falta agregar el directorio de images 

i = 0  
for f in glob.glob("images/*"): #extrae de nuestro directorio la lista de imagenes 
    try:
    #f = "images/NY01406176_lg.jpg"
        fn = f[7:]
        im = Image.open(f) #abre la imagen*
        s = im.size #devuelve el tamaño de la imagen
    # print(f)
    

        sql = """
          UPDATE public.hocr_results
          SET x = %s, y = %s
          WHERE filename = %s
          """
        cur.execute(sql, (s[0], s[1], fn))   

        if i % 100 == 0: #operador de módulo 
            db_pg.commit() #==permite comparar dos valores

        i = i + 1
    except IOError:
        print("cannot identify image file", f)
        pass

db_pg.commit() #para finalizar los cambios 
db_pg.close()




pg_engine='postgresql+psycopg2://localhost:5432/mlproject'
df_hocr_results = pd.read_sql_query("SELECT * FROM public.hocr_results", pg_engine)
df_ocred = pd.read_sql_query("SELECT * FROM public.ocred_records_raw", pg_engine)
pg_engine.close()

#pg_engine='postgresql+psycopg2://localhost:5432/mlproject'
my_engine='mysql+mysqldb://root:tAn1a.ccud@localhost/mlproject?charset=utf8mb4'

df_hocr_results.to_sql("hocr_results", my_engine)

df_ocred.to_sql("ocred_records_raw", my_engine)

user = "root"
passwd = "tAn1a.ccud"

db = MySQLdb.connect(host="localhost",
                     user=user,
                     passwd=passwd,
                     db="mlproject")

cur_mysql = db.cursor()


cur_mysql.execute("CREATE INDEX raw_occid ON hocr_results(occid);")
cur_mysql.execute("CREATE INDEX hocr_fn ON hocr_results(filename);")
cur_mysql.execute("CREATE INDEX rw_occid ON ocred_records_raw(occid);")




   
cur_mysql.execute("CREATE TABLE \
            data_labels \
            SELECT \
            h.id, h.occid, h.text, \
            if(LOCATE(TRIM(UPPER(h.text)), UPPER(r.family)), r.family, NULL) as in_family, \
            if(LOCATE(TRIM(UPPER(h.text)), UPPER(r.recordedby)), r.recordedby, NULL) as in_recordedby, \
            if(LOCATE(TRIM(UPPER(h.text)), UPPER(r.verbatimeventdate)), r.verbatimeventdate, NULL) as in_verbatimeventdate, \
            if(LOCATE(TRIM(UPPER(h.text)), UPPER(r.recordnumber)), r.recordnumber, NULL) as in_recordnumber, \
            if(LOCATE(TRIM(UPPER(h.text)), UPPER(r.country)), r.country, NULL) as in_country, \
            if(LOCATE(TRIM(UPPER(h.text)), UPPER(r.stateprovince)), r.stateprovince, NULL) as in_stateprovince, \
            if(LOCATE(TRIM(UPPER(h.text)), UPPER(r.county)), r.county, NULL) as in_county, \
            if(LOCATE(TRIM(UPPER(h.text)), UPPER(r.verbatimlatitude)), r.verbatimlatitude, NULL) as in_verbatimlatitude, \
            if(LOCATE(TRIM(UPPER(h.text)), UPPER(r.verbatimlongitude)), r.verbatimlongitude, NULL) as in_verbatimlongitude, \
            if(LOCATE(TRIM(UPPER(h.text)), UPPER(r.lifestage)), r.lifestage, NULL) as in_lifestage, \
            if(LOCATE(TRIM(UPPER(h.text)), UPPER(r.rcby_rf)), r.rcby_rf, NULL) as in_rcby_rf, \
            if(LOCATE(TRIM(UPPER(h.text)), UPPER(r.rcby_svm)), r.rcby_svm, NULL) as in_rcby_svm, \
            if(LOCATE(TRIM(UPPER(h.text)), UPPER(r.rcby_nn)), r.rcby_nn, NULL) as in_rcby_nn, \
            if(LOCATE(TRIM(UPPER(h.text)), UPPER(r.rcby_knn)), r.rcby_knn, NULL) as in_rcby_knn, \
            if(LOCATE(TRIM(UPPER(h.text)), UPPER(r.rcby_log)), r.rcby_log, NULL) as in_rcby_log \
            FROM \
            hocr_results h JOIN ocred_records_raw r ON h.occid = r.occid \
            WHERE \
            LENGTH(h.text) > 1;")  





df_labels = pd.read_sql_query("SELECT * FROM data_labels", my_engine)

pg_engine='postgresql+psycopg2://localhost:5432/mlproject'

df_labels.to_sql("data_labels", pg_engine)



db_pg = psycopg2.connect(host="localhost",
                         database="mlproject",
                         user=user_pg,
                         password=passwd_pg)

cur = db_pg.cursor()
#para crear la tabla 
#cur.execute(schm_labels)
#
#cur.close()
#db_pg.close()





cur.execute("""
            CREATE TABLE  \
            word_label AS \ 
            SELECT \
            id, occid, text, \
            CASE in_family IS NOT NULL AND in_recordedby IS NULL AND in_verbatimeventdate IS NULL AND in_recordnumber IS NULL AND in_country IS NULL AND in_stateprovince IS NULL AND in_county IS NULL AND in_verbatimlatitude IS NULL AND in_verbatimlongitude IS NULL AND in_lifestage IS NULL AND in_rcby_rf IS NULL AND in_rcby_svm IS NULL AND in_rcby_nn IS NULL AND in_rcby_knn IS NULL AND in_rcby_log IS NULL  \
            WHEN true THEN \
            'family' \
            ELSE \
            CASE in_family IS NULL AND in_recordedby IS NOT NULL AND in_verbatimeventdate IS NULL AND in_recordnumber IS NULL AND in_country IS NULL AND in_stateprovince IS NULL AND in_county IS NULL AND in_verbatimlatitude IS NULL AND in_verbatimlongitude IS NULL AND in_lifestage IS NULL AND in_rcby_rf IS NULL AND in_rcby_svm IS NULL AND in_rcby_nn IS NULL AND in_rcby_knn IS NULL AND in_rcby_log IS NULL  \
            WHEN true THEN \
            'recordedby'\
            ELSE \
            CASE in_family IS NULL AND in_recordedby IS NULL AND in_verbatimeventdate IS NOT NULL AND in_recordnumber IS NULL AND in_country IS NULL AND in_stateprovince IS NULL AND in_county IS NULL AND in_verbatimlatitude IS NULL AND in_verbatimlongitude IS NULL AND in_lifestage IS NULL AND in_rcby_rf IS NULL AND in_rcby_svm IS NULL AND in_rcby_nn IS NULL AND in_rcby_knn IS NULL AND in_rcby_log IS NULL  \
            WHEN true THEN \
            'verbatimeventdate' \
            ELSE \
            CASE in_family IS NULL AND in_recordedby IS NULL AND in_verbatimeventdate IS NULL AND in_recordnumber IS NOT NULL AND in_country IS NULL AND in_stateprovince IS NULL AND in_county IS NULL AND in_verbatimlatitude IS NULL AND in_verbatimlongitude IS NULL AND in_lifestage IS NULL AND in_rcby_rf IS NULL AND in_rcby_svm IS NULL AND in_rcby_nn IS NULL AND in_rcby_knn IS NULL AND in_rcby_log IS NULL \
            WHEN true THEN \
            'recordnumber' \
            ELSE \
            CASE in_family IS NULL AND in_recordedby IS NULL AND in_verbatimeventdate IS NULL AND in_recordnumber IS NULL AND in_country IS NOT NULL AND in_stateprovince IS NULL AND in_county IS NULL AND in_verbatimlatitude IS NULL AND in_verbatimlongitude IS NULL AND in_lifestage IS NULL AND in_rcby_rf IS NULL AND in_rcby_svm IS NULL AND in_rcby_nn IS NULL AND in_rcby_knn IS NULL AND in_rcby_log IS NULL \
            WHEN true THEN \
            'country' \
            ELSE \
            CASE in_family IS NULL AND in_recordedby IS NULL AND in_verbatimeventdate IS NULL AND in_recordnumber IS NULL AND in_country IS NULL AND in_stateprovince IS NOT NULL AND in_county IS NULL AND in_verbatimlatitude IS NULL AND in_verbatimlongitude IS NULL AND in_lifestage IS NULL AND in_rcby_rf IS NULL AND in_rcby_svm IS NULL AND in_rcby_nn IS NULL AND in_rcby_knn IS NULL AND in_rcby_log IS NULL \
            WHEN true THEN \
            'stateprovince' \
            ELSE \
            CASE in_family IS NULL AND in_recordedby IS NULL AND in_verbatimeventdate IS NULL AND in_recordnumber IS NULL AND in_country IS NULL AND in_stateprovince IS NULL AND in_county IS NOT NULL AND in_verbatimlatitude IS NULL AND in_verbatimlongitude IS NULL AND in_lifestage IS NULL AND in_rcby_rf IS NULL AND in_rcby_svm IS NULL AND in_rcby_nn IS NULL AND in_rcby_knn IS NULL AND in_rcby_log IS NULL \
            WHEN true THEN \
            'county' \
            ELSE \
            CASE in_family IS NULL AND in_recordedby IS NULL AND in_verbatimeventdate IS NULL AND in_recordnumber IS NULL AND in_country IS NULL AND in_stateprovince IS NULL AND in_county IS NULL AND in_verbatimlatitude IS NOT NULL AND in_verbatimlongitude IS NULL AND in_lifestage IS NULL AND in_rcby_rf IS NULL AND in_rcby_svm IS NULL AND in_rcby_nn IS NULL AND in_rcby_knn IS NULL AND in_rcby_log IS NULL \
            WHEN true THEN \
            'verbatimlatitude' \
            ELSE \
            CASE in_family IS NULL AND in_recordedby IS NULL AND in_verbatimeventdate IS NULL AND in_recordnumber IS NULL AND in_country IS NULL AND in_stateprovince IS NULL AND in_county IS NULL AND in_verbatimlatitude IS NULL AND in_verbatimlongitude IS NOT NULL AND in_lifestage IS NULL AND in_rcby_rf IS NULL AND in_rcby_svm IS NULL AND in_rcby_nn IS NULL AND in_rcby_knn IS NULL AND in_rcby_log IS NULL \
            WHEN true THEN \
            'verbatimlongitude' \
            ELSE \
            CASE in_family IS NULL AND in_recordedby IS NULL AND in_verbatimeventdate IS NULL AND in_recordnumber IS NULL AND in_country IS NULL AND in_stateprovince IS NULL AND in_county IS NULL AND in_verbatimlatitude IS NULL AND in_verbatimlongitude IS NULL AND in_lifestage IS NOT NULL AND in_rcby_rf IS NULL AND in_rcby_svm IS NULL AND in_rcby_nn IS NULL AND in_rcby_knn IS NULL AND in_rcby_log IS NULL \
            WHEN true THEN \
            'lifestage' \
            ELSE \
            CASE in_family IS NULL AND in_recordedby IS NULL AND in_verbatimeventdate IS NULL AND in_recordnumber IS NULL AND in_country IS NULL AND in_stateprovince IS NULL AND in_county IS NULL AND in_verbatimlatitude IS NULL AND in_verbatimlongitude IS NULL AND in_lifestage IS NULL AND in_rcby_rf IS NOT NULL AND in_rcby_svm IS NULL AND in_rcby_nn IS NULL AND in_rcby_knn IS NULL AND in_rcby_log IS NULL \
            WHEN true THEN \
            'rcby_rf' \
		   ELSE \
            CASE in_family IS NULL AND in_recordedby IS NULL AND in_verbatimeventdate IS NULL AND in_recordnumber IS NULL AND in_country IS NULL AND in_stateprovince IS NULL AND in_county IS NULL AND in_verbatimlatitude IS NULL AND in_verbatimlongitude IS NULL AND in_lifestage IS NULL AND in_rcby_rf IS NULL AND in_rcby_svm IS NOT NULL AND in_rcby_nn IS NULL AND in_rcby_knn IS NULL AND in_rcby_log IS NULL \
            WHEN true THEN \
            'rcby_svm' \
		   ELSE \
            CASE in_family IS NULL AND in_recordedby IS NULL AND in_verbatimeventdate IS NULL AND in_recordnumber IS NULL AND in_country IS NULL AND in_stateprovince IS NULL AND in_county IS NULL AND in_verbatimlatitude IS NULL AND in_verbatimlongitude IS NULL AND in_lifestage IS NULL AND in_rcby_rf IS NULL AND in_rcby_svm IS NULL AND in_rcby_nn IS NOT NULL AND in_rcby_knn IS NULL AND in_rcby_log IS NULL \
            WHEN true THEN \
            'rcby_nn' \
		   ELSE \
            CASE in_family IS NULL AND in_recordedby IS NULL AND in_verbatimeventdate IS NULL AND in_recordnumber IS NULL AND in_country IS NULL AND in_stateprovince IS NULL AND in_county IS NULL AND in_verbatimlatitude IS NULL AND in_verbatimlongitude IS NULL AND in_lifestage IS NULL AND in_rcby_rf IS NULL AND in_rcby_svm IS NULL AND in_rcby_nn IS NULL AND in_rcby_knn IS NOT NULL AND in_rcby_log IS NULL \
            WHEN true THEN \
            'rcby_knn' \
		   ELSE \
            CASE in_family IS NULL AND in_recordedby IS NULL AND in_verbatimeventdate IS NULL AND in_recordnumber IS NULL AND in_country IS NULL AND in_stateprovince IS NULL AND in_county IS NULL AND in_verbatimlatitude IS NULL AND in_verbatimlongitude IS NULL AND in_lifestage IS NULL AND in_rcby_rf IS NULL AND in_rcby_svm IS NULL AND in_rcby_nn IS NULL AND in_rcby_knn IS NULL AND in_rcby_log IS NOT NULL \
            WHEN true THEN \
            'rcby_log' \
            ELSE \
            NULL \
            END  \
            END  \
            END \
            END \
            END \
            END \
            END \
            END \
            END \
            END \
            END \
            END \
            END \
            END \
            as label \
            FROM \
            data_labels \
            WHERE \
            LENGTH(TRIM(text)) > 1 ;""")


cur.execute("SELECT * FROM word_label;")

cur.execute("CREATE INDEX word_label_id ON word_label(id);")
cur.execute("CREATE INDEX word_label_occid ON word_label(occid);")

cur.execute("CREATE TABLE \
            text_extent AS \
            SELECT \
            occid, \
            min(area_x0) as min_area_x0, \
            min(area_y0) as min_area_y0, \
            max(area_x1) as max_area_x1, \
            max(area_y1) as max_area_y1, \
            min(line_x0) as min_line_x0, \
            min(line_y0) as min_line_y0, \
            max(line_x1) as max_line_x1, \
            max(line_y1) as max_line_y1, \
            min(word_x0) as min_word_x0, \
            min(word_y0) as min_word_y0, \
            max(word_x1) as max_word_x1, \
            max(word_y1) as max_word_y1 \
            FROM \
            hocr_results \
            WHERE \
            x > 100 \
            AND y > 100 \
            AND area_x0 > 10 \
            AND area_y0 > 10 \
            AND area_x1 < (x - 10) \
            AND area_y1 < (y - 10) \
            AND line_x0 > 10  \
            AND line_y0 > 10  \
            AND line_x1 < (x - 10) \
            AND line_y1 < (y - 10) \
            AND word_x0 > 10 \
            AND word_y0 > 10 \
            AND word_x1 < (x - 10) \
            AND word_y1 < (y - 10) \
            AND LENGTH(TRIM(text))>1 GROUP BY occid;")

cur.execute("CREATE INDEX text_extent_occid ON text_extent(occid);")



df_labels = pd.read_sql_query("SELECT * FROM data_labels", my_engine)

pg_engine='postgresql+psycopg2://localhost:5432/mlproject'

df_labels.to_sql("data_labels", pg_engine)






cur.execute("CREATE TABLE \
            input AS \
            SELECT DISTINCT \
            l.id, l.occid, l.text, l.label, \
            (r.area_x0 - e.min_area_x0) / (e.max_area_x1 - e.min_area_x0) as scaled_area_x0, \
            (r.area_y0 - e.min_area_y0) / (e.max_area_y1 - e.min_area_y0) as scaled_area_y0, \
            (r.line_x0 - e.min_line_x0) / (e.max_line_x1 - e.min_line_x0) as scaled_line_x0, \
            (r.line_y0 - e.min_line_y0) / (e.max_line_y1 - e.min_line_y0) as scaled_line_y0, \
            (r.word_x0 - e.min_word_x0) / (e.max_word_x1 - e.min_word_x0) as scaled_word_x0, \
            (r.word_y0 - e.min_word_y0) / (e.max_word_y1 - e.min_word_y0) as scaled_word_y0 \
            FROM \
            word_label l \
            JOIN text_extent e \
            JOIN hocr_results r \
            ON \
            l.occid = e.occid \
            AND l.id = r.id \
            WHERE l.label IS NOT NULL \
            AND r.area_x0 > e.min_area_x0 \
            AND r.area_y0 > e.min_area_y0 \
            AND r.line_x0 > e.min_line_x0 \
            AND r.line_y0 > e.min_line_y0 \
            AND r.word_x0 > e.min_word_x0 \
            AND r.word_y0 > e.min_word_y0;")




