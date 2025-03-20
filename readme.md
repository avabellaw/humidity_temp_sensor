Takes in humidity and temperature readings.

An LED traffic light system is used to indicate whether water needs to be sprayed to raise humidity for Apollo - my partner's Crested Gecko.
Once the target has been met, the humidity needs to fall until the next scheduled time. Humidity needs to be higher at night.

## Make changes

1. Connect a USB-C cable to the ESP32 and find the COM using device manager.

2. Connect using rshell and the COM you just found. ```rshell -p [COM8]```

4. Copy all the files over to the ESP32 using ```cp [filename].py /pyboard/```

3. Update the main.py by simply copying it over again. ```cp main.py /pyboard/```

### Test 

Connect using a serial connection on an SSH client such as PUTTY.

1. Close rshell otherwise connection will be refused.

2. Input the COM and the speed recommended for your device. (likely 115200).

3. Press reset CTRL+C.

4. Import main