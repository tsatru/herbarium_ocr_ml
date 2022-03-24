from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import psycopg2
import MySQLdb
import pandas as pd


user_pg = "tania"
passwd_pg = "tania.ccud"




db_pg = psycopg2.connect(host="localhost",
                         database="mlproject",
                         user=user_pg,
                         password=passwd_pg)


alp_pg = psycopg2.connect(host="localhost",
                         database="alphatole",
                         user=user_pg,
                         password=passwd_pg)


catalogo_col = pd.read_sql_query("SELECT id, recordedby FROM ccud_data_work.catalogo_recordedby", alp_pg)



to_fw = pd.read_sql_query("SELECT * FROM public.rby_to_fuzzywuzzy", db_pg)



col_w = catalogo_col.drop_duplicates(['recordedby'], keep=False)


to_fw['clean_text'] = to_fw['array_to_string'].str.translate(str.maketrans("", "", "®©_=~}¥-<>§|*¢+)"))



def fuzzy_extract(x, choices, scorer, cutoff):
    return process.extractOne(
        x, choices=choices, scorer=scorer, score_cutoff=cutoff
    )


to_fw['fw_result'] = to_fw['clean_text'].apply(
    fuzzy_extract,
    args=(
        col_w['recordedby'], 
        fuzz.ratio,
        40
    )
)