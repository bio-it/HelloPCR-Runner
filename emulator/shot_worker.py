import time
import threading
RFU_TABLE = [
2,3,3,4,5,6,8,9,11,13,
16,20,24,28,34,41,49,59,71,85,
101,121,144,172,205,243,289,341,403,474,
556,649,754,872,1003,1146,1301,1466,1639,1818,
2000,2181,2360,2533,2698,2853,2996,3127,3245,3350,
3443,3525,3596,3658,3710,3756,3794,3827,3855,3878,
3898,3914,3928,3940,3950,3958,3965,3971,3975,3979,
3983,3986,3988,3990,3991,3993,3994,3995,3996,3996,
]

class ShotEmulator(threading.Thread):
    def __init__(self) -> None:
        threading.Thread.__init__(self) 
        self.daemon = True
        
        self.running = threading.Event()
        self.running.clear()

        self.shot_counter = 0
        self.filter_index = 0
        self.current_cycle = 0
        self.intensity = -1

    def reset(self):
        self.running.clear()
        self.current_cycle = 0
        self.shot_counter = 0
        self.intensity = -1

    def shot(self, filter_index:int, current_cycle:int, experiment_date:str):
        self.reset()
        self.running.set()
        self.filter_index = filter_index
        self.current_cycle = current_cycle

    def get_intensity(self):
        # return { 'cycle':self.current_cycle, 'fluor':self.filter_index, 'intensity':self.intensity}
        return self.intensity
    
    def get_RFU_value(self):
        col = 0
        if self.filter_index == 0:      # FAM
            col = 3     # Blue
        elif self.filter_index == 1:    # HEX
            col = 0     # WildGreen
        elif self.filter_index == 2:    # ROX
            col = 2     # Green 
        elif self.filter_index == 3:    # CY5
            col = 1     # Red
        idx = (int)((1. + col * 0.33) * self.current_cycle)
        return RFU_TABLE[idx] if idx < 80 else RFU_TABLE[-1]
    
    def run(self) -> None:
        round_timer = time.perf_counter()

        while True:
            self.running.wait()
            
            if not time.perf_counter() - round_timer > 1:
                continue
            
            self.shot_counter += 1 
            if self.shot_counter >= 1:
                self.intensity = self.get_RFU_value()
                self.running = False
            round_timer = time.perf_counter() 


    def close(self):
        return