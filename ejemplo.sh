#!/usr/bin/python3

from api_mk import ApiRos 

ser = ApiRos("10.0.5.67", "play", "poi")
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
