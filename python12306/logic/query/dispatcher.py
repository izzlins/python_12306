import datetime
import random
import time

from config import Config
from utils.log import Log
from .query import Query


def format_time(time_string):
    now = datetime.datetime.now()
    k = datetime.datetime.strptime(time_string, "%H:%M")
    return datetime.datetime(year=now.year,
                             month=now.month,
                             day=now.day,
                             hour=k.hour,
                             minute=k.minute
                             )


class Dispatcher(object):

    def __init__(self):
        self.pre_sale_flag = False
        self.pre_sale_end = False

    @property
    def query_left_ticket_time(self):
        if self.pre_sale_flag and Config.presale_enable:
            try:
                delta = Config.presale_config.query_left_ticket_time + random.random()
            except AttributeError:
                delta = 1 + random.random()
        else:
            try:
                delta = Config.basic_config.query_left_ticket_time - 1 + random.random()
            except AttributeError:
                delta = 4 + random.random()
        return delta

    @property
    def delta_stop_time(self):
        return datetime.timedelta(minutes=Config.presale_config.stop_time)

    @property
    def delta_continue_time(self):
        return datetime.timedelta(minutes=Config.presale_config.continue_time)

    def check_current_mode(self):
        if (not Config.presale_enable) or self.pre_sale_end:
            return False
        else:
            now = datetime.datetime.now()
            open_times = list(map(format_time, Config.presale_config.start_times))
            f = lambda x: x - now <= self.delta_stop_time and now - x <= self.delta_continue_time
            result = any(filter(f, open_times))
            if result:
                Log.v("当前处于预售模式，不再处理正常模式下的日期查询")
                return True
            check_result = list(filter(lambda x: now > x + self.delta_continue_time, open_times))
            if check_result and all(check_result):
                self.pre_sale_end = True
                return False
        return False

    @property
    def query_travel_dates(self):
        self.pre_sale_flag = self.check_current_mode()
        if self.pre_sale_flag:
            return [Config.presale_config.travel_date]
        else:
            if self.pre_sale_end:
                if Config.presale_enable and Config.presale_config.travel_date not in Config.basic_config.travel_dates:
                    return Config.basic_config.travel_dates + [Config.presale_config.travel_date]
                else:
                    return Config.basic_config.travel_dates
            else:
                open_times = list(map(format_time, Config.presale_config.start_times))
                if datetime.datetime.now() > min(open_times) + self.delta_continue_time:
                    if Config.presale_enable and Config.presale_config.travel_date not in Config.basic_config.travel_dates:
                        return Config.basic_config.travel_dates + [Config.presale_config.travel_date]
                    else:
                        return Config.basic_config.travel_dates
                else:
                    return Config.basic_config.travel_dates

    def run(self, travel_date):
        Log.v("当前查询日期为 {}".format(travel_date))
        q = Query(travel_date)
        data = q.filter()
        if not data:
            Log.v("日期 {0} 满足条件的车次暂无余票, 正在重新查询".format(travel_date))

        for v in data:
            print("\t\t\t当前座位席别 {}".format(v[0].name))
            q.pretty_output(v[1])
        return data

    def output_delta_time(self, query_time):
        delta_time = datetime.datetime.now() - query_time
        delta = self.query_left_ticket_time
        time.sleep(delta)
        Log.v("当次查询时间间隔为 {0:.3} 秒, 查询请求处理时间 {1:.3} 秒".format(
            delta, delta_time.total_seconds()))


DispatcherTool = Dispatcher()

