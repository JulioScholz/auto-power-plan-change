import GPUtil
from winrt.windows.ui.notifications import ToastNotificationManager, ToastNotification, ToastTemplateType
from threading import Thread
import time, sys, subprocess, argparse
import numpy as np


DEBUG = False
def toast_notification(AppID='1', title="TITULAO", text="TEXTAO"):
    XML = ToastNotificationManager.get_template_content(ToastTemplateType.TOAST_TEXT02)
    t = XML.get_elements_by_tag_name("text")
    t[0].append_child(XML.create_text_node(title))
    t[1].append_child(XML.create_text_node(text))
    notifier = ToastNotificationManager.create_toast_notifier(AppID)
    notifier.show(ToastNotification(XML))

#source: https://stackoverflow.com/a/70382780/9385889
def positive(numeric_type):
    def require_positive(value):
        number = numeric_type(value)
        if number <= 0:
            raise ArgumentTypeError(f"Number {value} must be positive.")
        return number

    return require_positive

class Monitor(Thread):
    def __init__(self, delay, size, threshold):
        super(Monitor, self).__init__()

        #mode 0 = Power saving profile
        #mode 1 = High performance profile
        self.mode = -1
        
        self.threshold = threshold  #The average gpu usage threshold
       
        self.delay = delay # Time between calls to GPUtil
        self.it = 0 #Iterations counter
        self.arr = np.array([]) #Array that stores the last gpu usage measuraments, used to calculate the gpu usage average
        self.size = size #The size of the array
        self.stopped = False
        #self.start()

    def stop(self):
        self.stopped = True

    def run(self):
        while not self.stopped:
            gpu1 = GPUtil.getGPUs()[0]

            if len(self.arr) == self.size:
                self.arr[(self.it%self.size)-1] = gpu1.load
            else:
                self.arr = np.append(self.arr,gpu1.load)
            
            #Get the gpu usage average
            avg = np.average(self.arr)

            #If average usage is high and mode 0 (Power Saving)
            if avg >= self.threshold and self.mode != 1:
                toast_notification("Gpu Utilization",f"Current GPU load {gpu1.load*100}%","Changed to High Performance")
                subprocess.call(["powercfg", "-s","9935e61f-1661-40c5-ae2f-8495027d5d5d"])
                subprocess.call(["powercfg", "-getactivescheme"])
                print("\n")
                self.mode = 1
            #If average usage is low and mode 1 (High Performance)
            elif avg <= self.threshold and self.mode != 0:
                toast_notification("Gpu Utilization",f"Current GPU load {gpu1.load*100}%","Changed to Power Saving")
                subprocess.call(["powercfg", "-s" ,"a1841308-3541-4fab-bc81-f71556f20b4a"])
                subprocess.call(["powercfg", "-getactivescheme"])
                print("\n")
                self.mode = 0

            print(avg)
            self.it += 1
            if DEBUG == True:
                if self.it%30 == 0:
                    print("\033c", end='')
                    print(subprocess.call(["powercfg", "-getactivescheme"]))   
            time.sleep(self.delay)

def main():
    global DEBUG
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-d','--delay', type=positive(int),metavar='', help='an integer for the delay in seconds between gpu usage verifications')
    parser.add_argument('-s','--size', type=positive(int),metavar='', help='an integer for the size of the array that stores the gpu usage in the last n interations')
    parser.add_argument('-t','--threshold', type=positive(int),metavar='', help='an integer for the gpu usage threshold, determines when the power profile will be changed')
    parser.add_argument('--debug', action='store_true', help='debug boolean, if true some debugging prints will be enable')
    args = parser.parse_args()

    delay = 2
    size = 50
    threshold = 15
    DEBUG = False

    if args.delay:
        delay = args.delay
    if args.size:
        size = args.size
    if args.threshold:
        threshold = args.threshold
    if args.debug:
        DEBUG = args.debug

    try:
        print(f"Starting gpu usage monitor:\n- delay set to {delay} seconds\n- array size {size}\n- threshold set to {threshold}%\n- debug = {DEBUG}\n")
        subprocess.call(["powercfg", "-getactivescheme"])
        print("\n")
        monitor = Monitor(delay,size,threshold/100)
        monitor.start()
    except (KeyboardInterrupt, SystemExit):
        print ('\n! Received keyboard interrupt, quitting threads.\n')
        monitor.stop()
        sys.exit()


if __name__ == '__main__':
    main()