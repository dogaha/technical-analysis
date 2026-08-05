import time
import re
import os
from datetime import date, datetime, timedelta
import logging
import pandas as pd
import numpy as np

VALID_MONTHS = {
    'ES': ['H', 'M', 'U', 'Z'],
    'NQ': ['H', 'M', 'U', 'Z']
}

EXPIRY_MONTH_NUM = {
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

EXPIRY_MONTH_STR = {
    'F': 'JAN',
    'G': 'FEB',
    'H': 'MAR',
    'J': 'APR',
    'K': 'MAY',
    'M': 'JUN',
    'N': 'JUL',
    'Q': 'AUG',
    'U': 'SEP',
    'V': 'OCT',
    'X': 'NOV',
    'Z': 'DEC',
}

EXPIRY_MONTH_STR_EZ = {value: key for key, value in EXPIRY_MONTH_STR.items()}

class ContractDateRangeError(Exception):
    pass

class ContractNameError(Exception):
    pass

class DuplicateContractError(Exception):
    pass

class PostgresTableError(Exception):
    pass

def get_logger():
    logger = logging.getLogger("es_pipeline")
    if not logger.handlers:
        handler = logging.FileHandler("/opt/airflow/logs/pipeline.log")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

def create_contract_list(contract_root,start_year,end_year):
    contract_list = []
    
    for y in range(end_year - start_year + 1):
        year = start_year+y 
        for month_code in VALID_MONTHS[contract_root.upper()]:
            year_two_digits = f"{abs(year) % 100:02d}"
            filename = (contract_root + month_code + year_two_digits).upper()
            contract_list.append(filename)
    return contract_list

def validate_filename(contract):
    # Check for Format
    match = re.match(r'^([A-Z]{1,3})([FGHJKMNQUVXZ])(\d{2})$', contract)   
    if not match:
        raise ContractNameError(f"Invalid filename '{contract}', use CME format")
    root, month, year = match.groups()
    if root not in VALID_MONTHS:
        raise ContractNameError(f"Invalid contract '{root}', use contracts compatible with this pipeline")
    if month not in VALID_MONTHS[root]:
        raise ContractNameError(f"Invalid contract month code '{month}', use compatible month codes for contract '{root}'")

def third_monday(year, month):
    d = date(year, month, 1) # get the first of the month
    d += timedelta(days=(7 - d.weekday()) % 7) # get the first monday
    return d + timedelta(weeks=2) # add two weeks to get third monday

def get_daterange(contract):
    match = re.match(r'^([A-Z]{1,3})([FGHJKMNQUVXZ])(\d{2})$', contract)
    root, month_code, year = match.groups()
    exp_month = EXPIRY_MONTH_NUM[month_code]
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
    
    return start, end

def get_legs(df):
    contracts = df['contract'].to_numpy()
    highs = df['high'].to_numpy()
    lows = df['low'].to_numpy()
    closes = df['close'].to_numpy()
    opens = df['open'].to_numpy()
    times = df['bar_time'].to_numpy()
    dates = df['bar_date'].to_numpy()
    volumes = df['volume'].to_numpy()
    
    legs = []
    for i in range(len(highs)):
        # Case Of New Day (First run of new Day)
        if i==0 or dates[i] != dates[i-1] or start_index is None :
            start_index = i
            end_index = i
            if (closes[i] > opens[i]):
                trend = 'UP'
            elif (closes[i] < opens[i]):
                trend = 'DOWN'
            else:
                trend = 'NONE'
            volume = volumes[i]
            leg_low = lows[i]
            leg_high = highs[i]
            bullish_movement = highs[i] - opens[i]
            bearish_movememnt = opens[i] - lows[i]
            continue
        
        if (closes[i] > closes[i-1]):
            cur_trend = 'UP'
        elif (closes[i] < closes[i-1]):
            cur_trend = 'DOWN'
        else:
            cur_trend = 'NONE'

        if trend == 'NONE':
            if (closes[i] > closes[start_index]):
                trend = 'UP'
            elif (closes[i] < closes[start_index]):
                trend = 'DOWN'
            else:
                trend = 'NONE'
            volume += volumes[i]
            end_index = i
            leg_high = max(leg_high, highs[i])
            leg_low = min(leg_low, lows[i])
            bullish_movement += highs[i] - opens[i]
            bearish_movememnt += opens[i] - lows[i]
            
        elif trend==cur_trend or cur_trend=='NONE':
            volume += volumes[i]
            end_index = i
            leg_high = max(leg_high, highs[i])
            leg_low = min(leg_low, lows[i])
            bullish_movement += abs(opens[i] - highs[i])
            bearish_movememnt += abs(opens[i] - lows[i])
        else:
            legs.append([contracts[start_index],dates[start_index],times[start_index],times[end_index],leg_high,opens[start_index],closes[end_index],leg_low,volume,bullish_movement,bearish_movememnt,trend])
            start_index = None
    
    leg_columns=['contract','date','time_start','time_end','high', 'open','close','low','volume','bullish_price_movement','bearish_price_movememnt','trend']
    return pd.DataFrame(legs,columns=leg_columns)

# def get_consolidations(df):
#     contracts = df['contract'].to_numpy()
#     highs = df['high'].to_numpy()
#     lows = df['low'].to_numpy()
#     closes = df['close'].to_numpy()
#     opens = df['open'].to_numpy()
#     start_times = df['time_start'].to_numpy()
#     end_times = df['time_end']
#     dates = df['date'].to_numpy()
#     trends = df['trends'].to_numpy()
#     volumes = df['volume'].to_numpy()

#     for i in range(len(1,contracts)):
#         # case new day
#         if dates[i] != dates[i-1]:
#             # new day
#             continue
#         cur_trend = trends[i]
#         if start_time is None:
#             i_net = highs[i-1]-open[i-1] if trends[i-1] == "UP" else open[i-1]-low[i-1]
#             j_net = highs[i]-open[i] if trends[i] == "UP" else open[i]-low[i]

#             bullish_movement = highs[i-1]-open[i-1] + highs[i]-open[i]
#             bearish_movement = open[i-1]-low[i-1] + open[i]-low[i]
            
#             net_movememnt = i_net + j_net
#             total_movememnt = highs[i] - low[i] + highs[i-1] - lows[i-1]
            
#             directional_efficiency = net_movememnt/total_movememnt
#             range_efficiency = range_size / total_movememnt
#             balance = min(bullish_movement,bearish_movement) / max(bullish_movement,bearish_movement)

#         # consolidation score
#         if directional_efficiency < 0.3 and  range_efficiency  > 5 and balance > .7:
#             start_time = start_times[i]
#             end_time = end_time[i]
#             net_movememnt = highs[i]-open[i] if cur_trend == "UP" else open[i]-low[i]
#             total_movememnt = highs[i] - low[i]

#             if cur_trend == "UP":
#                 bull_sum = net_movememnt
#                 bear_sum = 0
#             else:
#                 bull_sum = 0
#                 bear_sum = net_movememnt
#             high = highs[i]
#             low = lows[i]
#             range_size = high-low
#         # end of consolidation

