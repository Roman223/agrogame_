import datetime
# Яровая пшеница (Старая)
YP_rule = {0: [4, 25, 30],
           1: [5, 5, 8],
           2: [5, 8, 13],
           3: [5, 14, 20],
           4: [8, 16, 20],
           5: [8, 21, 23],
           6: [8, 24, 26],
           7: [8, 27, 29],
           8: [8, 30, 31],
           9: [8, None, None]
           }

YP_duration = {0: datetime.timedelta(days=2),
               1: datetime.timedelta(days=1),
               2: datetime.timedelta(days=2),
               3: datetime.timedelta(days=1),
               4: datetime.timedelta(days=1),
               5: datetime.timedelta(days=1),
               6: datetime.timedelta(days=1),
               7: datetime.timedelta(days=1),
               8: datetime.timedelta(days=1),
               9: datetime.timedelta(days=1)
               }