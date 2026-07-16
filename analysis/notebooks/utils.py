import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from dotenv import load_dotenv
import mplfinance as mpf
import datetime

def get_basic_info(df,target):
    print(df[target].describe())
    print("Median: ",df[target].median())
    print("Std Dev: ",df[target].std())
    print("IQR:", df[target].quantile(0.75) - df[target].quantile(0.25))

def aggregate_by_time(df,bucket,target):
    groupby = df.groupby(bucket)[target]
    df_agg = groupby.agg(['mean','median','std','count'])
    df['q1'] = groupby.transform(lambda x: x.quantile(.25))
    df['q3'] = groupby.transform(lambda x: x.quantile(.75))
    df_agg_filtered = df[(df[target]>df['q1']) & (df[target]<df['q3'])]
    df_agg_IQR = df_agg_filtered.groupby(bucket)[target].agg(['mean','median','std','count'])
    return df_agg, df_agg_IQR

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

def bar_by_time(df, target, xlabel, ylabel,angle=45,tickbin=None):
    plt.figure(figsize=(10,3))
    plt.bar(df.index.astype(str), df[target])
    if tickbin:
        plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(nbins=tickbin))
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(ylabel+' By '+xlabel)
    ax = plt.gca()
    plt.xticks(rotation=angle)
    plt.show()

def visualize_barchart(df, date):
    df_chart = df[df['bar_date'] == date].copy()
    df_chart['datetime'] = pd.to_datetime(df_chart['bar_date'].astype(str) + ' ' + df_chart['bar_time'].astype(str))
    df_chart = df_chart.set_index('datetime')
    df_chart = df_chart[['open','high','low','close','volume']]
    df_chart.columns = ['Open','High','Low','Close','Volume']
    mpf.plot(df_chart, type='candle', volume=False)

def get_swings(df):
    highs = df['high'].to_numpy()
    lows = df['low'].to_numpy()
    closes = df['close'].to_numpy()
    opens = df['open'].to_numpy()
    times = df['bar_time'].to_numpy()
    dates = df['bar_date'].to_numpy()
    
    swings = []
    start = None
    end = None
    direction = None
    threshold = 0
    
    for i in range(1,len(closes)):
        cur_direction = None
        if (closes[i] > closes[i-1]):
            cur_direction = 'UP'
        elif closes[i] < closes[i-1]:
            cur_direction = 'DOWN'
        else:
            cur_direction = "NONE"
        if dates[i] != dates[i-1]:
            swing = [
                dates[start],
                times[start],
                times[end],
                (times[end].hour * 60 + times[end].minute) - (times[start].hour * 60 + times[start].minute),
                max(highs[start],highs[end]),
                opens[start],
                closes[end],
                min(lows[start],lows[end]),
                direction,
                profit,
                drawdown
            ]
            swings.append(swing)
            direction = None
            continue
        
        if direction == None:
            direction = cur_direction
            start = i-1
            end = i
        elif ((direction == cur_direction) or abs(closes[i]-closes[i-1])<threshold):
            end = i
        else:
            profit=0;
            drawdown=0;
            if direction == 'UP':
                profit = abs(highs[end] - opens[start])
                drawdown = abs(opens[start] - lows[start])
            elif direction == 'DOWN':
                profit = abs(lows[end] - opens[start])
                drawdown = abs(opens[start] - lows[start])
            swing = [
                dates[start],
                times[start],
                times[end],
                (times[end].hour * 60 + times[end].minute) - (times[start].hour * 60 + times[start].minute),
                max(highs[start],highs[end]),
                opens[start],
                closes[end],
                min(lows[start],lows[end]),
                direction,
                profit,
                drawdown
            ]
            swings.append(swing)
            direction = cur_direction
            start = i-1
            end = i
    swing_columns=['date','time_start','time_end','duration','high','open', 'close','low','direction','profit','drawdown']
    df_swings = pd.DataFrame(swings,columns=swing_columns)
    df_swings['bucket_30min'] = df_swings['time_start'].apply(
        lambda t: (datetime.datetime.min + datetime.timedelta(minutes=(t.hour*60+t.minute)//30*30)).time()
    )
    df_swings['bucket_15min'] = df_swings['time_start'].apply(
        lambda t: (datetime.datetime.min + datetime.timedelta(minutes=(t.hour*60+t.minute)//15*15)).time()
    )
    df_swings['bucket_5min'] = df_swings['time_start'].apply(
        lambda t: (datetime.datetime.min + datetime.timedelta(minutes=(t.hour*60+t.minute)//5*5)).time()
    )
    return df_swings