FirstRate Data FUTURES API Documentation
The API provides customers with a lightweight method for accessing our datasets which can be integrated into custom workflows such as Python scripts.


Note - the API does not deliver raw data, only zip archives of csv files are served. You will need to uncompress the zip archive and iterate through the files in the archive.

Datasets are updated daily. The 'update' data (for past day, week or month) are available at 1am US Eastern Time for the prior day's trade data, whereas the full archives (containing the entire historical series) are available at 2am US Eastern Time.

All API functions are authenticated using your userid which is XMbX1O2zD0--j0RfUK-W9A.
Therefore all API requests need to be appended with the parameter userid=XMbX1O2zD0--j0RfUK-W9A as shown in the examples.

Details on the futures dataset (file format, timezone etc) are available on the readme file at https://firstratedata.com/_readme/futures.txt
API Functions
The API supports the below capabilities:

Historical Data Requests - (requesting the historical datafiles)

Individual Contracts - (requesting data for individual futures contracts)

Last Update - (provides the last update date for the data. This is helpful for checking if there is fresh data available to request)

Ticker Listing - (provides the full listing of tickers as well as start and end dates)

Historical Data Requests
This function returns historical data archives (.txt files in csv format which are grouped into zip archives)

Url EndPoint : https://firstratedata.com/api/data_file

Requires Authentication : YES. All requests must include the parameter userid with your userid given to you in your signup email. Also available from your Customer Download Page.

Data Details : Full details on the data format, timezone, as well as available tickers and date ranges can be viewed on the bundle ReadMe Page

Parameters : The below parameters are used with the Url Endpoint to use the Historical Data Requests function:

Parameter : type
Accepted Values : stock , etf, futures , crypto , index , fx , options

Description : Specifies the type of instrument that is being requested.

Example :
https://firstratedata.com/api/data_file?type=futures&period=week&timeframe=1day&adjustment=contin_UNadj&userid=XMbX1O2zD0--j0RfUK-W9A

Parameter : period
Accepted Values : full , month , week , day

Description : Specifies the period to request data for. 'full' requests the entire historical archive, 'month' requests the last 30 days, 'week' requests the current trading week (starting on Monday), 'day' requests the last trading day.

Example :
https://firstratedata.com/api/data_file?type=futures&period=full&adjustment=contin_UNadj&timeframe=1hour&userid=XMbX1O2zD0--j0RfUK-W9A

Parameter : timeframe
Accepted Values : 1min , 5min , 30min , 1hour , 1day

Description : Specifies the period the timeframe of the data. '1min' will request 1-minute intraday bars, '5min' requests 5-minute bars etc.
Note : bars with zero volumes are not included
Note: 1day data also includes open - interest in the final file. (therefore the data format for 1day futures data is { DateTime, Open, High, Low, Close, Volume, Open Interest })

Example :
https://firstratedata.com/api/data_file?type=futures&period=week&adjustment=contin_UNadj&timeframe=1min&userid=XMbX1O2zD0--j0RfUK-W9A

Parameter : adjustment
Accepted Values : contin_UNadj , contin_adj_ratio , contin_adj_absolute

Description : Specifies the type of adjustment applied to the continuous data. (note the continuous data is created by stiching together front-month contracts into a single continuous series - more details on this and the adjustments can be found on our Futures Adjustment Info Page

'contin_UNadj'is the raw unadjusted trade data.
'contin_adj_ratio' is the ratio-adjusted data to avoid artifical price jumps on roll dates.
'contin_adj_absolute' is the absolute-adjusted data to avoid artifical price jumps on roll dates.
Example :
https://firstratedata.com/api/data_file?type=futures&period=week&timeframe=1day&adjustment=contin_UNadj&userid=XMbX1O2zD0--j0RfUK-W9A

Individual Contract Data
This function returns data for individual futures contracts.
All contracts are aggregated into a single zip file - one zip file can be requested for the archive data (pre 2026) and one file is for updated for 2026 data.

Url EndPoint : https://firstratedata.com/api/futures_contract

Requires Authentication : YES. All requests must include the parameter userid with your userid given to you in your signup email. Also available from your Customer Download Page.

Parameters : The below parameters are used with the Url Endpoint to use the Individual Contract function:

Parameter : contract_files
Accepted Values : archive , update

Description : An 'archive' request returns the pre-2026 data as a single zip archive of all individual futures contracts. 'update' returns a zip of the 2026 + contracts which is updated daily.

Example :
https://firstratedata.com/api/futures_contract?contract_files=update&timeframe=1min&userid=XMbX1O2zD0--j0RfUK-W9A

Parameter : timeframe
Accepted Values : 1min , 5min , 30min , 1hour , 1day

Description : Specifies the period the timeframe of the data. '1min' will request 1-minute intraday bars, '1day' requests 1-day bars etc.
Note that bars with zero volumes are not included.
Note : 1day data also includes open-interest in the final file. (therefore the data format for 1day futures data is {DateTime, Open, High, Low, Close, Volume,Open Interest})

Example :
https://firstratedata.com/api/futures_contract?contract_files=update&timeframe=1min&userid=XMbX1O2zD0--j0RfUK-W9A

Last Update
This function returns the last update for an instrument type. This function can be used to check whether there has been an update prior to executing data requests. Unlike data requests, this function returns raw data in the form of a date and not zip files.

Url EndPoint : https://firstratedata.com/api/last_update

Requires Authentication : YES. All requests must include the parameter userid with your userid given to you in your signup email. Also available from your Customer Download Page.

Parameters : The below parameters are used with the Url Endpoint to use the Last Update function:

Parameter : type
Accepted Values : stock , etf, futures , crypto , index , fx

Description : Specifies the type of instrument that is being requested.

Example :
https://firstratedata.com/api/last_update?type=futures&userid=XMbX1O2zD0--j0RfUK-W9A

Parameter : is_full_update (optional)
Accepted Values : false , true (false is the default)

Description : This parameter is used when requesting the last update of the full historical dataset (otherwise the Last Update function will return the date for the update files for the past day, week or month).

Example :
https://firstratedata.com/api/last_update?type=futures&is_full_update=true&userid=XMbX1O2zD0--j0RfUK-W9A

Ticker Listing
This function returns the full listing of tickers as well as start and end dates for a specified instrument type. The data is returned in csv format so it can be copied into a text file and opened from a spreadsheet application if required.

Url EndPoint : https://firstratedata.com/api/ticker_listing

Data Format : {ticker},{name},{startDate},{endDate}

Parameters : The below parameters are used with the Url Endpoint to use the Last Update function:

Parameter : type
Accepted Values : stock , etf

Description : Specifies the type of instrument that is being requested.

Example :
https://firstratedata.com/api/ticker_listing?type=futures&userid=XMbX1O2zD0--j0RfUK-W9A

Parameter : html
Accepted Values : true, false (false is the default value)

Description : Specifies the is the returned data is in HTML format. Set this value to true to view the data in a web browser.

Example :
https://firstratedata.com/api/ticker_listing?type=futures&userid=XMbX1O2zD0--j0RfUK-W9A&html=true