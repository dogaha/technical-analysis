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

def third_friday(year, month):
    # Find first Friday
    c = calendar.monthcalendar(year, month)
    fridays = [week[calendar.FRIDAY] for week in c if week[calendar.FRIDAY] != 0]
    return date(year, month, fridays[2])
def next_trading_day(d):
    d = d + timedelta(days=1)
    while d.weekday() in (5, 6):  # 5=Saturday, 6=Sunday
        d += timedelta(days=1)
    return d

def validate_daterange_quarterly(contract, min_date, max_date):
    match = re.match(r'^([A-Z]{1,3})([FGHJKMNQUVXZ])(\d{2})$', contract)
    root, month_code, year = match.groups()
    year = 2000 + int(year)
    exp_month = EXPIRY_MONTH[month_code]
    expiry = third_friday(year, exp_month)

    prior_month = exp_month - 3 if exp_month > 3 else exp_month + 9
    prior_year = year if exp_month > 3 else year - 1
    start = third_friday(prior_year, prior_month) + timedelta(days=1)

    if not (min_date >= start and max_date <= expiry):
        raise ContractDateRangeError(f"Invalid date range for {contract}: must be between {start} - {expiry}")

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
                validate_daterange_quarterly(filename,bar_date_min,bar_date_max)
                
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

