import requests
import json
import configparser
from RequestReader import RequestAPIVersion, RequestInverterInfo
import threading
import time

class FroniusScanner:
    def __init__(self, ipbase = 'http://192.168.1.'): #setting default 
        self.IP_base = ipbase
        self.FRONIUS_URL = None
        self.device_id = None
        self.device_found = False
        self.config = configparser.ConfigParser()
        self.configfile = 'config.ini'
        self.read_config()
    
    def read_config(self):
        
        try:
            self.config.read(self.configfile)
            self.FRONIUS_URL = str(self.config['network']['url'])
            self.IP_base = str(self.config['network']['ipbase'])
        
        except Exception as e:
            print(f'Could not read config. Error {e}')
            pass

    def write_device_config(self):
        with open(self.configfile, 'w') as configfile:
            self.config['device']['deviceid'] = self.device_id
            self.config.write(configfile)

    def write_net_config(self):
        with open(self.configfile, 'w') as configfile:
            self.config['network']['url'] = self.FRONIUS_URL
            self.config['network']['ipbase']= self.IP_base
            self.config.write(configfile)


    
    def check_IP(self, url):
        timeout = 0.5
        #time.sleep(1)
        try:
            print(f'checking {url}')
            r = requests.get(url, timeout= timeout)
            r.raise_for_status()
            print(f'Connection on {url} found: {r.status_code}')
            self.check_api(url)
        except Exception as e:
            pass
        
    
    def scan_lan(self):
        '''scans LAN from ipbase 0 to 254 to check, if IP is responding'''
        
        self.device_id = False
        # make a requests with last know URL from config.ini before starting scan
        self.check_api(self.FRONIUS_URL)
        
        for i in range (255):
            
            if self.device_found == True:
                break

            url = self.IP_base + str(i)

            #s = threading.Thread(target=self.check_IP, args=(url,))
            #s.start()
            #time.sleep(0.2)
            self.check_IP(url)
            

        if self.device_found == False:
            print('No Fronius Devices found')

    def check_api(self, url_found):
        '''checks if at the found url the Fronius API v1 is available'''
        #print(f'Checking for API at {url_found}')
        try:
            print('Checking api')
            ar = RequestAPIVersion(url_found)
            api_response = ar.get_API_version()
            if api_response==1:
                print(f'Fronius device with matching API Version found at: {url_found}')
                self.FRONIUS_URL = url_found
                self.write_net_config()
                self.device_found = True

                # get the first inverterID found - only one ID currently supported
                try:
                    ii = RequestInverterInfo(url_found)
                    device_list = ii.get_inverter_ids()
                    self.device_id = device_list[0]
                    self.write_device_config()
                    print(f'Device found with Device_ID {self.device_id}')
                except Exception as e:
                    print(f'Error: {e}')

        except Exception as e:
            print(f'Error: {e}')

    def get_url(self):
        return  self.FRONIUS_URL

    def get_device_id(self):
        return self.device_id        



if __name__ == "__main__":
    f = FroniusScanner()
    f.scan_lan()
