# the compare the time,if the maret close we return the closed message
if datalist[31] is not None:
    time = datetime.datetime.strptime(datalist[31], '%H:%M:%S').time()
if time < datetime.datetime.strptime('09:29:59', '%H:%M:%S').time() \
        or (time > datetime.datetime.strptime('11:31:00', '%H:%M:%S').time() \
                    and time < datetime.datetime.strptime('12:59:59', '%H:%M:%S').time()) \
        or time > datetime.datetime.strptime('15:01:00', '%H:%M:%S').time():
    print('true')

print(time)