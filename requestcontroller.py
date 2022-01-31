# imports for RequestController
import RequestReader as rr
from datetime import datetime as dt
import datetime
import froniusscanner
#import threading
import threading, time, signal
from datetime import timedelta
from graph_updater import graph_updater
import json
import pandas as pd
import traceback


# global parameters 
OFFLINE_TESTING = False # if true will read from a stored file - False will try to retrieve data
TESTING = False

WAIT_TIME_SECONDS = 1
MAX_RETRIES_LAN_SCAN = 10


class RequestController:
    def __init__(self):
        self.connected = False # change when implementing autoconnect
        self.first_run = True
        self.device_id = None
        self.statuscode = None
        self.status = None
        self.starttime = datetime.time(8,0,0) # only relevant, if no history in inverter
        self.endtime = datetime.time(16,0,0) # only relevant if no history in inverter
        self.guipage = 'MainPage'

        self.update_frequency = 5 # setting how often the mainloop checks for connection
        self.fs = froniusscanner.FroniusScanner()
        self.url = self.fs.get_url()
        self.rr = rr.RequestReader(self.url,"") # passing empty apistring
        
        self.co2_factor = 0 
        self.cash_factor = 0
        # storing data from scheduled requests
        self.frameupdate_data = None
        self.cum_data = None
        self.max_data = None
        self.logger_info = None
        #self.graph48 = None
        self.graph_data = None

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        self.joblist = [
            Job(interval=timedelta(seconds=5), execute=self.get_frame_update),
            Job(interval=timedelta(seconds=20), execute=self.get_max_data),
            Job(interval=timedelta(seconds=20), execute=self.get_logger_info),
            Job(interval=timedelta(seconds=20), execute=self.get_cumulative_data),
            Job(interval=timedelta(seconds=10), execute=self.get_device_status),  
            Job(interval=timedelta(seconds=20), execute=self.generate_graph_data)
            #Job(interval=timedelta(seconds=WAIT_TIME_SECONDS), execute=foo), # check if still running
            
        ] 
        
        #self.startup()
        #self.start_all_jobs()

    def generate_graph_data(self):
        gu = graph_updater(self.url, self.device_id)
        try:
            self.graph_data = gu.collect_graph_data()
        except Exception as e:
            print(f'Could not collect data for graph - Error {e}')

    def get_graph_data(self):
        return self.graph_data

    def get_gui_page(self):
        return self.guipage

    def scan_fronius(self):
        for i in range(MAX_RETRIES_LAN_SCAN):
            print(f'LAN-Scan {i+1}/{MAX_RETRIES_LAN_SCAN}')
            try:
                self.fs.scan_lan()
                if self.fs.device_found:
                    break
            except Exception as e:
                print('Error: {e}')
            
            print('Could not connect')
            exit()

    def get_working_hours(self):        
        '''get's a history retrieve for yesterday, and checks, when the log started'''
        '''using parsing logic from graph_updater'''
        
        # collect device id first


        #try:
        max_retries = 10
        for i in range(max_retries):
            self.device_id = int(self.fs.get_device_id())
            if self.device_id != None:
                break

        if self.device_id != None:
            print('getting working hours')
            yesterday = dt.today() - timedelta(days=1)
            yesterday_str = dt.strftime(yesterday, '%d.%m.%Y')
            t = rr.RequestHictoricProductionSystemDetail(self.url, self.device_id, yesterday_str, yesterday_str)
            data = t.get_data()
            if TESTING:
                filename = 'testdata\history\hist_28.10.2020-28.10.2020.json'
                with open(filename) as jsonfile:
                    data = json.load(jsonfile)
            
            data_parsed = data['EnergyReal_WAC_Sum_Produced']['Values']

            df = pd.DataFrame.from_dict(data_parsed, orient='index')
            df.reset_index(inplace=True)
            df.columns=['TS', 'Wh']
            df.TS = df.TS.astype(int)

            # only on method from graph_updater used (not clean)
            gu = graph_updater(self.url, self.device_id)
            start_date = gu.get_yesterday_date_string()
            df['Datetime'] = df.apply(lambda x: gu.convert_to_datetime(start_date, x['TS']), axis=1)
            
            # adding 30 min on each end to adjust for different susrise / sunset time
            starttime = df.Datetime.min()-timedelta(minutes=30)
            endtime = df.Datetime.max()+timedelta(minutes=30)

            
        else:
            print('Could not get device id. Start and Endtime remain unchanged')
        #except Exception as e:
        #print('Error: {e}')
        #starttime = dt.now().time()
        #endtime = starttime + timedelta(hours=1)
        return starttime.time(), endtime.time()

    def simple_main_loop(self):
        print('Starting jobs')
        self.start_all_jobs()

        while True:
            print('Main Loop running')    
            
            # get time, when the status is changed - in the morning, just repeat - in the evening - go to evening mode
            #print('Setting Working Hours')
            #st, et = self.get_working_hours()    
            #self.starttime = st
            #self.endtime = et
            #print(self. starttime, self.endtime)
            # get yesterday's working hours (+/- offset)


            # core of main-loop should never stop until application is closed via mainthread (gui)
            #print(f'Current Status:  ({last_statuscode})')
            # status 7 means Inverter is running
            
            print('Getting device status')
            self.get_device_status()
            print(f'FrameUpdate: {self.frameupdate_data}' )
            print(f'Cumdata: {self.cum_data}')
            print(f'Maxdata: {self.max_data}')
            print(f'LoggerInfo: {self.logger_info}')

            print('Mainloop Sleeps')
            time.sleep(self.update_frequency)            
            
            print(f'Status changed to {self.status} ({self.statuscode})')
            
            for j in self.joblist:
                if j.is_alive:
                    pass
                else: 
                    print(f'Job {f} is not alive. Restarting Jobs')
                    for j in self.joblist:
                        try:
                            j.stop()
                        except:
                            print('Could not stop Job {f}')
                    time.sleep(5)
                    self.start_all_jobs()

    def main_loop(self):
        print('Main Loop running')
        print('Starting jobs')
        self.start_all_jobs()
        
        # get time, when the status is changed - in the morning, just repeat - in the evening - go to evening mode
        print('Setting Working Hours')
        st, et = self.get_working_hours()    
        self.starttime = st
        self.endtime = et
        print(self. starttime, self.endtime)
        # get yesterday's working hours (+/- offset)


        # core of main-loop should never stop until application is closed via mainthread (gui)
        while True:
            last_statuscode = self.statuscode
            print(f'Current Status:  ({last_statuscode})')
            # status 7 means Inverter is running
            while self.statuscode == 7:
                print('Getting device status')
                self.get_device_status()
                print(f'FrameUpdate: {self.frameupdate_data}' )
                print(f'Cumdata: {self.cum_data}')
                print(f'Maxdata: {self.max_data}')

                time.sleep(self.update_frequency)            
            
            print(f'Status changed to {self.status} ({self.statuscode})')
            self.close_all_jobs()
            self.get_working_hours()

            currtime = dt.now().time()
            print(type(currtime))
            print(type(self.starttime))
            print(type(self.endtime))
            
            # going to sleep
            if (currtime>self.endtime) or (currtime<starttime):    
                print('Currently Sleeping')
                self.guipage = 'DetailPage'
                self.update_frequency=300
                time.sleep(self.update_frequency)
                self.get_device_status()
                self.close_all_jobs()

            # waking up
            elif (currtime>self.startime):
                print('waking up') # while connected retry - if connection lost scan lan
                self.guipage = 'mainpage'
                self.update_frequency=10
                time.sleep(self.update_frequency)
                self.get_device_status()
                if (self.statuscode==7) and (last_statuscode != 7):
                    self.start_all_jobs()

            else:
                if (self.connected == False) & (currtime>starttime+timedelta(minutes=90)):
                    self.scan_lan()
                    self.get_device_status()
                    if (self.statuscode==7) and (last_statuscode != 7):
                        self.start_all_jobs()

                # should be online scanning LAN

            # morning 
            # evening
            # working hours
            
        print('Done - closing it all')
        exit()

    def startup(self):
        if not TESTING: 
            if self.first_run:
                print('First run - starting LAN-Scan')
                self.scan_fronius()            
                
                    
            self.statuscode, self.status = self.get_device_status()
            if self.fs.device_found:
                self.connected = True
                self.device_id = self.fs.device_id
                #mainthread = Job(interval=None, target=self.simple_main_loop(), daemon=False)
                mainthread = threading.Thread(target=self.simple_main_loop, daemon=True)
                mainthread.start()

            else:
                print(f'Could not get connection: DeviceStatus {self.status} ({self.statuscode}) ')
                exit()
        else:
        # to override for testing purposes
            self.connected = True
            #mainthread = threading.Thread(target=self.main_loop, daemon=True)
            mainthread.start()

    def start_all_jobs(self):
        for j in self.joblist:
            j.start()
            #j.join()

    def close_all_jobs(self):
        for j in self.joblist:
            j.stop()
    
    def get_frame_update(self):
        if not OFFLINE_TESTING:
            if self.connected:
                t = rr.RequestInverterRealtimeDataSystem(self.url)        
                
                
        else:
            t = rr.RequestInverterRealtimeDataDevice_FILETEST(1,'dummyurl','testdata\pv14-06-56.json')
            pass

        #datalist = t.get_available_data()
        co2_factor = 0.563 #should be updated from system
        #print(datalist)
        try: 
            data, timestamp = t.get_data()
            energy_current = data['PAC']['Values']['1']
            energy_today = data['DAY_ENERGY']['Values']['1']/1000
            CO2 = data['TOTAL_ENERGY']['Values']['1']*self.co2_factor/1000

            self.frameupdate_data = (energy_current, energy_today, CO2)
        except Exception as e:
            print(f'Could not do FrameUpdate: Error {e}')
            traceback.print_exc()

    def collect_frame_update_data(self):
        if self.frameupdate_data != None:
            out = self.frameupdate_data
        else:
            out = (0,0,0)
        #print(out)
        return (out)

    def make_graph(self):
        try:
            gu = graph_updater(self.url, self.device_id)
            self.graph48 = gu.make_48_hr_graph()
            print('Graph Updated')
            self.graph48.show()

        except Exception as e:
            print(f'Could not updated Graph: Error {e}')
            traceback.print_exc()

    def collect_graph48(self):
        return self.graph48

    def get_cumulative_data(self):
        if self.cum_data != None:
            out = self.cum_data

        print('Getting Cumulative data System...')
        try:
            t = rr.RequestInverterRealtimeDataSystemMinMax(self.url)
            data, timestamp = t.get_data()
            energy_today = data['DAY_ENERGY']['Values']['1']
            energy_this_year = data['YEAR_ENERGY']['Values']['1']
            energy_total = data['TOTAL_ENERGY']['Values']['1']
            co2_today = energy_today*self.co2_factor
            co2_this_year = energy_this_year * self.co2_factor
            co2_total = energy_total * self.co2_factor
            cash_today = energy_today*self.cash_factor/1000
            cash_this_year = energy_this_year * self.cash_factor/1000
            cash_total = energy_total * self.cash_factor/1000
            
            self.cum_data = (energy_today, energy_this_year, energy_total, co2_today, co2_this_year, co2_total, cash_today, cash_this_year, cash_total )
        
        except Exception as e:
            print(f'Could not get Cumulative data Syste: Error {e} ')
            traceback.print_exc()
    
    def collect_cum_data(self):
        if self.cum_data != None:
            out = self.cum_data
        else:
            out = (0,0,0,0,0,0,0,0,0)
        #print(out)
        return (out)

    def get_max_data(self):
        if self.max_data != None:
            out = self.max_data

        print('Getting Max data Device')
        try:
            print(self.url, self.device_id)        
            t = rr.RequestInverterRealtimeDataDeviceMinMax(self.url, self.device_id)
            print(t.get_api_string())
            time.sleep(1)
            data, timestamp = t.get_data()
            
            max_energy_today = data['DAY_PMAX']['Value']
            max_energy_this_year = data['YEAR_PMAX']['Value']
            max_energy_total = data['TOTAL_PMAX']['Value']
            
            self.max_data = (max_energy_today, max_energy_this_year, max_energy_total)

        except Exception as e:
            print(f'Could not get MaxData data Device: Error {e} ')
            traceback.print_exc()

            
    def collect_max_data(self):
        if self.max_data != None:
            out = self.max_data
        else:
            out = (0,0, 0)
        #print(out)
        return (out)



    def get_logger_info(self):
        if self.logger_info != None:
            out = self.logger_info

        print('Getting Logger Info')
        try:        
            t = rr.RequestLoggerInfo(self.url)
            data = t.get_data()
            
            co2factor = data['CO2Factor'] 
            cashfactor = data['CashFactor'] 
            hwverion = data['HWVersion']
            productid = data['ProductID'] 
            swversion = data['SWVersion'] 
            uniqueid = data['UniqueID']

            self.co2_factor = co2factor
            self.cash_factor = cashfactor
            self.logger_info = (self.url, self.device_id, co2factor, cashfactor, hwverion, productid, swversion, uniqueid)

        except Exception as e:
            print(f'Could not get LoggerInfo: Error {e} ')
            traceback.print_exc()

            
    def collect_logger_info(self):
        if self.logger_info != None:
            out = self.logger_info
        else:
            out = ("NA", "NA", 0,0, "NA", "NA","NA","NA")
        return (out)




    
    ## convert into job and function to collect from GUI
    @staticmethod
    def get_time_string():
        time = dt.now()
        timestr = dt.strftime(time, '%H:%M:%S')
        return timestr
    
    @staticmethod
    def get_date_string():
        date = dt.now()
        datestr = dt.strftime(date, '%d %b %Y')
        return datestr

    def get_device_status(self):
        try:
            t = rr.RequestInverterInfo(self.url)
            answer = t.make_request()
            self.statuscode = answer['Body']['Data']['1']['StatusCode'] 
            print(self.statuscode)
            status_dict = {
                0: 'Startup', 
                1: 'Startup', 
                2: 'Startup',
                3: 'Startup', 
                4: 'Startup', 
                5: 'Startup',
                6: 'Startup',
                7: 'Running', 
                8: 'Standby', 
                9: 'Bootloading',
                10: 'Error'}
            self.status = status_dict[self.statuscode]
            
        except Exception as e:
            print(f'Could not get status code Error {e}')
            self.status = 'No Connection'
            self.statuscode = 99
            self.connected=False

        return (self.statuscode, self.status)

class ProgramKilled(Exception):
    pass

def foo():
    print (time.ctime())
    
def signal_handler(signum, frame):
    raise ProgramKilled
    
class Job(threading.Thread):
    def __init__(self, interval, execute, *args, **kwargs):
        threading.Thread.__init__(self)
        self.daemon = False
        self.stopped = threading.Event()
        self.interval = interval
        self.execute = execute
        self.args = args
        self.kwargs = kwargs
        
    def stop(self):
                self.stopped.set()
                self.join()
    def run(self):
            while not self.stopped.wait(self.interval.total_seconds()):
                self.execute(*self.args, **self.kwargs)
            

if __name__ == "__main__":
    rc = RequestController()
    url = 'http://192.168.173.32'
    device_id = 1
    
    t = rc.RequestInverterRealtimeDataSystemMinMax(self.url)
    data, timestamp = t.get_data()
    
    print(data)
    #t = rc.get_cumulative_data()
    #print(t)
    #t = rc.rr.RequestInverterRealtimeDataDeviceMinMax(url, device_id)
    #data = t.get_data()
    #print(data)

    '''
    while True:
          try:
              print('Mainthread sleeps')
              time.sleep(10)
              
          except ProgramKilled:
              print ("Program killed: running cleanup code")
              for j in rc.joblist:
                  j.stop()
              #job.stop()
              #jobframeupdate.stop()
              break
    '''