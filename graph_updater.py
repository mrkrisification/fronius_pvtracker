import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
## additional import for using TkAgg
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
### end of additional imports

from datetime import datetime, timedelta
import RequestReader
import seaborn as sns


class graph_updater:
    def __init__(self, url, device_id):
        self.url = url
        self.device_id= device_id
        #self.rr = rr.RequestReader(url, "")
        pass

    def get_details_yesterday(self):
        rr = RequestReader.RequestHictoricProductionDeviceDetail_last48(self.url, 1)
        data = rr.get_data()
        #print(data)
        return data['Data']['EnergyReal_WAC_Sum_Produced']['Values'] 

    def read_json(self, filename):
        with open(filename) as json_file:
            r = json.load(json_file)
        
        return r

    def get_yesterday_date_string(self):
        yesterday = datetime.today()-timedelta(days=1)
        yest_str = datetime.strftime(yesterday, '%Y-%m-%d')
        return yest_str

    def convert_to_datetime(self, startdate, timestamp):
        startdate = datetime.strptime(startdate, '%Y-%m-%d')
        try:
        #check if still corresponds to startdate
            if (timestamp / (24*3600) >= 1):
                daysdelta = int(timestamp/(24*3600))
                startdate = startdate + timedelta(days=daysdelta)
                timestamp = timestamp - (24*3600) * daysdelta
            else:
                pass
            hour = int(timestamp/3600)
            minute = int((timestamp % 3600) / 60)

            year = startdate.year
            month = startdate.month
            day = startdate.day

            #print(year, month, day, hour, minute)

            return datetime(year, month, day, hour, minute)
        except Exception as e:
            print(f'Could not convert {timestamp} - Error {e}')
    

    def show_48_hr_graph(self, data_parsed):
        # for offline testing
        data_parsed = data_parsed
        #data_parsed = self.get_details_yesterday() # collecting data directly from API
        start_date = self.get_yesterday_date_string()

        df = pd.DataFrame.from_dict(data_parsed, orient='index')
        df.reset_index(inplace=True)
        df.columns=['TS', 'Wh']
        df.TS = df.TS.astype(int)

        df['Datetime'] = df.apply(lambda x: self.convert_to_datetime(start_date, x['TS']), axis=1)
        df.drop(columns='TS', inplace=True)
        df['Date'] = df['Datetime'].dt.date
        df['Time'] = df['Datetime'].dt.strftime('%H:%M')
        df['Time'] = pd.to_datetime(df.Time).dt.time
        df['DAY'] = np.nan
        yesterday = str(df.Date.min())
        today = str(df.Date.max())
        df.Date = df.Date.astype(str)

        df['DAY'].loc[df.Date==yesterday] = 'yesterday'
        df['DAY'].loc[df.Date==today] = 'today'

        df.Time = df.Time.astype(str)
        df['Time'] = pd.to_datetime(today + ' ' + df.Time)

        print(df.loc[df.DAY=='yesterday'].head())

        relcols = ['Wh', 'Time', 'DAY']


        df_plt = pd.DataFrame(df.pivot_table(index='Time', columns='DAY', values='Wh', aggfunc='sum'))
        df_plt.dropna(inplace=True)
        df_plt.reset_index(inplace=True)

        #print(df_plt.columns)

        #print(df_plt.head())
        #print(plt.style.available)
        plt.style.use('dark_background')
        plot_bg_color = '#2d3436'

        fig, ax = plt.subplots(figsize=(3,2))
        fig.patch.set_facecolor(plot_bg_color)
        ax.set_facecolor(plot_bg_color)
        ax.axes.xaxis.set_ticklabels([])
        ax.axes.xaxis.set_ticks([])
        ax.tick_params(axis='y', labelsize= 8)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)

        #plt.xticks(rotation=90)
        ax = plt.plot(df_plt.Time, df_plt.today, linewidth=3, color='#fbc531', label='today')
        ax = plt.plot(df_plt.Time, df_plt.yesterday, linewidth=1, color='#636e72', label='yesterday')
        plt.legend(facecolor=plot_bg_color, frameon = False, bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left',
                ncol=2,  borderaxespad=0., prop={'size': 8})

        #df_plt.yesterday.plot(kind='bar')
        #plt.show()
        #plt.savefig('graph.png', dpi=80, facecolor=plot_bg_color, edgecolor=plot_bg_color, orientation='portrait', )
        plt.show()


    ##### retrieve and transform data####
    def collect_graph_data(self):
        print('Collecting Graph Data')
        data_parsed = self.get_details_yesterday() # collecting data directly from API
        start_date = self.get_yesterday_date_string()

        df = pd.DataFrame.from_dict(data_parsed, orient='index')
        df.reset_index(inplace=True)
        df.columns=['TS', 'Wh']
        df.TS = df.TS.astype(int)

        df['Datetime'] = df.apply(lambda x: self.convert_to_datetime(start_date, x['TS']), axis=1)
        df.drop(columns='TS', inplace=True)
        df['Date'] = df['Datetime'].dt.date
        df['Time'] = df['Datetime'].dt.strftime('%H:%M')
        df['Time'] = pd.to_datetime(df.Time).dt.time
        df['DAY'] = np.nan
        yesterday = str(df.Date.min())
        today = str(df.Date.max())
        df.Date = df.Date.astype(str)

        df['DAY'].loc[df.Date==yesterday] = 'yesterday'
        df['DAY'].loc[df.Date==today] = 'today'

        df.Time = df.Time.astype(str)
        df['Time'] = pd.to_datetime(today + ' ' + df.Time)

        #print(df.loc[df.DAY=='yesterday'].head())

        relcols = ['Wh', 'Time', 'DAY']


        df_plt = pd.DataFrame(df.pivot_table(index='Time', columns='DAY', values='Wh', aggfunc='sum'))
        df_plt.dropna(inplace=True)
        df_plt.reset_index(inplace=True)

        return df_plt

   ##### retrieve and transform data####
    def make_graph(self, fig, ax, df_plt):
        #print(df_plt.columns)

        #print(df_plt.head())
        #print(plt.style.available)
        plt.style.use('dark_background')
        plot_bg_color = '#2d3436'

        #fig, ax = plt.subplots(figsize=(3,2))
        fig.patch.set_facecolor(plot_bg_color)
        ax.set_facecolor(plot_bg_color)
        ax.axes.xaxis.set_ticklabels([])
        ax.axes.xaxis.set_ticks([])
        ax.tick_params(axis='y', labelsize= 8)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)

        #plt.xticks(rotation=90)
        ax = plt.plot(df_plt.Time, df_plt.today, linewidth=3, color='#fbc531', label='today')
        ax = plt.plot(df_plt.Time, df_plt.yesterday, linewidth=1, color='#636e72', label='yesterday')
        plt.legend(facecolor=plot_bg_color, frameon = False, bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left',
                ncol=2,  borderaxespad=0., prop={'size': 8})

        #df_plt.yesterday.plot(kind='bar')
        #plt.show()
        #
        #plt.savefig('graph.png', dpi=80, facecolor=plot_bg_color, edgecolor=plot_bg_color, orientation='portrait', )
        #plt.show()
        return ax


    ##### retrieve and transform data####
    def make_48_hr_graph(self):
        data_parsed = self.get_details_yesterday() # collecting data directly from API
        start_date = self.get_yesterday_date_string()

        df = pd.DataFrame.from_dict(data_parsed, orient='index')
        df.reset_index(inplace=True)
        df.columns=['TS', 'Wh']
        df.TS = df.TS.astype(int)

        df['Datetime'] = df.apply(lambda x: self.convert_to_datetime(start_date, x['TS']), axis=1)
        df.drop(columns='TS', inplace=True)
        df['Date'] = df['Datetime'].dt.date
        df['Time'] = df['Datetime'].dt.strftime('%H:%M')
        df['Time'] = pd.to_datetime(df.Time).dt.time
        df['DAY'] = np.nan
        yesterday = str(df.Date.min())
        today = str(df.Date.max())
        df.Date = df.Date.astype(str)

        df['DAY'].loc[df.Date==yesterday] = 'yesterday'
        df['DAY'].loc[df.Date==today] = 'today'

        df.Time = df.Time.astype(str)
        df['Time'] = pd.to_datetime(today + ' ' + df.Time)

        print(df.loc[df.DAY=='yesterday'].head())

        relcols = ['Wh', 'Time', 'DAY']


        df_plt = pd.DataFrame(df.pivot_table(index='Time', columns='DAY', values='Wh', aggfunc='sum'))
        df_plt.dropna(inplace=True)
        df_plt.reset_index(inplace=True)

        #print(df_plt.columns)

        #print(df_plt.head())
        #print(plt.style.available)
        plt.style.use('dark_background')
        plot_bg_color = '#2d3436'

        fig, ax = plt.subplots(figsize=(3,2))
        #fig.patch.set_facecolor(plot_bg_color)
        ax.set_facecolor(plot_bg_color)
        ax.axes.xaxis.set_ticklabels([])
        ax.axes.xaxis.set_ticks([])
        ax.tick_params(axis='y', labelsize= 8)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)

        #plt.xticks(rotation=90)
        ax = plt.plot(df_plt.Time, df_plt.today, linewidth=3, color='#fbc531', label='today')
        ax = plt.plot(df_plt.Time, df_plt.yesterday, linewidth=1, color='#636e72', label='yesterday')
        plt.legend(facecolor=plot_bg_color, frameon = False, bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left',
                ncol=2,  borderaxespad=0., prop={'size': 8})

        #df_plt.yesterday.plot(kind='bar')
        #plt.show()
        #
        #plt.savefig('graph.png', dpi=80, facecolor=plot_bg_color, edgecolor=plot_bg_color, orientation='portrait', )
        #plt.show()
        return ax

if __name__ == "__main__":
    url = 'http://192.168.178.32'
    device_id = 1
    gu = graph_updater(url, device_id)
    #gu.get_details_yesterday()
    ax = gu.make_48_hr_graph()
    plt.show()
    '''
    data_parsed = gu.get_details_yesterday() # collecting data directly from API
    start_date = gu.get_yesterday_date_string()

    df = pd.DataFrame.from_dict(data_parsed, orient='index')
    df.reset_index(inplace=True)
    df.columns=['TS', 'Wh']
    df.TS = df.TS.astype(int)
    print(df.head())
    print(start_date)
    first = df['TS'].min() 
    last = df['TS'].max() 
    print(first, last)
    gu.convert_to_datetime(start_date, first)
    gu.convert_to_datetime(start_date, last)
    df['Datetime'] = df.apply(lambda x: gu.convert_to_datetime(start_date, x['TS']), axis=1)
    '''