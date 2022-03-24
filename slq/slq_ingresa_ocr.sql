
CREATE TABLE "public"."images" (
  "imgid" SERIAL PRIMARY KEY,
  "originalurl" text,
  "url" text,
  "occid" varchar(32)
);




CREATE TABLE "public"."omoccurrences" 
(
  processingstatus text,
  catalogNumber text,
  recordedby_wk text,
  recordedby_wk_o text,
  recordedby_bkp text,
  recorded_by_pda text,
  verbatimeventdate_wk text,
  verbatimeventdate_wk_o text,
  verbatimeventdate_bkp text,
  verbatim_event_date_pda text,
  identifiedby_wk text,
  identifiedby_wk_o text,
  identifiedby_bkp text,
  identifiedby_pda text,
  dateidentified_wk text,
  dateidentified_wk_o text,
  dateidentified_bkp text,
  dateidentified_pda text,
  family_wk text,
  family_wk_o text,
  family_bkp text,
  family_pda text,
  scientificname_wk text,
  scientificname_wk_o text,
  scientificname_bkp text,
  scientificname_pda text,
  recordnumber_wk text,
  recordnumber_wk_o text,
  recordnumber_bkp text,
  record_number_pda text,
  country_wk text,
  country_wk_o text,
  country_bkp text,
  country_pda text,
  stateprovince_wk text,
  stateprovince_wk_o text,
  stateprovince_bkp text,
  state_province_pda text,
  county_wk text,
  county_wk_o text,
  county_bkp text,
  county_pda text,
  locality_wk text,
  locality_wk_o text,
  locality_bkp text,
  locality_pda text,
  verbatimlatitude_wk text,
  verbatimlatitude_wk_o text,
  verbatimlatitude_bkp text,
  verbatim_latitude_pda text,
  verbatimlongitude_wk text,
  verbatimlongitude_wk_o text,
  verbatimlongitude_bkp text,
  verbatim_longitude_pda text,
  lifestage_wk text,
  lifestage_wk_o text,
  lifestage_bkp text,
  life_stage_pda text,
  habitat_wk text,
  habitat_wk_o text,
  habitat_bkp text,
  habitat_pda text,
  individualcount_wk text,
  individualcount_wk_o text,
  individualcount_bkp text,
  individualcount_pda text,
  occid varchar(32)
  );


CREATE TABLE "public"."specprocessorrawlabels" 
(
  imgid serial primary key,
  rawstr text
);




INSERT INTO public.omoccurrences(occid, catalognumber, recordedby_wk, recordedby_wk_o, recordedby_bkp, recorded_by_pda, verbatimeventdate_wk, verbatimeventdate_wk_o, verbatimeventdate_bkp,
verbatim_event_date_pda, identifiedby_wk, identifiedby_wk_o, identifiedby_bkp, identifiedby_pda, dateidentified_wk, dateidentified_wk_o, dateidentified_bkp, dateidentified_pda,
family_wk, family_wk_o, family_bkp, family_pda, scientificname_wk, scientificname_wk_o, scientificname_bkp, scientificname_pda, country_wk, country_wk_o, country_bkp, country_pda,
locality_wk, locality_wk_o, locality_bkp, locality_pda, verbatimlatitude_wk, verbatimlatitude_wk_o, verbatimlatitude_bkp, verbatim_latitude_pda, verbatimlongitude_wk, verbatimlongitude_wk_o,
verbatimlongitude_bkp, verbatim_longitude_pda, lifestage_wk, lifestage_wk_o, lifestage_bkp, life_stage_pda, habitat_wk, habitat_wk_o, habitat_bkp, habitat_pda, individualcount_wk,
individualcount_wk_o, individualcount_bkp, individualcount_pda)
SELECT id_biodiversity_work, specimen_id_wk, recordedby_wk, recordedby_wk_o, recordedby_bkp, recorded_by_pda, verbatimeventdate_wk, verbatimeventdate_wk_o, verbatimeventdate_bkp,
verbatim_event_date_pda, identifiedby_wk, identifiedby_wk_o, identifiedby_bkp, identifiedby_pda, dateidentified_wk, dateidentified_wk_o, dateidentified_bkp, dateidentified_pda,
family_wk, family_wk_o, family_bkp, family_pda, scientificname_wk, scientificname_wk_o, scientificname_bkp, scientificname_pda, country_wk, country_wk_o, country_bkp, country_pda,
locality_wk, locality_wk_o, locality_bkp, locality_pda, verbatimlatitude_wk, verbatimlatitude_wk_o, verbatimlatitude_bkp, verbatim_latitude_pda, verbatimlongitude_wk, verbatimlongitude_wk_o,
verbatimlongitude_bkp, verbatim_longitude_pda, lifestage_wk, lifestage_wk_o, lifestage_bkp, life_stage_pda, habitat_wk, habitat_wk_o, habitat_bkp, habitat_pda, individualcount_wk,
individualcount_wk_o, individualcount_bkp, individualcount_pda
FROM rcby_ocr; 




insert into images (occid)
select id_biodiversity_work
from w_colector_ocr; 


update images set originalurl = source_bkp
from w_colector_ocr
where images.occid = w_colector_ocr.id_biodiversity_work::text; 

insert into specprocessorrawlabels (imgid)
select imgid
from images; 




CREATE TABLE "public"."hocr_results" (
  "id" SERIAL PRIMARY KEY,
  "occid" varchar(22),
  "catalognumber" varchar(9),
  "filename" varchar(40),
  "processed" int4,
  "x" varchar(6),
  "y" varchar(6),
  "area_id" varchar(12),
  "line_id" varchar(12),
  "word_id" varchar(12),
  "text" varchar(107),
  "area_x0" float8,
  "area_y0" float8,
  "area_x1" float8,
  "area_y1" float8,
  "line_x0" float8,
  "line_y0" float8,
  "line_x1" float8,
  "line_y1" float8,
  "word_x0" float8,
  "word_y0" float8,
  "word_x1" float8,
  "word_y1" float8
)
;