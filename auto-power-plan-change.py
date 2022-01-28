import GPUtil
from threading import Thread
import time, sys, subprocess
import numpy as np
from winrt.windows.ui.notifications import ToastNotificationManager, ToastNotification, ToastTemplateType


DEBUG = True
def toast_notification(AppID='1', title="TITULAO", text="TEXTAO"):
    XML = ToastNotificationManager.get_template_content(ToastTemplateType.TOAST_TEXT02)
    t = XML.get_elements_by_tag_name("text")
    t[0].append_child(XML.create_text_node(title))
    t[1].append_child(XML.create_text_node(text))
    notifier = ToastNotificationManager.create_toast_notifier(AppID)
    notifier.show(ToastNotification(XML))


class Monitor(Thread):
    def __init__(self, delay, size, threshold):
        super(Monitor, self).__init__()
        self.mode = 0
        self.threshold = threshold
        self.stopped = False
        self.delay = delay # Time between calls to GPUtil
        self.it = 0
        self.arr = np.array([])
        self.sz = size
        self.start()

    def stop(self):
        self.stopped = True

    def run(self):
        while not self.stopped:
            GPUs = GPUtil.getGPUs()
            gpu1 = GPUs[0]

            if len(self.arr) == self.sz:
                self.arr[(self.it%self.sz)-1] = gpu1.load
            else:
                self.arr = np.append(self.arr,gpu1.load)

            #print(self.arr)
            avg = np.average(self.arr)
            if avg >= self.threshold and self.mode == 0:
                toast_notification("Gpu Utilization",f"Current GPU load {gpu1.load*100}%","Plano de energia alto desempenho")
                subprocess.call(["powercfg", "-s","9935e61f-1661-40c5-ae2f-8495027d5d5d"])
                subprocess.call(["powercfg", "-getactivescheme"])
                self.mode = 1
            elif avg <= self.threshold and self.mode == 1:
                toast_notification("Gpu Utilization",f"Current GPU load {gpu1.load*100}%","Plano de energia modo economia")
                subprocess.call(["powercfg", "-s" ,"a1841308-3541-4fab-bc81-f71556f20b4a"])
                subprocess.call(["powercfg", "-getactivescheme"])
                self.mode = 0
            #@subprocess.call('cls') 
            #print("\033c", end='')
            print(avg)
            self.it += 1
            if self.it%30 == 0:
                print("\033c", end='')
                print(subprocess.call(["powercfg", "-getactivescheme"]))   
            time.sleep(self.delay)
            sys


# Instantiate monitor with a 10-second delay between updates
print(subprocess.call(["powercfg", "-getactivescheme"]))
#print(subprocess.call(["powercfg", "-l"]))
#exit()
try:
    monitor = Monitor(2,100,0.15)

except (KeyboardInterrupt, SystemExit):
  print ('\n! Received keyboard interrupt, quitting threads.\n')
  sys.exit()
# Train, etc.

# Close monitor
#monitor.stop()