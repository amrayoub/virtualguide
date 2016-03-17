### Virtual Guide

Virtual Guide is a project to be used for any exhibition around the world. The central idea is to be the unique application for every exhibition, from small as a garage sale or large as Museums.
This is a complete project, from mobile application to administration web interface.
Yes, it's an application guide with batteries included!

### What do you will need
- A REST server: included with name “virtrest.py”;
- The Administration interface: included with name “adminvirt.py”
- A MongoDB database: collections included;
- Python dependencies:
 - Python 2.7
 - M2Crypto
 - Flask
 - PyMongo
 - ColorThief
 - PyQRCode

First, you need to provide an Wi-Fi connection to your costumers. Put some hotspots around the area to avoid “black holes” (points without or with weak signal).
These hotspots need to be connected in the same network as your Rest Server (virtrest.py).

To protect your database from attacks, it's a good idea to put your database behind a firewall, into another separate network and allow connections from your rest server only.

Configure your “adminvirt.py” server to access your database. Now, it's possible to upload objects to your exhibition through the web admin interface.

### How it Works
It's really very simple. Look at above picture:

![How it Works](https://raw.githubusercontent.com/allangood/virtualguide/master/site_media/virtualguide_en.jpg "How it Works")

First, your costumers install the app from Google Play Store.
Then, your costumers need to connect to your Wi-Fi network.
After, open the application and do the CheckIn with the QR Code provided by you (print the QR Code from Web Interface and paste somewhere).
Now, when your costumers look to a object and scan the QRCode, a text, audio and/or video will be presented to him!
