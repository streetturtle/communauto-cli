# Communauto CLI

README is in progress

## Authentication

There are 3 ways to provide your credentials to the script:

 - safest - password prompt  
 Provide your username as an option, and for the password there will be a prompt:
  
    ```bash
     $ communauto-cli.py list-reservations --username=your@email.com
     Password:   
     ```

 - most convenient - environment variable  
  Set environment variable in the current terminal session. You can add space before the 'export', to prevent command from saving in the history:
 
    ```bash
    $ export ca_user=your@email.com
    $ export ca_password=yourpass
    $ communauto-cli.py list-reservations
    ```
  
 - easiest - provide password as an option  
  Don't do this, as it will be saved in the terminal history:
  
```bash
$ communauto-cli.py list-reservations --username=your@email.com --password=yourpassword
```
 
## Output format

For all supported commands there are two formats available:
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