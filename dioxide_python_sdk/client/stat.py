import time
from ..client import clientlogger

class StatTool:
    begin = time.time()
    end  = 0
    timeused = 0
    unit = "ms"

    @staticmethod
    def begin(unit="ms"):
        stat =  StatTool()
        stat.begin =time.time()
        stat.unit = unit
        return stat

    def done(self):
        self.end = time.time()
        self.timeused = self.end - self.begin

    def make_statmsg(self,msg):
        if self.end ==0 :
            self.done()
        timeused_toshow  = self.timeused

        if self.unit=="ms":
            timeused_toshow = timeused_toshow *1000

        statmsg  = "%.3f%s,%s"% (timeused_toshow,self.unit,msg)
        return statmsg

    def debug(self,msg):
        clientlogger.stat_logger.debug(self.make_statmsg(msg))

    def info(self,msg):
        clientlogger.stat_logger.info(self.make_statmsg(msg))

    def error(self,msg):
        clientlogger.stat_logger.error(self.make_statmsg(msg))