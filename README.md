# Communauto CLI

Inspired by [/Alarty/communauto-search](https://github.com/Alarty/communauto-search). 

A CLI which simplifies interaction with Communauto website, currently supported commands are:

#### List reservations:

```bash
./communauto-cli.py list-reservations --status=upcoming
+----------+-----------------------+----------------------+----------------------+---------------------------+
|       id | Car                   | From                 | To                   | Station                   |
|----------+-----------------------+----------------------+----------------------+---------------------------|
| 26823428 | # 5021 Toyota Corolla | Fri 21/08/2020 13:00 | Fri 28/08/2020 14:00 | 058 - Cartier et Rosemont |
| 26835439 | # 4639 Toyota Corolla | Sun 09/08/2020 07:00 | Sun 09/08/2020 16:00 | 218 - Métro Jean-Talon    |
+----------+-----------------------+----------------------+----------------------+---------------------------+
```

#### Search for a car
The link at the bottom will redirect you to the page with available cars, so you'll just need to click on the preferred one to book it:

```bash
./communauto-cli.py search --start_date="10/08/20 07:00" --end_date="10/08/20 16:00" --city=sherbrooke --lang=fr
Date range: 10/8/2020 7:0 - 10/8/2020 16:0
+-------------------------------+------------+----------------+-----------------------------------------------------------+
| Station Name                  |   Distance | Car            | Features                                                  |
|-------------------------------+------------+----------------+-----------------------------------------------------------|
| 011 - Galt et du Saint-Esprit |        4.0 | Toyota Prius C | argent 5p/5pl PROMO  b.rabat. Hayon cd MP3 USB            |
| 019 - Webster                 |        6.8 | Chevrolet Volt | argent 4p/4pl PROMO  b.rabat. Berline cd MP3 rég. vitesse |
| 017 - Murray et Chalifoux     |        7.8 | Toyota Prius C | argent 5p/5pl b.rabat. Hayon cd MP3 USB s.bébé<18kg       |
+-------------------------------+------------+----------------+-----------------------------------------------------------+
Link: https://www.reservauto.net/Scripts/client/ReservationDisponibility.asp?IgnoreError=False&CityID=...
``` 

## How to use

You should have python3 installed, then clone/download the repo and run:

```bash
$ pip3 install -r requirements.txt
$ python3.8 ./communauto-cli.py --help
```

## Features

### Authentication

There are 3 ways to provide your credentials to the script:

 - safest - password prompt  
 Provide your username as an option, and for the password there will be a prompt:
  
    ```bash
     $ communauto-cli.py list-reservations --username=your@email.com
     Password:   
     ```

 - most convenient - set environment variables  
  Set environment variable in the current terminal session. You can add space before the `export`, to prevent command from saving in the history:
 
    ```bash
    $  export ca_user=your@email.com
    $  export ca_password=yourpass
    $ communauto-cli.py list-reservations
    ```
  
 - easiest - provide a password as an option  
  Don't do this, as it will be saved in the terminal history:
  
    ```bash
    $ communauto-cli.py list-reservations --username=your@email.com --password=yourpass
    ```
 
### Output format

For all supported commands there are two output formats available:
 - table (default)
 ```bash
 $ communauto-cli.py list-reservations       
 +----------+-----------------------+----------------------+----------------------+---------------------------+
 |       id | Car                   | From                 | To                   | Station                   |
 |----------+-----------------------+----------------------+----------------------+---------------------------|
 | 56834422 | # 1235 Toyota Corolla | Fri 21/08/2020 13:00 | Fri 28/08/2020 14:00 | 058 - Cartier et Rosemont |
 | 56834539 | # 1234 Toyota Corolla | Sun 09/08/2020 07:00 | Sun 09/08/2020 16:00 | 218 - Métro Jean-Talon    |
 +----------+-----------------------+----------------------+----------------------+---------------------------+
```
 - json
 ```bash
 $ communauto-cli.py list-reservations --output=json | jq
 {
   "reservations": [
     {
       "id": "56834422",
       "car": "# 1235 Toyota Corolla",
       "from": "Fri 21/08/2020 13:00",
       "to": "Fri 28/08/2020 14:00",
       "station": "058 - Cartier et Rosemont"
     },
     {
       "id": "56834539",
       "car": "# 1234 Toyota Corolla",
       "from": "Sun 09/08/2020 07:00",
       "to": "Sun 09/08/2020 16:00",
       "station": "218 - Métro Jean-Talon"
     }
   ]
 }
```
