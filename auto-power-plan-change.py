import GPUtil
from winrt.windows.ui.notifications import ToastNotificationManager, ToastNotification, ToastTemplateType
from threading import Thread
import time, sys, subprocess, argparse
import numpy as np


DEBUG = False
#source: https://gist.github.com/MarcAlx/443358d5e7167864679ffa1b7d51cd06?permalink_comment_id=3573731#gistcomment-3573731
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
            raise argparse.ArgumentTypeError(f"Number {value} must be positive.")
        return number

    return require_positive

class Monitor(Thread):
    def __init__(self, delay, length, threshold):
        super(Monitor, self).__init__()
        #mode 0 = Power saving profile
        #mode 1 = High performance profile
        self.mode = -1
        self.threshold = threshold  #The average gpu usage threshold
        self.delay = delay # Time between calls to GPUtil
        self.it = 0 #Iterations counter
        self.arr  = np.zeros(length) #Array that stores the last gpu usage measuraments, used to calculate the gpu usage average
        self.length = length #The size of the array
        self.stopped = False

    def stop(self):
        self.stopped = True

    def run(self):
        while not self.stopped:
            self.it += 1
            #GPUtil.ge
            gpu1 = GPUtil.getGPUs()[0]
        
            self.arr[(self.it%self.length)] = gpu1.load

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
            
            if DEBUG == True:
                if self.it%30 == 0:
                    print("\033c", end='')
                    subprocess.call(["powercfg", "-getactivescheme"])   
            time.sleep(self.delay)

def main():
    global DEBUG
    parser = argparse.ArgumentParser(description='Process some integers.')
    #parser.add_argument('-s','--setup')
    parser.add_argument('-d','--delay', type=positive(int),metavar='', help='an integer for the delay in seconds between gpu usage verifications')
    parser.add_argument('-l','--length', type=positive(int),metavar='', help='an integer for the length of the array that stores the gpu usage in the last n interations')
    parser.add_argument('-t','--threshold', type=positive(int),metavar='', help='an integer for the gpu usage threshold, determines when the power profile will be changed')
    parser.add_argument('--debug', action='store_true', help='debug boolean, if true some debugging prints will be enable')
    args = parser.parse_args()

    #result = subprocess.getoutput(["powercfg","-l"])
    #print(result)
    
    delay = 1
    length = 2
    threshold = 15
    DEBUG = False
    #print(f'len: {args}')
    if args.delay:
        delay = args.delay
    if args.length:
        length = args.length
    if args.threshold:
        threshold = args.threshold
    if args.debug:
        DEBUG = args.debug

    try:
        print(f"Starting gpu usage monitor:\n- delay set to {delay} seconds\n- array length {length}\n- threshold set to {threshold}%\n- debug = {DEBUG}\n- current power profile: ")
        subprocess.call(["powercfg", "-getactivescheme"])
        print("\n")
        monitor = Monitor(delay,length,threshold/100)
        monitor.start()
    except (KeyboardInterrupt, SystemExit):
        print ('\n! Received keyboard interrupt, quitting threads.\n')
        monitor.stop()
        sys.exit()


if __name__ == '__main__':
    main()