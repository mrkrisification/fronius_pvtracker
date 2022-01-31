import json
import requests
from datetime import datetime, timedelta
import time

class RequestReader:
    def __init__(self, inverterUrl, apistring=None):
       
       self.inverterUrl = inverterUrl
       self.apistring = apistring
       
    def setInverterUrl(self, inverterurl):
        '''sets URL of inverter for RequestReader Object'''
        self.inverterUrl = inverterurl

    def make_request(self):
        '''generic RequestReader to Fronius Inverters, takes apistring as argument
        returns a dictionary from the request'''
        try:
            #r = requests.get('http://192.168.1.26/solar_api/v1/GetInverterRealtimeData.cgi?scope=System&DataCollection=CommonInverterData')
            r = requests.get(self.inverterUrl+self.apistring)
            #print(r.text)
            output = json.loads(r.text)
            return output
        
        except Exception as e:
            print(f"Error: {e}")
        
        
    def get_api_string(self):
        return self.apistring


    def make_file_request(self, filepath):
        '''for testing only - reads stored file requests'''
        try:
            with open(filepath) as json_file:
                r = json.load(json_file)
                output = r
        except Exception as e:
                print(f"Error: {e}")
        return output

    def show_json(self, output):
        '''for testing only - shows formatted json output'''
        print(json.dumps(output, indent=4, sort_keys=True))


class RequestAPIVersion(RequestReader):
    def __init__(self, url):
        self.apistring = '/solar_api/GetAPIVersion.cgi'
        super().__init__(url, self.apistring)
    
    def get_API_version(self):
        output = super().make_request()
        return output['APIVersion']


class RequestLoggerInfo(RequestReader):
    def __init__(self, url):
        self.apistring = '/solar_api/v1/GetLoggerInfo.cgi'
        super().__init__(url, self.apistring)

    def get_available_data(self):
        '''returns a list of all available Keys in Data'''
        output = super().make_request()
        return list(output['Body']['LoggerInfo'].keys())

    def get_data(self):
        '''performs request of respective apistring and converts it into a dict or list of dicts'''
        output = super().make_request()
        datadict = output['Body']['LoggerInfo']
        #timestamp = output['Head']['Timestamp']
        return datadict


class RequestInverterInfo(RequestReader):
    def __init__(self, url):
        self.apistring = '/solar_api/v1/GetInverterInfo.cgi'
        super().__init__(url, self.apistring)

    def get_inverter_ids(self):
        '''returns a list of all available Keys in Data'''
        output = super().make_request()
        return list(output['Body']['Data'].keys())


class RequestPowerFlowRealtime(RequestReader):
    def __init__(self, url):
        self.apistring = '/solar_api/v1/GetPowerFlowRealtimeData.fcgi'
        super().__init__(url, self.apistring)


class RequestInverterRealtimeDataSystem(RequestReader):
    def __init__(self, url):
        self.apistring = '/solar_api/v1/GetInverterRealtimeData.cgi?Scope=System&DataCollection=CommonInverterData'
        super().__init__(url, self.apistring)

    def get_available_data(self):
        '''returns a list of all available Keys in Data'''
        output = super().make_request()
        return list(output['Body']['Data'].keys())

    def get_data(self):
        '''performs request of respective apistring and converts it into a dict or list of dicts'''
        output = super().make_request()
        datadict = output['Body']['Data']
        timestamp = output['Head']['Timestamp']
        return datadict, timestamp


class RequestInverterRealtimeDataSystemMinMax(RequestReader):
    def __init__(self, url):
        self.apistring = '/solar_api/v1/GetInverterRealtimeData.cgi?Scope=System&DataCollection=MinMaxInverterData'
        super().__init__(url, self.apistring)

    def get_available_data(self):
        '''returns a list of all available Keys in Data'''
        output = super().make_request()
        return list(output['Body']['Data'].keys())

    def get_data(self):
        '''performs request of respective apistring and converts it into a dict or list of dicts'''
        output = super().make_request()
        datadict = output['Body']['Data']
        timestamp = output['Head']['Timestamp']
        return datadict, timestamp


class RequestInverterRealtimeDataDeviceMinMax(RequestReader):
    def __init__(self, url, device_id):
        self.collection = 'MinMaxInverterData'
        self.device_id = device_id
        self.apistring = '/solar_api/v1/GetInverterRealtimeData.cgi?Scope=Device&DeviceId=' + str(self.device_id) + '&DataCollection=' + self.collection
        super().__init__(url, self.apistring)

    def get_available_data(self):
        '''returns a list of all available Keys in Data'''
        output = super().make_request()
        return list(output['Body']['Data'].keys())

    def get_data(self):
        '''performs request of respective apistring and converts it into a dict or list of dicts'''
        output = super().make_request()
        datadict = output['Body']['Data']
        timestamp = output['Head']['Timestamp']
        return datadict, timestamp


class RequestInverterRealtimeDataDevice(RequestReader):
    def __init__(self, url, device_id):
        self.collection = 'CommonInverterData'
        self.device_id = device_id
        self.apistring = '/solar_api/v1/GetInverterRealtimeData.cgi?Scope=Device&DeviceId=' + str(self.device_id) + '&DataCollection=' + self.collection
        super().__init__(url, self.apistring)

    def get_available_data(self):
        '''returns a list of all available Keys in Data'''
        output = super().make_request()
        return list(output['Body']['Data'].keys())

    def get_data(self):
        '''performs request of respective apistring and converts it into a dict or list of dicts'''
        output = super().make_request()
        datadict = output['Body']['Data']
        timestamp = output['Head']['Timestamp']
        return datadict, timestamp


class RequestHictoricProductionDeviceDaily(RequestReader):
    def __init__(self, url, device_id):
        self.channel = 'EnergyReal_WAC_Sum_Produced'
        #self.seriestype = 'Detail'
        
        self.seriestype = 'DailySum'
        self.device_id = device_id
        self.deviceclass = 'Inverter'
        
        # history requires start and enddate in Format %d.%m.%Y
        today = datetime.today()
        maxdays = 15 # API is limited to 16 days of History
        fmt = '%d.%m.%Y'
        enddate = today - timedelta(1)
        startdate = enddate - timedelta(maxdays)

        endstr = datetime.strftime(enddate, fmt)
        startstr = datetime.strftime(startdate, fmt)

        self.apistring = '/solar_api/v1/GetArchiveData.cgi?Scope=Device&DeviceId=' + str(self.device_id) + '&DeviceClass='+self.deviceclass+'&SeriesType=DailySum&StartDate=' +startstr +'&EndDate='+endstr+'&Channel=' + self.channel
        #self.apistring = '/solar_api/v1/GetArchiveData.cgi?Scope=System&SeriesType=DailySum&StartDate=' +startstr +'&EndDate='+endstr+'&Channel=' + self.channel
        super().__init__(url, self.apistring)

    def get_available_data(self):
        '''returns a list of all available Keys in Data'''
        output = super().make_request()
        return list(output['Body']['Data'][f'inverter/{self.device_id}'].keys())

    def get_data(self):
        '''performs request of respective apistring and converts it into a dict or list of dicts'''
        output = super().make_request()
        datadict = output['Body']['Data'][f'inverter/{self.device_id}']
        
        #datadict = output['Body']['Data'][f'inverter/{self.device_id}']
        return datadict


class RequestHictoricProductionDeviceDetail(RequestReader):
    def __init__(self, url, device_id, start_date, end_date):
        '''deliveres detail production in 5 min invervals. requires a start and enddate in format %d.%m.%Y
        API is limited to 16 days for seriestype Details '''
        
        self.channel = 'EnergyReal_WAC_Sum_Produced'
        #self.seriestype = 'Detail'
        startstr = start_date 
        endstr = end_date
        self.seriestype = 'Details'
        self.device_id = device_id
        self.deviceclass = 'Inverter'
        
        self.apistring = '/solar_api/v1/GetArchiveData.cgi?Scope=Device&DeviceId=' + str(self.device_id) + '&DeviceClass='+self.deviceclass+'&StartDate=' +startstr +'&EndDate='+endstr+'&Channel=' + self.channel
        #self.apistring = '/solar_api/v1/GetArchiveData.cgi?Scope=System&SeriesType=DailySum&StartDate=' +startstr +'&EndDate='+endstr+'&Channel=' + self.channel
        super().__init__(url, self.apistring)

    def get_available_data(self):
        '''returns a list of all available Keys in Data'''
        output = super().make_request()
        return  list(output['Body']['Data'][f'inverter/{self.device_id}'].keys())
        
    def get_data(self):
        '''performs request of respective apistring and converts it into a dict or list of dicts'''
        output = super().make_request()
        datadict = output['Body']['Data']['inverter/1']
        return datadict


class RequestHictoricProductionDeviceDetailTimeSpan(RequestReader):
    def __init__(self, url, device_id, start_date, end_date):
        '''deliveres detail production in 5 min invervals. requires a start and enddate in format %d.%m.%Y
        API is limited to 16 days for seriestype Details '''
        
        self.channel = 'TimeSpanInSec'
        #self.seriestype = 'Detail'
        startstr = start_date 
        endstr = end_date
        self.seriestype = 'Details'
        self.device_id = device_id
        self.deviceclass = 'Inverter'
        
        self.apistring = '/solar_api/v1/GetArchiveData.cgi?Scope=Device&DeviceId=' + str(self.device_id) + '&DeviceClass='+self.deviceclass+'&StartDate=' +startstr +'&EndDate='+endstr+'&Channel=' + self.channel
        #self.apistring = '/solar_api/v1/GetArchiveData.cgi?Scope=System&SeriesType=DailySum&StartDate=' +startstr +'&EndDate='+endstr+'&Channel=' + self.channel
        super().__init__(url, self.apistring)

    def get_available_data(self):
        '''returns a list of all available Keys in Data'''
        output = super().make_request()
        return  list(output['Body']['Data'][f'inverter/{self.device_id}'].keys())
        
    def get_data(self):
        '''performs request of respective apistring and converts it into a dict or list of dicts'''
        output = super().make_request()
        datadict = output['Body']['Data']['inverter/1']
        return datadict




class RequestHictoricProductionDeviceDetail_last48(RequestReader):
    def __init__(self, url, device_id, history=1):
        self.channel = 'EnergyReal_WAC_Sum_Produced'
        #self.seriestype = 'Detail'
        
        #self.seriestype = 'DailySum'
        self.device_id = device_id
        self.deviceclass = 'Inverter'
        
        # history requires start and enddate in Format %d.%m.%Y
        today = datetime.today()
        history = history # API is limited to 16 days of History
        fmt = '%d.%m.%Y'
        enddate = today
        startdate = enddate - timedelta(history)

        endstr = datetime.strftime(enddate, fmt)
        startstr = datetime.strftime(startdate, fmt)

        self.apistring = '/solar_api/v1/GetArchiveData.cgi?Scope=Device&DeviceId=' + str(self.device_id) + '&DeviceClass='+self.deviceclass+'&StartDate=' +startstr +'&EndDate='+endstr+'&Channel=' + self.channel
        #self.apistring = '/solar_api/v1/GetArchiveData.cgi?Scope=System&SeriesType=DailySum&StartDate=' +startstr +'&EndDate='+endstr+'&Channel=' + self.channel
        super().__init__(url, self.apistring)

    def get_available_data(self):
        '''returns a list of all available Keys in Data'''
        output = super().make_request()
        return list(output['Body']['Data'][f'inverter/{self.device_id}'].keys())

    def get_data(self):
        '''performs request of respective apistring and converts it into a dict or list of dicts'''
        output = super().make_request()
        datadict = output['Body']['Data'][f'inverter/{self.device_id}']
        
        #datadict = output['Body']['Data'][f'inverter/{self.device_id}']
        return datadict


class RequestHictoricProductionSystemDetail(RequestReader):
    def __init__(self, url, device_id, start_date, end_date):
        '''deliveres detail production in 5 min invervals. requires a start and enddate in format %d.%m.%Y
        API is limited to 16 days for seriestype Details '''
        
        self.channel = 'EnergyReal_WAC_Sum_Produced'
        #self.seriestype = 'Detail'
        startstr = start_date 
        endstr = end_date
        self.seriestype = 'Details'
        self.device_id = device_id
        
        
        self.apistring = '/solar_api/v1/GetArchiveData.cgi?Scope=System'+'&StartDate=' +startstr +'&EndDate='+endstr+'&Channel=' + self.channel
        #self.apistring = '/solar_api/v1/GetArchiveData.cgi?Scope=System&SeriesType=DailySum&StartDate=' +startstr +'&EndDate='+endstr+'&Channel=' + self.channel
        super().__init__(url, self.apistring)

    def get_available_data(self):
        '''returns a list of all available Keys in Data'''
        output = super().make_request()
        return  list(output['Body']['Data'][f'inverter/{self.device_id}'].keys())
        
    def get_data(self):
        '''performs request of respective apistring and converts it into a dict or list of dicts'''
        output = super().make_request()
        datadict = output['Body']['Data'][f'inverter/{self.device_id}']['Data']
        return datadict

class RequestPowerFlowRealtimeData(RequestReader):
    def __init__(self, url):
        self.apistring = '/solar_api/v1/GetPowerFlowRealtimeData.fcgi'
        super().__init__(url, self.apistring)

    def get_available_data(self):
        '''returns a list of all available Keys in Data'''
        output = super().make_request()
        return list(output['Body']['Data'].keys())

    def get_data(self):
        '''performs request of respective apistring and converts it into a dict or list of dicts'''
        output = super().make_request()
        datadict = output['Body']['Data']
        timestamp = output['Head']['Timestamp']
        return datadict, timestamp



if __name__ == "__main__":
    
    url = 'http://192.168.178.32'

    '''    
    t = RequestAPIVersion(url)
    print(t.get_api_string())
    print(t.get_API_version())
    '''

    print('MinMax - Scope System')
    t = RequestInverterRealtimeDataSystemMinMax(url)
    print(t.get_api_string())
    print(t.get_available_data())
    data, timestamp = t.get_data()
    energy_today = data['DAY_ENERGY']['Values']['1']
    energy_now = data['PAC']['Values']['1']
    energy_this_year = data['YEAR_ENERGY']['Values']['1']
    energy_total = data['TOTAL_ENERGY']['Values']['1']

    print(energy_today, energy_now, energy_this_year, energy_total)
    
    '''
    print('MinMax - Scope Device')
    t = RequestInverterRealtimeDataDeviceMinMax(url, 1)
    print(t.get_available_data())
    time.sleep(1)
    data, timestamp = t.get_data()
    #print(data)
    max_energy_today = data['DAY_PMAX']['Value']
    max_energy_this_year = data['YEAR_PMAX']['Value']
    max_energy_total = data['TOTAL_PMAX']['Value']
    print(max_energy_today, max_energy_this_year, max_energy_total)

    
    print('Logger Info')
    t = RequestLoggerInfo(url)
    print(t.get_available_data())
    data = t.get_data()
    print(data)

    t = RequestHictoricProductionDeviceDaily(url, 1)
    api = t.get_api_string()
    print(api)

    r = RequestReader(url, '/solar_api/v1/GetArchiveData.cgi?Scope=Device&DeviceId=1&DeviceClass=Inverter&SeriesType=DailySum&StartDate=1.1.2010&EndDate=28.10.2020&Channel=EnergyReal_WAC_Sum_Produced')
    answer = r.make_request()
    print(answer)

    t = RequestInverterRealtimeDataDevice(url, 1)
    api = t.get_api_string()
    print(api)
    print(t.get_available_data())
    data = t.get_data()
    print(data)
    
    t = RequestInverterRealtimeDataSystemMinMax(url)
    api = t.get_api_string()
    print(api)
    print(t.get_available_data())
    data = t.get_data()
    print(data)
    with open(f'minmax.json', 'w') as outfile:
            json.dump(data, outfile)
    
    '''