# rasppi-caldera
Dedicated software to control a custom pellet heating system, using a Raspberry Pi and a relay board.

NOTE: Some of the logs and diagrams are written in Spanish, as this project has been accomplished in collaboration with my father, who does not speak English. My apologies for that.

## Installation
Install dependencies:

```
pip install -r requirements.txt
```

## Execution
To run the Heating Cycle:

```
python caldera.py
```

### In case of errors while importing RPIO
On some circumstances, while attempting to run the heating cycle, the following error may pop up:
```
SystemError: This module can only be run on a Raspberry Pi
```

This may be caused because newer versions of RPIO are not compatible with old versions of Raspberry Pi 2 B

To overcome this, simply proceed as follows:
```
git clone https://github.com/metachris/RPIO.git --branch v2 --single-branch
cd RPIO
sudo python setup.py install
```
