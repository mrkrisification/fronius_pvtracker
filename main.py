# imports for GUI
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
#from tkinter import *
from PIL import ImageTk, Image, ImageOps
import requestcontroller as rc
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
import threading
import random
from graph_updater import graph_updater


# global parameters for GUI
HEADER_FONT = ("Helvetica", 30, 'bold')
GIANT_FONT = ("Helvetica", 40, 'bold')
LARGE_FONT = ("Helvetica", 20) 
SMALL_FONT = ("Helvetica", 12) 
RELIEF = tk.GROOVE
FRAME_COLOR = '#636e72'
BACK_GROUND_COLOR = '#2d3436'
FONT_COLOR = '#dfe6e9'
HEADER_FONT_COLOR='#dfe6e9'
ENERGY_FONT_COLOR='#fbc531'
PADX = 1
PADY = 1
BUTTON_BG = '#2d3436'
BUTTON_FONT_COLOR = '#dfe6e9'
UPDATE_FREQUENCY = 5  # in seconds
UPDATE_FREQUENCY_GRAPH = 20 # in seconds
UPDATE_FREQUENCY_PAGE_CHECK = 1800 # in seconds


class Main(tk.Tk):
    def __init__(self, *args, **kwargs):

        tk.Tk.__init__(self, *args, **kwargs)
        if os.name != 'nt': #developing on windows - should only use fullscreen on raspberry
            self.attributes('-fullscreen', True)
        self.rc = rc.RequestController()
        
        self.grid_rowconfigure(0, weight=1) 
        self.grid_columnconfigure(0, weight=1)

        main_container = tk.Frame(self)
        main_container.grid(column=0, row=0, sticky = "nsew")
        main_container.grid_rowconfigure(0, weight = 1)
        main_container.grid_columnconfigure(0, weight = 1)

        self.frames = {}

        for fr in (MainPage, DetailPage, Settings):
            frame = fr(main_container, self)
            self.frames[fr] = frame
            frame.grid(row = 0, column = 0, sticky = "nsew")
        
        self.after(UPDATE_FREQUENCY_PAGE_CHECK*1000, func=lambda:self.check_page())
        self.show_frame(MainPage)



    def show_frame(self, pointer):
        frame = self.frames[pointer]
        frame.tkraise()

    def on_closing(self):
        if messagebox.askokcancel('Quit', 'Do you want to quit?'):
            print('closing')
            # not closing app yet
            self.rc.close_all_jobs()
            self.destroy()

    def check_page(self):
        page = self.rc.get_gui_page()
        print('Controller requested switch to '+page)
        if page == 'DetailPage':
            self.show_frame(DetailPage)
        if page == 'MainPage':
            self.show_frame(MainPage)

        self.after(UPDATE_FREQUENCY_PAGE_CHECK*1000, func=lambda:self.check_page())

class MainPage(tk.Frame):
    
    
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=FRAME_COLOR)
        self.after(int(UPDATE_FREQUENCY*1000), self.frame_update)
        self.after(int(UPDATE_FREQUENCY_GRAPH*1000), self.update_graph_image)
        self.after(int(UPDATE_FREQUENCY*1000), self.update_status_label)

        self.controller = controller
        # variables used for this Page
        self.energy_current = 0
        self.energy_today = 0
        self.CO2 = 0
        self.status = ''
        self.datestr = ''
        self.timestr = ''
        #self.graph48 = Figure()
        self.figure = Figure(figsize=(4,2), dpi=100)
        self.axes = self.figure.add_subplot(111)

        # setting weights within  page
        self.columnconfigure(0, weight = 1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight = 0)
        self.rowconfigure(1, weight = 1)
        self.rowconfigure(2, weight = 0)
        self.rowconfigure(3, weight = 0)
        self.rowconfigure(4, weight = 0)

        
        self.headerframe = tk.Frame(self, bg=BACK_GROUND_COLOR)
        self.headerframe.grid(row = 0, column=0, columnspan=2, sticky='nswe', padx=PADX, pady=PADY)
        self.headerframe.rowconfigure(0, weight=0)
        self.headerframe.columnconfigure(1, weight=1)
        self.headerframe.columnconfigure(2, weight=1)

        logo_path = os.path.join('resources/solar-energy_gui.png')
        load = Image.open(logo_path)
        render=ImageTk.PhotoImage(load)
        self.img = tk.Label(self.headerframe, image=render, bg=BACK_GROUND_COLOR)
        self.img.image = render
        self.img.grid(row=0, column=0, sticky='nswe', padx=20, pady=5)
        self.label = tk.Label(self.headerframe, text = "PV Tracker", font = SMALL_FONT, bg=BACK_GROUND_COLOR, fg=HEADER_FONT_COLOR)
        self.label.grid(row = 0, column=1, padx = 0, pady = 0, sticky='nswe')
        self.label = tk.Label(self.headerframe, text = "v10", font = SMALL_FONT, bg=BACK_GROUND_COLOR, fg=HEADER_FONT_COLOR)
        self.label.grid(row = 0, column=2, padx = 10, pady = 0, sticky='nse')

        # main value - should be huge
        self.energyLbl = tk.Label(self, text=f'{self.energy_current} W', font=GIANT_FONT, bg=BACK_GROUND_COLOR, fg=ENERGY_FONT_COLOR)
        self.energyLbl.grid(row=1, column=0, rowspan=2, sticky='nswe', padx=PADX, pady=PADY)
        
        # graph as big as possible on the right
        

        #self.img = tk.Label(self.headerframe, image=render, bg=BACK_GROUND_COLOR)
        
        self.graphCanv = FigureCanvasTkAgg(self.figure, self)
        #self.graphCanv = FigureCanvasTkAgg(self.graph48, self)
        
        #self.graphCanv.draw()
        self.graphCanv.get_tk_widget().grid(row=1, column=1, rowspan=2, sticky='nswe', padx=PADX, pady=PADY)
        

        
        # frame for holding 2 smaller labels
        self.detailframe = tk.Frame(self, padx=0, pady=0)
        self.detailframe.rowconfigure(0, weight=1)
        self.detailframe.rowconfigure(1, weight=1)
        self.detailframe.columnconfigure(0, weight=1)
        
        self.detailframe.grid(row=3, column=0, rowspan=1, sticky='nswe', padx=PADX, pady=PADY)
        
        #adding to frame
        # using dayenergyLBL to set WIDTH
        # NOT ELEGENT BUT WORKING
        self.dayenergyLbl = tk.Label(self.detailframe, width=25, text=f'{self.energy_today:.1f} kWh', font=LARGE_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.dayenergyLbl.grid(row=0, sticky='nswe')
        self.co2Lbl = tk.Label(self.detailframe, text=f'{self.CO2:.1f} kg Co2', font=LARGE_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.co2Lbl.grid(row=1, sticky='nswe')
        
        #frame displaying date and time
        self.timeframe= tk.Frame(self, padx=0, pady=0)
        self.timeframe.rowconfigure(0, weight=1)
        self.timeframe.rowconfigure(1, weight=1)
        self.timeframe.columnconfigure(0, weight=1)
        self.timeframe.grid(row=3, column=1, rowspan=1, sticky='nsew', padx=PADX, pady=PADY)
        
        #update time every second
        self.timeframe.after(1000, self.update_date_time_labels)

        self.dateLbl = tk.Label(self.timeframe, text=self.datestr, font=LARGE_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.timeLbl = tk.Label(self.timeframe, text=self.timestr, font=LARGE_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.dateLbl.grid(row=0, column=0, sticky='nswe')
        self.timeLbl.grid(row=1, column=0, sticky='nswe')

        # frame showing status and navigation buttons
        self.statusframe = tk.Frame(self, padx=PADX, pady=PADY, bg=BACK_GROUND_COLOR)
        self.statusframe.grid(row=4, column=0, columnspan=2, sticky='nswe')

        self.statusframe.rowconfigure(0,weight=1)
        self.statusframe.columnconfigure(0,weight=1)
        self.statusframe.columnconfigure(1,weight=1)
        self.statusframe.columnconfigure(2,weight=1)
        self.statusframe.columnconfigure(3,weight=1)

        self.godetailBtn = tk.Button(self.statusframe, text = "Detail Page", command = lambda: controller.show_frame(DetailPage), 
        bg=BUTTON_BG, fg=BUTTON_FONT_COLOR, font=SMALL_FONT)
        self.godetailBtn.grid(row=0, column = 0, sticky = 'nswe')

        self.gosettingsBtn = tk.Button(self.statusframe, text = "Settings", command = lambda: controller.show_frame(Settings), 
        bg=BUTTON_BG, fg=BUTTON_FONT_COLOR, font=SMALL_FONT)
        self.gosettingsBtn.grid(row=0, column=3, sticky = 'nswe')

        #label color should change with respective status - connected = red, searching = red
        self.statusLbl = tk.Label(self.statusframe, text=self.status, font=SMALL_FONT, bg=BACK_GROUND_COLOR)
        self.statusLbl.grid(row=0, column=1, columnspan=2, sticky='nswe')

        #exitBtn = ttk.Button(statusframe, text = "EXIT", command = quit)
        #exitBtn.grid(row=0, column=2, sticky = 'nswe')

    def update_graph_image(self):
        print('Updating Graph')
        
        try:
            self.clear_plot()
            print('Plot cleared')
        except Exception as e:
            print(f'Could not clear plot - Error {e}')
        
        try:
            self.plot_graph()

        except Exception as e:
            print(f'Could not update graph - Error {e}')
        self.after(int(UPDATE_FREQUENCY_GRAPH*1000), self.update_graph_image)
    
    def plot_graph(self):
        
        try:
            df_plt = self.controller.rc.get_graph_data()
            print(df_plt.head())
        except Exception as e:
            print(f'Could not fetch data for Graph - Error: {e}')

        try:
            plt.style.use('dark_background')
            plot_bg_color = '#2d3436'

            #fig, ax = plt.subplots(figsize=(3,2))
            self.figure.patch.set_facecolor(plot_bg_color)
            self.axes.set_facecolor(plot_bg_color)
            self.axes.axes.xaxis.set_ticklabels([])
            self.axes.axes.xaxis.set_ticks([])
            self.axes.tick_params(axis='y', labelsize= 6)
            self.axes.spines['right'].set_visible(False)
            self.axes.spines['top'].set_visible(False)
            self.axes.spines['left'].set_visible(False)
            self.axes.spines['bottom'].set_visible(False)    
            
            self.axes.plot(df_plt.Time, df_plt.today, linewidth=3, color='#fbc531', label='today')
            self.axes.plot(df_plt.Time, df_plt.yesterday, linewidth=1, color='#636e72', label='yesterday')
        except Exception as e:
            print(f'Could not plot axes. Error {e}')


        #x = [1,3,5,6,8]
        #y = [2,4,2,6,3]
        #self.axes.plot(x,y)
        #self.axes.plot(x*2, y*2)
        self.graphCanv.draw()
    
    def clear_plot(self):
        
        self.axes.cla()
        self.graphCanv.draw()

    def update_status_label(self):
        self.status = f'{self.controller.rc.status} ({self.controller.rc.statuscode})'
        self.statusLbl.configure(text=self.status, fg='orange red')
        if self.controller.rc.statuscode == 7:
            self.statusLbl.configure(fg = 'SpringGreen3')
        self.after(int(UPDATE_FREQUENCY*1000), self.update_status_label)





    def update_date_time_labels(self):
        self.timestr = self.controller.rc.get_time_string()
        self.datestr = self.controller.rc.get_date_string()
        self.timeLbl.configure(text=self.timestr)
        self.dateLbl.configure(text=self.datestr)
        self.after(1000, self.update_date_time_labels)
        
    def frame_update(self):
        # store previous data temporarily if something goes wrong
        old_data = (self.energy_current, self.energy_today, self.CO2) 
        #
        try:
            self.energy_current, self.energy_today, self.CO2 = self.controller.rc.collect_frame_update_data()

        except Exception as e:
            print(e)
            self.energy_current, self.energy_today, self.CO2 = old_data

        self.energyLbl.configure(text=f'{self.energy_current} W')        
        self.dayenergyLbl.configure(text=f'{self.energy_today:.2f} kWh')
        self.co2Lbl.configure(text=f'{self.CO2:.1f} kg CO2')
        
        self.after(int(UPDATE_FREQUENCY*1000), self.frame_update)


class DetailPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=FRAME_COLOR)
        self.after(int(UPDATE_FREQUENCY*1000), self.update_status_label)
        self.after(int(UPDATE_FREQUENCY_GRAPH*1000), self.update_record_frame)
        self.after(int(UPDATE_FREQUENCY_GRAPH*1000), self.update_detail_frame)

        self.status = ''
        self.controller = controller


        # Values for this page
        self.max_energy_today = 0
        self.max_energy_this_year = 0
        self.max_energy_total = 0

        self.energy_today = 0
        self.energy_this_year = 0
        self.energy_total = 0 
        self.co2_today = 0 
        self.co2_this_year = 0 
        self.co2_total = 0 
        self.cash_today = 0 
        self.cash_this_year = 0 
        self.cash_total = 0

        
        # setting weights within  page
        self.columnconfigure(0, weight = 1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight = 0)
        self.rowconfigure(1, weight = 1)
        self.rowconfigure(2, weight = 0)
        self.rowconfigure(3, weight = 0)
        self.rowconfigure(4, weight = 0)
        self.rowconfigure(5, weight = 0)

        
        self.headerframe = tk.Frame(self, bg=BACK_GROUND_COLOR)
        self.headerframe.grid(row = 0, column=0, columnspan=2, sticky='nswe', padx=PADX, pady=PADY)
        self.headerframe.rowconfigure(0, weight=0)
        self.headerframe.columnconfigure(1, weight=1)
        self.headerframe.columnconfigure(2, weight=1)

        logo_path = os.path.join('resources/solar-energy_gui.png')
        load = Image.open(logo_path)
        render=ImageTk.PhotoImage(load)
        self.img = tk.Label(self.headerframe, image=render, bg=BACK_GROUND_COLOR)
        self.img.image = render
        self.img.grid(row=0, column=0, sticky='nswe', padx=20, pady=5)
        self.label = tk.Label(self.headerframe, text = "PV Tracker", font = SMALL_FONT, bg=BACK_GROUND_COLOR, fg=HEADER_FONT_COLOR)
        self.label.grid(row = 0, column=1, padx = 0, pady = 0, sticky='nswe')
        self.label = tk.Label(self.headerframe, text = "v10", font = SMALL_FONT, bg=BACK_GROUND_COLOR, fg=HEADER_FONT_COLOR)
        self.label.grid(row = 0, column=2, padx = 10, pady = 0, sticky='nse')


        self.detailframe = tk.Frame(self, bg=BACK_GROUND_COLOR)
        self.detailframe.grid(row=1, column=0, columnspan=2, padx=PADX, pady=PADY, sticky='nswe')

        self.detailframe.columnconfigure(0, weight=1)
        self.detailframe.columnconfigure(1, weight=1)
        self.detailframe.columnconfigure(2, weight=1)
        self.detailframe.columnconfigure(3, weight=1)
        self.detailframe.rowconfigure(0, weight=1)
        self.detailframe.rowconfigure(1, weight=1)
        self.detailframe.rowconfigure(2, weight=1)
        self.detailframe.rowconfigure(3, weight=1)
        self.detailframe.rowconfigure(4, weight=1)
        self.detailframe.rowconfigure(5, weight=1)
        
        self.headerLbl = tk.Label(self.detailframe, text='Overview', font=LARGE_FONT, bg=BACK_GROUND_COLOR, fg=ENERGY_FONT_COLOR)
        self.headerLbl.grid(row=0, column=0, columnspan=4, sticky='nswe')
        self.subheaderLbl0 = tk.Label(self.detailframe, text='', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.subheaderLbl0.grid(row=1, column=0, sticky='nswe')
        self.subheaderLbl1 = tk.Label(self.detailframe, text='kWh', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.subheaderLbl1.grid(row=1, column=1, sticky='nswe')
        self.subheaderLbl2 = tk.Label(self.detailframe, text='CO2 kg', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.subheaderLbl2.grid(row=1, column=2, sticky='nswe')
        self.subheaderLbl3 = tk.Label(self.detailframe, text='EUR', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.subheaderLbl3.grid(row=1, column=3, sticky='nswe')
        

        self.rowLbl1 = tk.Label(self.detailframe, text='Today', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.rowLbl1.grid(row=2, column=0, sticky='nse')
        self.rowLbl2 = tk.Label(self.detailframe, text='This Year', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.rowLbl2.grid(row=3, column=0, sticky='nse')
        self.rowLbl3 = tk.Label(self.detailframe, text='Total', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.rowLbl3.grid(row=4, column=0, sticky='nse')
        
        # Production for detailframe
        self.energyLbl1 = tk.Label(self.detailframe, text='0', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.energyLbl1.grid(row=2, column=1, sticky='nswe')
        self.energyLbl2 = tk.Label(self.detailframe, text='0', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.energyLbl2.grid(row=3, column=1, sticky='nswe')
        self.energyLbl3 = tk.Label(self.detailframe, text='0', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.energyLbl3.grid(row=4, column=1, sticky='nswe')
        
        # Co2 for detailframe
        self.CO2Lbl1 = tk.Label(self.detailframe, text='0', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.CO2Lbl1.grid(row=2, column=2, sticky='nswe')
        self.CO2Lbl2 = tk.Label(self.detailframe, text='0', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.CO2Lbl2.grid(row=3, column=2, sticky='nswe')
        self.CO2Lbl3 = tk.Label(self.detailframe, text='0', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.CO2Lbl3.grid(row=4, column=2, sticky='nswe')
       
        # EUR for detailframe
        self.EURLbl1 = tk.Label(self.detailframe, text='0', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.EURLbl1.grid(row=2, column=3, sticky='nswe')
        self.EURLbl2 = tk.Label(self.detailframe, text='0', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.EURLbl2.grid(row=3, column=3, sticky='nswe')
        self.EURLbl3 = tk.Label(self.detailframe, text='0', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.EURLbl3.grid(row=4, column=3, sticky='nswe')
       
        self.recordframe = tk.Frame(self, bg='red')
        self.recordframe.grid(row=2, column=0, columnspan=2, padx=PADX, pady=PADY, sticky='nswe')

        self.recordframe.rowconfigure(0, weight=1)
        self.recordframe.rowconfigure(1, weight=1)
        self.recordframe.columnconfigure(0, weight=1)    
        self.recordframe.columnconfigure(1, weight=1)    
        self.recordframe.columnconfigure(2, weight=1)    

        # Record Frame
        self.recordLbl = tk.Label(self.recordframe, text='Highest Production', font=LARGE_FONT, bg=BACK_GROUND_COLOR, fg=ENERGY_FONT_COLOR)
        self.recordLbl.grid(row=0, column=0, columnspan=3, sticky='nswe')

        # Data for Record Frame
        self.recLbl1 = tk.Label(self.recordframe, text='Today', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.recLbl1.grid(row=1, column=0, sticky='nswe')
        self.recLbl2 = tk.Label(self.recordframe, text='This Year', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.recLbl2.grid(row=1, column=1, sticky='nswe')
        self.recLbl3 = tk.Label(self.recordframe, text='Total', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.recLbl3.grid(row=1, column=2, sticky='nswe')

        self.rectoday = tk.Label(self.recordframe, text='0', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.rectoday.grid(row=2, column=0, sticky='nswe')
        self.recyear = tk.Label(self.recordframe, text='0', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.recyear.grid(row=2, column=1, sticky='nswe')
        self.rectotal = tk.Label(self.recordframe, text='0', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.rectotal.grid(row=2, column=2, sticky='nswe')



        
        # frame showing status and navigation buttons
        self.statusframe = tk.Frame(self, padx=PADX, pady=PADY, bg=BACK_GROUND_COLOR)
        self.statusframe.grid(row=3, column=0, columnspan=2, sticky='nswe')

        self.statusframe.rowconfigure(0,weight=1)
        self.statusframe.columnconfigure(0,weight=1)
        self.statusframe.columnconfigure(1,weight=1)
        self.statusframe.columnconfigure(2,weight=1)
        self.statusframe.columnconfigure(3,weight=1)

        self.gomainbutton = tk.Button(self.statusframe, text = "Main Page", command = lambda: controller.show_frame(MainPage), 
        bg=BUTTON_BG, fg=BUTTON_FONT_COLOR, font=SMALL_FONT)
        self.gomainbutton.grid(row=0, column = 0, sticky = 'nswe')

        self.gosettingsBtn = tk.Button(self.statusframe, text = "EXIT", command = lambda: controller.on_closing(), 
        bg=BUTTON_BG, fg=BUTTON_FONT_COLOR, font=SMALL_FONT)
        self.gosettingsBtn.grid(row=0, column=3, sticky = 'nswe')

        #label color should change with respective status - connected = red, searching = red
        self.statusLbl = tk.Label(self.statusframe, text=self.status, font=SMALL_FONT, bg=BACK_GROUND_COLOR)
        self.statusLbl.grid(row=0, column=1, columnspan=2, sticky='nswe')


    def update_detail_frame(self):
        # self.cum_data = (energy_today, energy_this_year, energy_total, co2_today, co2_this_year, co2_total, cash_today, cash_this_year, cash_total )
               

        # store previous data temporarily if something goes wrong
        old_data = (self.energy_today, self.energy_this_year, self.energy_total, self.co2_today, self.co2_this_year, self.co2_total, self.cash_today, self.cash_this_year, self.cash_total) 
        #
        try:
            self.energy_today, self.energy_this_year, self.energy_total, self.co2_today, self.co2_this_year, self.co2_total, self.cash_today, self.cash_this_year, self.cash_total = self.controller.rc.collect_cum_data()

        except Exception as e:
            print(e)
            self.energy_today, self.energy_this_year, self.energy_total, self.co2_today, self.co2_this_year, self.co2_total, self.cash_today, self.cash_this_year, self.cash_total = old_data
        

        self.energyLbl1.configure(text=f'{self.energy_today/1000:.1f} kWh')
        self.energyLbl2.configure(text=f'{int(self.energy_this_year/1000)} kWh')
        self.energyLbl3.configure(text=f'{int(self.energy_total/1000)} kWh')
        self.CO2Lbl1.configure(text=f'{self.co2_today/1000:.1f} kg CO2')
        self.CO2Lbl2.configure(text=f'{int(self.co2_this_year/1000)} kg CO2')
        self.CO2Lbl3.configure(text=f'{int(self.co2_total/1000)} kg CO2')
        self.EURLbl1.configure(text=f'{self.cash_today:.2f} EUR')
        self.EURLbl2.configure(text=f'{int(self.cash_this_year)} EUR')
        self.EURLbl3.configure(text=f'{int(self.cash_total)} EUR')


        self.after(int(UPDATE_FREQUENCY_GRAPH*1000), self.update_detail_frame)

   
    def update_record_frame(self):
        
        # store previous data temporarily if something goes wrong
        old_data = (self.max_energy_today, self.max_energy_this_year, self.max_energy_total) 
        #
        try:
            self.max_energy_today, self.max_energy_this_year, self.max_energy_total = self.controller.rc.collect_max_data()

        except Exception as e:
            print(e)
            self.max_energy_today, self.max_energy_this_year, self.max_energy_total = old_data
        
        self.rectoday.configure(text = f'{self.max_energy_today} W')
        self.recyear.configure(text = f'{self.max_energy_this_year} W')
        self.rectotal.configure(text = f'{self.max_energy_total} W')
        self.after(int(UPDATE_FREQUENCY_GRAPH*1000), self.update_record_frame)




    def update_status_label(self):
        self.status = f'{self.controller.rc.status} ({self.controller.rc.statuscode})'
        self.statusLbl.configure(text=self.status, fg='orange red')
        if self.controller.rc.statuscode == 7:
            self.statusLbl.configure(fg = 'SpringGreen3')
        self.after(int(UPDATE_FREQUENCY*1000), self.update_status_label)




class Settings(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=FRAME_COLOR)
        self.after(int(UPDATE_FREQUENCY*1000), self.update_status_label)
        self.after(int(UPDATE_FREQUENCY_GRAPH*1000), self.detail_frame_update)
        
        
        self.status = ''
        self.controller = controller
        
        # values of this page
        self.url = "NA"
        self.device_ID = 0
        self.co2factor = 0
        self.cashfactor = 0
        self.hwverion = "NA" 
        self.productid = "NA" 
        self.swversion = "NA" 
        self.uniqueid = "NA"



        # setting weights within  page
        self.columnconfigure(0, weight = 1)
        self.columnconfigure(1, weight=0)
        self.rowconfigure(0, weight = 0)
        self.rowconfigure(1, weight = 1)
        self.rowconfigure(2, weight = 0)
        self.rowconfigure(3, weight = 0)
        self.rowconfigure(4, weight = 0)
        self.rowconfigure(5, weight = 0)

        
        self.headerframe = tk.Frame(self, bg=BACK_GROUND_COLOR)
        self.headerframe.grid(row = 0, column=0, columnspan=2, sticky='nswe', padx=PADX, pady=PADY)
        self.headerframe.rowconfigure(0, weight=0)
        self.headerframe.columnconfigure(1, weight=1)
        self.headerframe.columnconfigure(2, weight=1)

        logo_path = os.path.join('resources/solar-energy_gui.png')
        load = Image.open(logo_path)
        render=ImageTk.PhotoImage(load)
        self.img = tk.Label(self.headerframe, image=render, bg=BACK_GROUND_COLOR)
        self.img.image = render
        self.img.grid(row=0, column=0, sticky='nswe', padx=20, pady=5)
        self.label = tk.Label(self.headerframe, text = "PV Tracker", font = SMALL_FONT, bg=BACK_GROUND_COLOR, fg=HEADER_FONT_COLOR)
        self.label.grid(row = 0, column=1, padx = 0, pady = 0, sticky='nswe')
        self.label = tk.Label(self.headerframe, text = "v10", font = SMALL_FONT, bg=BACK_GROUND_COLOR, fg=HEADER_FONT_COLOR)
        self.label.grid(row = 0, column=2, padx = 10, pady = 0, sticky='nse')


        # Detail Frame showing the Settings Data
        self.detailframe = tk.Frame(self, bg=BACK_GROUND_COLOR)
        self.detailframe.grid(row=1, column=0, columnspan=2, padx=PADX, pady=PADY, sticky='nswe')

        self.detailframe.columnconfigure(0, weight=1)
        self.detailframe.columnconfigure(1, weight=3)
        self.detailframe.rowconfigure(0, weight=1)
        self.detailframe.rowconfigure(1, weight=1)
        self.detailframe.rowconfigure(2, weight=1)
        self.detailframe.rowconfigure(3, weight=1)
        self.detailframe.rowconfigure(4, weight=1)
        self.detailframe.rowconfigure(5, weight=1)
        self.detailframe.rowconfigure(6, weight=1)
        self.detailframe.rowconfigure(7, weight=1)
        






        #co2factor, cashfactor, hwverion, productid, swversion, uniqueid
        self.lbl0 = tk.Label(self.detailframe, text='Settings', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=ENERGY_FONT_COLOR)
        self.lbl0.grid(row=0, column=0, columnspan=2, sticky='nswe')
        self.lbl1 = tk.Label(self.detailframe, text='URL', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.lbl1.grid(row=1, column=0, sticky='nse')
        self.lbl2 = tk.Label(self.detailframe, text='Device ID', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.lbl2.grid(row=2, column=0, sticky='nse')
        self.lbl3 = tk.Label(self.detailframe, text='HW Version', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.lbl3.grid(row=3, column=0, sticky='nse')
        self.lbl4 = tk.Label(self.detailframe, text='Product ID', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.lbl4.grid(row=4, column=0, sticky='nse')
        self.lbl5 = tk.Label(self.detailframe, text='SW Version', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.lbl5.grid(row=5, column=0, sticky='nse')
        self.lbl6 = tk.Label(self.detailframe, text='Unique ID', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.lbl6.grid(row=6, column=0, sticky='nse')
        self.lbl7 = tk.Label(self.detailframe, text='CO2 factor', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.lbl7.grid(row=7, column=0, sticky='nse')
        self.lbl8 = tk.Label(self.detailframe, text='Cash factor', font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.lbl8.grid(row=8, column=0, sticky='nse')



        self.datalbl1 = tk.Label(self.detailframe, text="NA", font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.datalbl1.grid(row=1, column=1, sticky='nswe')
        self.datalbl2 = tk.Label(self.detailframe, text="NA", font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.datalbl2.grid(row=2, column=1, sticky='nswe')
        self.datalbl3 = tk.Label(self.detailframe, text="NA", font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.datalbl3.grid(row=3, column=1, sticky='nswe')
        self.datalbl4 = tk.Label(self.detailframe, text="NA", font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.datalbl4.grid(row=4, column=1, sticky='nswe')
        self.datalbl5 = tk.Label(self.detailframe, text="NA", font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.datalbl5.grid(row=5, column=1, sticky='nswe')
        self.datalbl6 = tk.Label(self.detailframe, text="NA", font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.datalbl6.grid(row=6, column=1, sticky='nswe')
        self.datalbl7 = tk.Label(self.detailframe, text="NA", font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.datalbl7.grid(row=7, column=1, sticky='nswe')
        self.datalbl8 = tk.Label(self.detailframe, text="NA", font=SMALL_FONT, bg=BACK_GROUND_COLOR, fg=FONT_COLOR)
        self.datalbl8.grid(row=8, column=1, sticky='nswe')
        



        # frame showing status and navigation buttons
        self.statusframe = tk.Frame(self, padx=PADX, pady=PADY, bg=BACK_GROUND_COLOR)
        self.statusframe.grid(row=5, column=0, columnspan=2, sticky='nswe')

        self.statusframe.rowconfigure(0,weight=1)
        self.statusframe.columnconfigure(0,weight=1)
        self.statusframe.columnconfigure(1,weight=1)
        self.statusframe.columnconfigure(2,weight=1)
        self.statusframe.columnconfigure(3,weight=1)

        self.gomainbutton = tk.Button(self.statusframe, text = "Main Page", command = lambda: controller.show_frame(MainPage), 
        bg=BUTTON_BG, fg=BUTTON_FONT_COLOR, font=SMALL_FONT)
        self.gomainbutton.grid(row=0, column = 0, sticky = 'nswe')

        self.exitButton = tk.Button(self.statusframe, text = "EXIT", command = lambda: controller.on_closing(), 
        bg=BUTTON_BG, fg=BUTTON_FONT_COLOR, font=SMALL_FONT)
        self.exitButton.grid(row=0, column=3, sticky = 'nswe')

        #label color should change with respective status - connected = red, searching = red
        self.statusLbl = tk.Label(self.statusframe, text=self.status, font=SMALL_FONT, bg=BACK_GROUND_COLOR)
        self.statusLbl.grid(row=0, column=1, columnspan=2, sticky='nswe')

    def update_status_label(self):
        self.status = f'{self.controller.rc.status} ({self.controller.rc.statuscode})'
        self.statusLbl.configure(text=self.status, fg='orange red')
        if self.controller.rc.statuscode == 7:
            self.statusLbl.configure(fg = 'SpringGreen3')
        self.after(int(UPDATE_FREQUENCY*1000), self.update_status_label)

    
    def detail_frame_update(self):
        
        # store previous data temporarily if something goes wrong
        old_data = (self.url,self.device_ID,self.co2factor,self.cashfactor,self.hwverion, self.productid, self.swversion, self.uniqueid)
        
        try:
            self.url,self.device_ID,self.co2factor,self.cashfactor,self.hwverion, self.productid, self.swversion, self.uniqueid = self.controller.rc.collect_logger_info()
        
        except Exception as e:
            print(e)
            self.url,self.device_ID,self.co2factor,self.cashfactor,self.hwverion, self.productid, self.swversion, self.uniqueid = old_data
        
            

        self.datalbl1.configure(text=self.url)
        self.datalbl2.configure(text=str(self.device_ID))
        self.datalbl3.configure(text=self.hwverion)
        self.datalbl4.configure(text=self.productid)
        self.datalbl5.configure(text=self.swversion)
        self.datalbl6.configure(text=self.uniqueid)
        self.datalbl7.configure(text=f'{int(self.co2factor*1000)} g / kWh ')
        self.datalbl8.configure(text=f'{self.cashfactor:.3f} EUR / kWh ')
        
        self.after(int(UPDATE_FREQUENCY_GRAPH*1000), self.detail_frame_update)


if __name__ == "__main__":
    app = Main()
    app.geometry("480x320")
    #app.geometry("1024x780")
    
    app.title('PV Tracker')
    app.protocol("WM_DELETE_WINDOW", app.on_closing)

    

    app.rc.startup() # starting requestcontroller
    #ani = FuncAnimation(f, animate, interval=10000)
    URL = app.rc.fs.get_url()
    DEVICE_ID = app.rc.fs.get_device_id()
    print(f'Global URL set to {URL}')
    print(f'Global DEVICE_ID set to {DEVICE_ID}')
    
    app.mainloop()
    '''except ProgramKilled:
        print ("Program killed: running cleanup code")
        for j in self.controller.rc.joblist:
            j.stop()

    


    RequestController.get_time_string()
    RequestController.get_date_string()
    '''