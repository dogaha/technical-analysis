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

def display_market_chart(df, date,date_col='bar_date',time_col='bar_time'):
    df_chart = df[df[date_col] == date].copy()
    df_chart['datetime'] = pd.to_datetime(df_chart[date_col].astype(str) + ' ' + df_chart[time_col].astype(str))
    df_chart = df_chart.set_index('datetime')
    df_chart = df_chart[['open','high','low','close','volume']]
    df_chart.columns = ['Open','High','Low','Close','Volume']

    open_time = f"{date} 08:30:00"
    mpf.plot(df_chart, type='candle', volume=True,vlines=dict(vlines=[open_time],linewidths=0.8, alpha=0.5))

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
    times = df['bar_time'].to_numpy()
    dates = df['bar_date'].to_numpy()
    volumes = df['volume'].to_numpy()
    
    swings = []
    start_index = None
    end_index = None
    trend = None
    volume = None
    swing_low = None
    swing_high = None
    upper_price_movememnt= None
    lower_price_movememnt= None
    
    for i in range(len(highs)):
        cur_trend = 'NONE'
        # Case Of New Day (First run of new Day)
        if i==0 or dates[i] != dates[i-1]:
            start_index = i
            end_index = i
            if (closes[i] > opens[i]):
                trend = 'UP'
            elif (closes[i] < opens[i]):
                trend = 'DOWN'
            else:
                trend = 'NONE'
            volume = volumes[i]
            swing_low = lows[i]
            swing_high = highs[i]
            upper_price_movememnt = abs(opens[i] - highs[i])
            lower_price_movememnt = abs(opens[i] - lows[i])
            continue
        
        if (closes[i] > closes[i-1]):
            cur_trend = 'UP'
        elif (closes[i] < closes[i-1]):
            cur_trend = 'DOWN'

        if trend is None or trend == 'NONE':
            if (closes[i] > closes[start_index]):
                trend = 'UP'
            elif (closes[i] < closes[start_index]):
                trend = 'DOWN'
            else:
                trend = 'NONE'
            volume += volumes[i]
            end_index = i
            swing_high = max(swing_high, highs[i])
            swing_low = min(swing_low, lows[i])
            upper_price_movememnt += abs(opens[i] - highs[i])
            lower_price_movememnt += abs(opens[i] - lows[i])
            
        elif trend==cur_trend or cur_trend=='NONE':
            volume += volumes[i]
            end_index = i
            swing_high = max(swing_high, highs[i])
            swing_low = min(swing_low, lows[i])
            upper_price_movememnt += abs(opens[i] - highs[i])
            lower_price_movememnt += abs(opens[i] - lows[i])
        else:
            if trend == 'UP':
                swings.append([dates[start_index],times[start_index],times[end_index],highs[start_index],opens[start_index],closes[end_index],swing_low,volume,upper_price_movememnt,lower_price_movememnt,trend])
            else:
                swings.append([dates[start_index],times[start_index],times[end_index],highs[start_index],opens[start_index],closes[end_index],swing_low,volume,lower_price_movememnt,upper_price_movememnt,trend])
            
            start_index = i
            end_index = i
            volume = volumes[i]
            if (closes[i] > opens[i]):
                trend = 'UP'
            elif (closes[i] < opens[i]):
                trend = 'DOWN'
            else:
                trend = 'NONE'
            swing_high = max(highs[i], highs[i-1])
            swing_low = lows[i]
            upper_price_movememnt = abs(opens[i] - highs[i])
            lower_price_movememnt = abs(opens[i] - lows[i])
    
    swing_columns=['date','time_start','time_end','high', 'open','close','low','volume','following_price_movement','fighting_price_movememnt','trend']
    df_swings = pd.DataFrame(swings,columns=swing_columns)
    create_time_bucket(df_swings,'time_start','30')
    create_time_bucket(df_swings,'time_start','15')
    create_time_bucket(df_swings,'time_start','5')
    return df_swings