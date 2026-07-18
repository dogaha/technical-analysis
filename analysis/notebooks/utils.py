import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from dotenv import load_dotenv
import mplfinance as mpf
import datetime

def descriptive_analysis(df,target):
    print(df[target].describe())
    print("\nMedian: ",df[target].median())
    print("Std Dev: ",df[target].std())
    print("IQR: ", df[target].quantile(0.75) - df[target].quantile(0.25))

def create_time_bucket(df,time_col,time_bucket):
    df['bucket_'+time_bucket+'min'] = df[time_col].apply(
        lambda t: (datetime.datetime.min + datetime.timedelta(minutes=(t.hour*60+t.minute)//int(time_bucket)*int(time_bucket))).time()
    )

def descriptive_groupby(df,group,target):
    groupby = df.groupby(group)[target]
    df_agg = groupby.agg(['mean','median','std','count'])
    return df_agg

def frequency_hist(df,target,bins,xlabel):
    plt.figure(figsize=(10,3))
    plt.hist(df[target],bins=bins,edgecolor='black')
    plt.xlabel(xlabel)
    plt.ylabel('Frequency')
    plt.title('Frequency Distribution of '+xlabel)
    plt.show()

def box_plot(df,target,ylabel,title):
    plt.figure(figsize=(10,3))
    plt.boxplot(df[target])
    plt.ylabel(ylabel)
    plt.title(title)
    plt.show()

def bar_chart(df, target, xlabel, ylabel,angle=45,tickbin=None,yerror=None):
    plt.figure(figsize=(10,3))
    plt.bar(df.index.astype(str), df[target],yerr=yerror,capsize=4)
    if tickbin:
        plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(nbins=tickbin))
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(ylabel+' By '+xlabel)
    ax = plt.gca()
    plt.xticks(rotation=angle)
    plt.show()

def display_market_chart(df, date):
    if 'total_volume' in df.columns:
        df = df.rename(columns={'total_volume':'volume'}) 
    df_chart = df[df['bar_date'] == date].copy()
    df_chart['datetime'] = pd.to_datetime(df_chart['bar_date'].astype(str) + ' ' + df_chart['bar_time'].astype(str))
    df_chart = df_chart.set_index('datetime')
    df_chart = df_chart[['open','high','low','close','volume']]
    df_chart.columns = ['Open','High','Low','Close','Volume']
    mpf.plot(df_chart, type='candle', volume=False)

def add_winsorized_col(df,target):
    lower = df[target].quantile(0.01)
    upper = df[target].quantile(0.99)

    df[target+'_winsorized'] = df[target].clip(lower=lower, upper=upper)
    return df

def get_swings(df):
    highs = df['high'].to_numpy()
    lows = df['low'].to_numpy()
    closes = df['close'].to_numpy()
    opens = df['open'].to_numpy()
    volumes = df['volume'].to_numpy()
    times = df['bar_time'].to_numpy()
    dates = df['bar_date'].to_numpy()
    
    swings = []
    start_index = None
    end_index = None
    start_price = None
    trend = None
    swing_low = None
    swing_high = None
    volume = None
    total_price_movement = None
    upper_price_movememnt= None
    lower_price_movememnt= None
    
    for i in range(len(highs)):
        cur_trend = 'NONE'
        # Case Of New Day (First run of new Day)
        if i==0 or dates[i] != dates[i-1]:
            start_index = i
            end_index = i
            start_price = opens[i]
            trend = 'NONE'
            swing_low = lows[i]
            swing_high = highs[i]
            volume = volumes[i]
            total_price_movement = abs(highs[i] - lows[i])
            upper_price_movememnt = abs(opens[i] - highs[i])
            lower_price_movememnt = abs(opens[i] - lows[i])
            continue
        
        if (closes[i] > closes[i-1]):
            cur_trend = 'UP'
        elif (closes[i] < closes[i-1]):
            cur_trend = 'DOWN'
    
        if trend is None or trend == 'NONE':
            if (closes[i] > start_price):
                trend = 'UP'
            elif (closes[i] < start_price):
                trend = 'DOWN'
            end_index = i
            swing_high = max(swing_high, highs[i])
            swing_low = min(swing_low, lows[i])
            total_price_movement += abs(highs[i] - lows[i])
            upper_price_movememnt += abs(opens[i] - highs[i])
            lower_price_movememnt += abs(opens[i] - lows[i])
            
        elif trend==cur_trend or cur_trend=='NONE':
            end_index = i
            swing_high = max(swing_high, highs[i])
            swing_low = min(swing_low, lows[i])
            total_price_movement += abs(highs[i] - lows[i])
            upper_price_movememnt += abs(opens[i] - highs[i])
            lower_price_movememnt += abs(opens[i] - lows[i])
        else:
            if trend == 'UP':
                swings.append([dates[start_index],times[start_index],times[end_index],swing_high,start_price,closes[end_index],swing_low,volume,total_price_movement,upper_price_movememnt,lower_price_movememnt,trend])
            else:
                swings.append([dates[start_index],times[start_index],times[end_index],swing_high,start_price,closes[end_index],swing_low,volume,total_price_movement,lower_price_movememnt,upper_price_movememnt,trend])
            
            start_index = i-1
            end_index = i
            trend = cur_trend
            start_price = closes[i-1]
            swing_high = max(highs[i], highs[i-1])
            swing_low = min(lows[i], lows[i-1])
            volume = volumes[i]+volumes[i-1]
            total_price_movement = abs(highs[i] - lows[i]) + abs(highs[i-1] - lows[i-1])
            upper_price_movememnt = abs(opens[i] - highs[i]) + abs(opens[i-1] - highs[i-1])
            lower_price_movememnt = abs(opens[i] - lows[i]) + abs(opens[i-1] - lows[i-1])
    
    swing_columns=['date','time_start','time_end','high','open', 'close','low','volume','price_movememnt','following_price_movement','fighting_price_movememnt','trend']
    df_swings = pd.DataFrame(swings,columns=swing_columns)
    create_time_bucket(df_swings,'time_start','30')
    create_time_bucket(df_swings,'time_start','15')
    create_time_bucket(df_swings,'time_start','5')
    return df_swings