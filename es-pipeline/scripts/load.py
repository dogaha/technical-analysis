# bronze.es_bars
#   id            BIGSERIAL PRIMARY KEY,
#   bar_timestamp TEXT NOT NULL,   -- raw string, e.g. '20241213 060100'
#   open_price    NUMERIC,
#   high_price    NUMERIC,
#   low_price     NUMERIC,
#   close_price   NUMERIC,
#   volume        NUMERIC,
#   source_file   TEXT NOT NULL,
#   loaded_at     TIMESTAMP NOT NULL DEFAULT now()


# Libraries
import os
import logging
import psycopg2
import io
import re
import calendar
from datetime import date, datetime, timedelta
from dotenv import load_dotenv

VALID_MONTHS = {
    'ES': set('HMUZ'),
    'NQ': set('HMUZ')
}
EXPIRY_MONTH = {
    'F': 1,   # Jan
    'G': 2,   # Feb
    'H': 3,   # Mar
    'J': 4,   # Apr
    'K': 5,   # May
    'M': 6,   # Jun
    'N': 7,   # Jul
    'Q': 8,   # Aug
    'U': 9,   # Sep
    'V': 10,  # Oct
    'X': 11,  # Nov
    'Z': 12,  # Dec
}

class ContractDateRangeError(Exception):
    pass

class ContractNameError(Exception):
    pass

def validate_filename(contract):
    match = re.match(r'^([A-Z]{1,3})([FGHJKMNQUVXZ])(\d{2})$', contract)
    if not match:
        raise ContractNameError(f"Invalid contract format: {contract}, use CME format")
    root, month, year = match.groups()
    if root not in VALID_MONTHS:
        raise ContractNameError(f"Invalid contract: {root}, not in VALID_MONTHS")
    if month not in VALID_MONTHS[root]:
        raise ContractNameError(f"Invalid month for {root}: {month}, use CME format")

def third_monday(year, month):
    d = date(year, month, 1) # get the first of the month
    d += timedelta(days=(7 - d.weekday()) % 7) # get the first monday
    return d + timedelta(weeks=2) # add two weeks to get third monday

def validate_daterange(contract, min_date, max_date):
    match = re.match(r'^([A-Z]{1,3})([FGHJKMNQUVXZ])(\d{2})$', contract)
    root, month_code, year = match.groups()
    exp_month = EXPIRY_MONTH[month_code]
    year = 2000 + int(year)

    # contract_month: 3=Mar, 6=Jun, 9=Sep, 12=Dec
    roll_month = exp_month - 3
    roll_year = year
    if roll_month <= 0:
        roll_month += 12
        roll_year -= 1
    start = third_monday(roll_year, roll_month)

    next_month = exp_month
    next_year = year
    next_roll_month = next_month
    next_roll_year = next_year
    end = third_monday(next_roll_year, next_roll_month) - timedelta(days=1)
    
    if not (min_date >= start and max_date <= end):
        raise ContractDateRangeError(f"Invalid date range for {contract}: must be between {start} - {end}")
        
load_dotenv()
logger = logging.getLogger("es_pipeline")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("/opt/airflow/logs/pipeline.log")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)

# logging.basicConfig(
#     filename="/opt/airflow/logs/pipeline.log",
#     level=logging.INFO,
#     format="%(asctime)s %(levelname)s %(message)s"
# )

# Ingestion
conn = psycopg2.connect(
    host="host.docker.internal",
    port="5432",
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD")
)
cur = conn.cursor()

landingPath = "/opt/airflow/data/landing"
archivePath = "/opt/airflow/data/archive"


for instance in os.listdir(landingPath):
    if instance.endswith(".txt"):
        instancePath = os.path.join(landingPath,instance)
        if os.path.isfile(instancePath):
            try:
                filename = os.path.splitext(os.path.basename(instancePath))[0]
                validate_filename(filename)

                buffer = io.StringIO()
                first_line = None
                last_line = None
                with open(instancePath,"r",encoding="utf-8") as file:
                    first_line = file.readline()
                    buffer.write(first_line.strip() + f";{filename}\n")
                    for line in file:
                        last_line = line
                        buffer.write(line.strip()+f";{filename}\n")
                buffer.seek(0)

                bar_date_min = datetime.strptime(first_line.split(';')[0], '%Y%m%d %H%M%S').date()
                bar_date_max = datetime.strptime(last_line.split(';')[0], '%Y%m%d %H%M%S').date()
                match = re.match(r'^([A-Z]{1,3})([FGHJKMNQUVXZ])(\d{2})$', contract)
                root, month_code, year = match.groups()
                year = 2000 + int(year)
                
                validate_daterange(filename,bar_date_min,bar_date_max)
                
                cur.copy_expert(
                    "COPY bronze.es_bars (bar_timestamp, open_price, high_price, low_price, close_price, volume, source_file) FROM STDIN WITH(FORMAT csv, DELIMITER ';')",
                    buffer
                )

                os.replace(instancePath, os.path.join(archivePath, instance))

                conn.commit()
                logger.info(f"Successfully Ingested {filename}")

            except ContractNameError as e:
                logger.error(f"Contract validation failed for {filename}: {e}")
                continue
            except ContractDateRangeError as e:
                logger.error(f"Date range validation failed for {filename}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error during ingestion for {filename}: {e}")
                continue

cur.close()
conn.close()

