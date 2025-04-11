Takes in humidity and temperature readings.

An LED traffic light system is used to indicate whether water needs to be sprayed to raise humidity for Apollo - my partner's Crested Gecko.
Once the target has been met, the humidity needs to fall until the next scheduled time. Humidity needs to be higher at night.

## Setup 

1. Create an env.py file.
2. Create a dict called 'variables'.
3. Add the following enviroment variables:

variables['SSID'] - Wifi ssid
variables['PASS'] - Wifi password

### Setup Over The Air updates

variables['OTA_HOST'] - HTTP/HTTPS file server url containing updates.
variables['OTA_PROJECT_NAME'] - The folder name that contains the updates.

1. Add a folder with the OTA_PROJECT_NAME. 
2. 
3. In the folder, create a file called 'version' that contains the current version (eg v1.0.0).

4. For each version, create a directory with the version as the name (eg v1.0.0). Add the env.py and main.py files.

## Make changes

1. Connect a USB-C cable to the ESP32 and find the COM using device manager.

2. Connect using rshell and the COM you just found. ```rshell -p [COM8]```

4. Copy all the files over to the ESP32 using ```cp [filename].py /pyboard/```

3. Update the main.py by simply copying it over again. ```cp main.py /pyboard/```

### Over The Air updates

1. Create a new folder with the next version number (eg v1.0.1).
   
2. Add the new env.py and main.py files.
   
3. Update the 'version' file to match.

### Test 

Connect using a serial connection on an SSH client such as PUTTY.

1. Close rshell otherwise connection will be refused.

2. Input the COM and the speed recommended for your device. (likely 115200).

3. Press reset CTRL+C.

4. Import main