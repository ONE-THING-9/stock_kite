build a fast api backend in which i want to have few api using kite connect api's. 
1. at starting of application it should get done authentication.
2. create a api which given stock name, timeframe, frm_date to to_date get the historical data. 
3. api that fetch all meta data for that api. 
4 api that fetch live data given stock name.


make sure you follow this deisgn 

backend 
    - models - model class for api's 
    - service - all service class. 
    - router - all api's routers
    - utils
    -main.py
i want to have modular design each router have its own file and seperate service file. add appropiate logging 