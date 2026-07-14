import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from dotenv import load_dotenv
import mplfinance as mpf

def get_basic_info(df,target):
    print(df[target].describe())
    print("Median: ",df[target].median())
    print("Std Dev: ",df[target].std())
    print("IQR:", df[target].quantile(0.75) - df[target].quantile(0.25))

def aggregate_by_time(df,bucket,target):
    groupby = df.groupby(bucket)[target]
    df_agg = groupby.agg(['mean','median','std'])
    df['q1'] = groupby.transform(lambda x: x.quantile(.25))
    df['q3'] = groupby.transform(lambda x: x.quantile(.75))
    df_agg_filtered = df[(df[target]>df['q1']) & (df[target]<df['q3'])]
    df_agg_IQR = df_agg_filtered.groupby(bucket)[target].agg(['mean','median','std'])
    return df_agg, df_agg_IQR

def frequency_hist(df,target,bins,xlabel):
    plt.figure(figsize=(10,3))
    plt.hist(df[target],bins=30,edgecolor='black')
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

def bar_by_time(df, target, xlabel, ylabel):
    plt.figure(figsize=(10,3))
    plt.bar(df.index.astype(str), df[target])
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(ylabel+' By '+xlabel)
    ax = plt.gca()
    plt.xticks(rotation=45)
    plt.show()

def visualize_barchart(df, date):
    df_chart = df[df['bar_date'] == date].copy()
    print(df_chart.iloc[1]['contract'])
    df_chart['datetime'] = pd.to_datetime(df_chart['bar_date'].astype(str) + ' ' + df_chart['bar_time'].astype(str))
    df_chart = df_chart.set_index('datetime')
    df_chart = df_chart[['open','high','low','close','volume']]
    df_chart.columns = ['Open','High','Low','Close','Volume']
    mpf.plot(df_chart, type='candle', volume=False)

