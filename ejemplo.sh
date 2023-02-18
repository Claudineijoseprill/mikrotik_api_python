#!/usr/bin/python3

from api_mk import ApiRos 

#                 IP           User    password     port    (True or False SSL= Default false)
#ser = MK_API(ip, username, password, port=8728, ssl=False)

ser = ApiRos("192.168.88.1", "admin", "")
if not ser.loged:
    sys.exit(0)


ser.command = '/interface/wireless/registration-table/getall'
ser.send()
if ser.error == '':
    print('OK', len(ser.datos), ser.status)

    for i in range(len(ser.datos)):
        if not 'mac-address' in ser.datos[i].keys():
            print(ser.datos[i])
        else: print(ser.datos[i]['radio-name'])
        
else: print('ERROR', ser.error)
