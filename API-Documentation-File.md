User
Login Flow
The login flow starts by navigating to the public SmartAPI login endpoint:

https://smartapi.angelone.in/publisher-login?api_key=xxx&state=statevariable
After successful login, user gets redirected to the URL specified under MyApps. With the URL we pass auth_token & feed_token as query parameters.

Request Type	APIs	Endpoint	Description
POST	Authenticate with Angel	https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword	Authenticate with Angel Login Credential
POST	Generate Token	https://apiconnect.angelone.in/rest/auth/angelbroking/jwt/v1/generateTokens	Generate jwt token on expire
GET	Get Profile	https://apiconnect.angelone.in/rest/secure/angelbroking/user/v1/getProfile	Retrieve the user profile
Authentication with Angel (Login Services)
You can authenticate to get open APIs trading access using AngelOne Ltd. Account Id. In order to login, you need a client code, valid pin and TOTP. The session established via SmartAPI remains active for upto 28 hours after login, unless the user chooses to log out.

Login Request
{
"clientcode":"Your_client_code",
"password":"Your_pin",
"totp":"enter_the_code_displayed_on_your_authenticator_app",
"state":"state_or_environment_variable"
}

Note: State variable is an optional parameter that is used in specific use cases. It is either passed in the request body of the login API as a key value pair or as a query parameter in the publisher login URL. It accepts a string and returns the same string in response. It is particularly useful for developers who develop external applications on top of SmartAPI.

Login Response
{
"status":true,
"message":"SUCCESS",
"errorcode":"",
"data":{
"jwtToken":"eyJhbGciOiJIUzUxMiJ9.eyJzdWI...",
"refreshToken":"eyJhbGciOiJIUzUxMiJ9.eyJpYXQiOjE1OTk0ODkwMz...",
"feedToken":"eyJhbGciOiJIUzUxMiJ9.eyJ1c2Vy…"
"state":"live"
  }
}
Note:- As a best practice we suggest the user to logout everyday after their activity.

import http.client
import mimetypes
conn = http.client.HTTPSConnection(
    "apiconnect.angelone.in"
    )
payload = "{\n\"clientcode\":\"CLIENT_ID\"
            ,\n\"password\":\"CLIENT_PIN\"\n
		,\n\"totp\":\"TOTP_CODE\"\n
    ,\n\"state\":\"STATE_VARIABLE\"\n}"
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-UserType': 'USER',
    'X-SourceID': 'WEB',
    'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
    'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
    'X-MACAddress': 'MAC_ADDRESS',
    'X-PrivateKey': 'API_KEY'
  }
conn.request(
    "POST", 
    "/rest/auth/angelbroking/user/
    v1/loginByPassword",
     payload,
     headers)

res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
Generate Token
Generate token helps to obtain the token after the login flow. After successful login, you get a JWT token and a Refresh token. You can use JWT token to make any transaction.

Generate Token Request
{
"refreshToken":"eyJhbGciOiJIUzUxMiJ9.eyJpYXQiOjE1OTk0OD..."
}
Generate Token Response
{
"status":true,
"message":"SUCCESS",
"errorcode":"",
"data":{
"jwtToken":"eyJhbGciOiJIUzUxMiJ9.eyJzdWIi...",
"refreshToken":"eyJhbGciOiJIUzUxMiJ9.e...",
"feedToken":"eyJhbGciOiJIUzUxMiJ9.eyJ1c2Vy…"
  }
}

import http.client
import mimetypes
conn = http.client.HTTPSConnection(
    "apiconnect.angelone.in"
    )
payload = "{\n
    \"refreshToken\":\"REFRESH_TOKEN\"
    \n}"
headers = {
    'Authorization': 'Bearer AUTHORIZATION_TOKEN',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-UserType': 'USER',
    'X-SourceID': 'WEB',
    'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
    'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
    'X-MACAddress': 'MAC_ADDRESS',
    'X-PrivateKey': 'API_KEY'
  }
conn.request("POST",
 "/rest/auth/angelbroking/jwt/
 v1/generateTokens",
  payload,
  headers)

res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
Get Profile
This allows to fetch the complete information of the user who is logged in.

Get Profile Response
{
"status":true,
"message":"SUCCESS",
"errorcode":"",
"data":{
"clientcode":"YOUR_CLIENT_CODE",
"name":"YOUR_NAME",
"email":"YOUR_EMAIL",
"mobileno":"YOUR_PHONE_NUMBER",
"exchanges":"[ "NSE", "BSE", "MCX", "CDS", "NCDEX", "NFO" ]",
"products":"[ "DELIVERY", "INTRADAY", "MARGIN"]",
"lastlogintime":"",
"brokerid":"B2C",
  }
}

import http.client
import mimetypes
conn = http.client.HTTPSConnection(
    " apiconnect.angelone.in "
    )
payload = ''
headers = headers = {
    'Authorization': 'Bearer AUTHORIZATION_TOKEN',
    'Accept': 'application/json',
    'X-UserType': 'USER',
    'X-SourceID': 'WEB',
    'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
    'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
    'X-MACAddress': 'MAC_ADDRESS',
    'X-PrivateKey': 'API_KEY'
  }
conn.request("GET",
 "/rest/secure/angelbroking/user/
 v1/getProfile", 
 payload,
 headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
Funds and Margins
The GET Request to RMS returns fund, cash and margin information of the user for equity and commodity segments.

Request Type	APIs	Endpoint	Description
GET	Get RMS Limit	https://apiconnect.angelone.in/rest/secure/angelbroking/user/v1/getRMS	To retrieve RMS limit
RMS (Risk Management System)
The RMS Limit defines margin rules to ensure that traders don't default on payments & delivery of their orders.

Get RMS Limit Response
{
"status":true,
"message":"SUCCESS",
"errorcode":"",
"data":{
"net":"9999999999999",
"availablecash":"9999999999999",
"availableintradaypayin":"0",
"availablelimitmargin":"0",
"collateral":"0",
"m2munrealized":"0",
"m2mrealized":"0",
"utiliseddebits":"0",
"utilisedspan":"0",
"utilisedoptionpremium":"0",
"utilisedholdingsales":"0",
"utilisedexposure":"0",
"utilisedturnover":"0",
"utilisedpayout":"0",
 }
}

import http.client
import mimetypes
conn = http.client.HTTPSConnection(
    " apiconnect.angelone.in "
    )
payload = ''
headers = {
    'Authorization': 'Bearer AUTHORIZATION_TOKEN',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-UserType': 'USER',
    'X-SourceID': 'WEB',
    'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
    'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
    'X-MACAddress': 'MAC_ADDRESS',
    'X-PrivateKey': 'API_KEY'
  }
conn.request("GET", 
"/rest/secure/angelbroking/user/
v1/getRMS", 
payload, 
headers)

res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
Logout
The API session is destroyed by this call and it invalidates the access_token. The user will be sent through a new login flow after this. User is not logged out of the official SmartAPI web.

Request Type	APIs	Endpoint	Description
POST	Logout	https://apiconnect.angelone.in/rest/secure/angelbroking/user/v1/logout	To logout
Logout Request
{
     "clientcode": "CLIENT_CODE"
}
Logout Response
{
     "status": true,
     "message": "SUCCESS",
     "errorcode": "",
     "data": ""
}
PythonNodeJsJavaRGO

import http.client
import mimetypes
conn = http.client.HTTPSConnection(
    " apiconnect.angelone.in "
    )
payload = "{\n     
    \"clientcode\": \"CLIENT_CODE\"\n
}"
headers = {
    'Authorization': 'Bearer AUTHORIZATION_TOKEN',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-UserType': 'USER',
    'X-SourceID': 'WEB',
    'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
    'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
    'X-MACAddress': 'MAC_ADDRESS',
    'X-PrivateKey': 'API_KEY'
  }
conn.request("POST",
"/rest/secure/angelbroking/user/v1/logout", 
payload, 
headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))

GTT
The currently supported exchange types are NSE and BSE only and the product types supported are DELIVERY and MARGIN only for now

Request Type	API's	Endpoint	Description
POST	Create Rule	https://apiconnect.angelone.in/rest/secure/angelbroking/gtt/v1/createRule	Create GTT Rule
POST	Modify Rule	https://apiconnect.angelone.in/rest/secure/angelbroking/gtt/v1/modifyRule	Modify GTT Rule
POST	Cancel Rule	https://apiconnect.angelone.in/rest/secure/angelbroking/gtt/v1/cancelRule	Cancel GTT Rule
POST	Rule Details	https://apiconnect.angelone.in/rest/secure/angelbroking/gtt/v1/ruleDetails	Get GTT Rule Details
POST	Rule List	https://apiconnect.angelone.in/rest/secure/angelbroking/gtt/v1/ruleList	Get GTT Rule List
GTT Error Codes
Sr. No	Error Code	Description
1	AB9000	Internal Server Error
2	AB9001	Invalid Parameters
3	AB9002	Method Not Allowed
4	AB9003	Invalid Client ID
5	AB9004	Invalid Status Array Size
6	AB9005	Invalid Session ID
7	AB9006	Invalid Order Quantity
8	AB9007	Invalid Disclosed Quantity
9	AB9008	Invalid Price
10	AB9009	Invalid Trigger Price
11	AB9010	Invalid Exchange Segment
12	AB9011	Invalid Symbol Token
13	AB9012	Invalid Trading Symbol
14	AB9013	Invalid Rule ID
15	AB9014	Invalid Order Side
16	AB9015	Invalid Product Type
17	AB9016	Invalid Time Period
18	AB9017	Invalid Page Value
19	AB9018	Invalid Count Value
Create Rule
When a rule is successfully created, the API returns a rule id.

All requests and its response structure is as below.
Create Rule Request
{
     "tradingsymbol": "SBIN-EQ",
     "symboltoken": "3045",
     "exchange": "NSE",
     "transactiontype": "BUY",
     "producttype": "DELIVERY",
     "price": "195",
     "qty": "1",
     "triggerprice": "196",
     "disclosedqty": "10"
}
Create Rule Response
{
     "status": true,
     "message": "SUCCESS",
     "errorcode": "",
     "data": {
          "id": "1"
     }
}

 import http.client

conn = http.client.HTTPSConnection("apiconnect.angelone.in")
payload = "{\r\n    \"tradingsymbol\": \"SBIN-EQ\",\r\n   
 \"symboltoken\": \"3045\",\r\n    \"exchange\": \"NSE\",\r\n  
   \"transactiontype\": \"BUY\",\r\n    \"producttype\": \"DELIVERY\",\r\n   
    \"price\": \"195\",\r\n    \"qty\": \"1\",\r\n 
       \"triggerprice\": \"196\",\r\n    \"disclosedqty\": \"10\"\r\n  
         }"
headers = {
  'Authorization': 'Bearer AUTHORIZATION_TOKEN',
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-UserType': 'USER',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-PrivateKey': 'API_KEY'
}
conn.request("POST", "/rest/secure/angelbroking/
gtt/v1/createRule", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
    
 
Modify Rule
When a rule is successfully modified, the API returns a rule id.

All requests and its response structure is as below.
Modify Rule Request
{
     "id": "1",
     "symboltoken": "3045",
     "exchange": "NSE",
     "price": "195",
     "qty": "1",
     "triggerprice": "196",
     "disclosedqty": "10"
}
Modify Rule Response
{
     "status": true,
     "message": "SUCCESS",
     "errorcode": "",
     "data": {
          "id": "1"
     }
}

import http.client

conn = http.client.HTTPSConnection("apiconnect.angelone.in")
payload = "{\r\n    \"id\": \"1\",\r\n 
   \"symboltoken\": \"3045\",\r\n    \"exchange\": \"NSE\",\r\n   
    \"price\": \"195\",\r\n    \"qty\": \"1\",\r\n   
     \"triggerprice\": \"196\",\r\n    \"disclosedqty\": \"10\",\r\n 
        }"
headers = {
  'Authorization': 'Bearer AUTHORIZATION_TOKEN',
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-UserType': 'USER',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-PrivateKey': 'API_KEY'
}
conn.request("POST", "/rest/secure/angelbroking/gtt/v1/modifyRule", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
   
Cancel Rule
When a rule is successfully cancelled, the API returns a rule id.

All requests and its response structure is as below.
Cancel Rule Request
{
     "id": "1",
     "symboltoken": "3045",
     "exchange": "NSE"
}
Cancel Rule Response
{
     "status": true,
     "message": "SUCCESS",
     "errorcode": "",
     "data": {
          "id": "1"
     }
}

import http.client

conn = http.client.HTTPSConnection("apiconnect.angelone.in")
payload = "{\r\n    \"id\": \"1\",\r\n   
 \"symboltoken\": \"3045\",\r\n    \"exchange\": \"NSE\"\r\n}"
headers = {
  'Authorization': 'Bearer AUTHORIZATION_TOKEN',
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-UserType': 'USER',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-PrivateKey': 'API_KEY'
}
conn.request("POST", "/rest/secure/angelbroking/gtt/v1/cancelRule
", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
Rule Details Request
When a rule is successfully fetched, the API returns complete details of the rule.

All requests and its response structure is as below.
Rule Details Request
{
     "id": "1"
}
Rule Details Response
{
     "status": true,
     "message": "SUCCESS",
     "errorcode": "",
     "data": {
          "status": "NEW",
          "createddate": "2020-11-16T14:19:51Z",
          "updateddate": "2020-11-16T14:28:01Z",
          "expirydate": "2021-11-16T14:19:51Z",
          "clientid": "100",
          "tradingsymbol": "SBIN-EQ",
          "symboltoken": "3045",
          "exchange": "NSE",
          "transactiontype": "BUY",
          "producttype": "DELIVERY",
          "price": "195",
          "qty": "1",
          "triggerprice": "196",
          "disclosedqty": "10"
     }
}

import http.client

conn = http.client.HTTPSConnection("apiconnect.angelone.in")
payload = "{\r\n    \"id\": \"1\"\r\n}"
headers = {
  'Authorization': 'Bearer AUTHORIZATION_TOKEN',
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-UserType': 'USER',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-PrivateKey': 'API_KEY'
}
conn.request("POST", "/rest/secure/angelbroking/
gtt/v1/ruleDetails", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
   
Rule List Request
When a list of rules is successfully fetched, the API returns complete details for the list of rules.

All requests and its response structure is as below.
Rule List Request
{
     "status": [
          "NEW",
          "CANCELLED",
          "ACTIVE",
          "SENTTOEXCHANGE",
          "FORALL"
     ],
     "page": 1,
     "count": 10
}
Rule List Response
{
     "status": true,
     "message": "SUCCESS",
     "errorcode": "",
     "data": {
          "clientid": "100",
          "createddate": "2020-11-16T14:19:51Z",
          "exchange": "NSE",
          "producttype": "DELIVERY",
          "transactiontype": "BUY",
          "expirydate": "2021-11-16T14:19:51Z",
          "id": "1",
          "qty": "1",
          "price": "195",
          "status": "NEW",
          "symboltoken": "3045",
          "tradingsymbol": "SBIN-EQ",
          "triggerprice": "196",
          "updateddate": "2020-11-16T14:28:01Z"
     }
}
PythonNodeJsJavaRGO

import http.client

conn = http.client.HTTPSConnection("apiconnect.angelone.in")
payload = "{\r\n    \"status\": [\r\n        \"NEW\",\r\n     
   \"CANCELLED\",\r\n        \"ACTIVE\",\r\n      
     \"SENTTOEXCHANGE\",\r\n        \"FORALL\"\r\n    ],
     \r\n    \"page\": 1,\r\n    \"count\": 10\r\n}"
headers = {
  'Authorization': 'Bearer AUTHORIZATION_TOKEN',
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-UserType': 'USER',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-PrivateKey': 'API_KEY'
}
conn.request("POST", "/rest/secure/angelbroking/gtt/v1/ruleList
", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
   

Orders
The order APIs allows you to place orders of different varieties like normal orders, after market orders & stoploss orders.

Request Type	APIs	Endpoint	Description
POST	Place Order	https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/placeOrder	To place an order
POST	Modify Order	https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/modifyOrder	To modify an order
POST	Cancel Order	https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/cancelOrder	To cancel an order
GET	Get Order Book	https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/getOrderBook	To retrieve Order book
GET	Get Trade Book	https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/getTradeBook	To retrieve trade book
POST	Get LTP Data	https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/getLtpData	To retrieve LTP data
GET	Get Individual Order Data	https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/details/{UniqueOrderID}	To retrieve individual order data
See the list of constants in below given table.

Order Constants
Here are several of the constant enum values used for placing orders.

Param	Value	Description
variety	
NORMAL

STOPLOSS

ROBO

Normal Order (Regular)

Stop loss order

ROBO (Bracket Order)

transactiontype	
BUY

SELL

Buy

Sell

ordertype	
MARKET

LIMIT

STOPLOSS_LIMIT

STOPLOSS_MARKET

Market Order(MKT)

Limit Order(L)

Stop Loss Limit Order(SL)

Stop Loss Market Order(SL-M)

producttype	
DELIVERY

CARRYFORWARD

MARGIN

INTRADAY

BO

Cash & Carry for equity (CNC)

Normal for futures and options (NRML)

Margin Delivery

Margin Intraday Squareoff (MIS)

Bracket Order (Only for ROBO)

Duration	
DAY

IOC

Regular Order

Immediate or Cancel

exchange	
BSE

NSE

NFO

MCX

BFO

CDS

BSE Equity

NSE Equity

NSE Future and Options

MCX Commodity

BSE Futures and Options

Currency Derivate Segment

Order Parameters
These parameters are common across different order varieties.

Param	Description
tradingsymbol	Trading Symbol of the instrument
symboltoken	Symbol Token is unique identifier
Exchange	Name of the exchange
transactiontype	BUY or SELL
ordertype	Order type (MARKET, LIMIT etc.)
quantity	Quantity to transact
producttype	Product type (CNC,MIS)
price	The min or max price to execute the order at (for LIMIT orders)
triggerprice	The price at which an order should be triggered (SL, SL-M)
squareoff	Only For ROBO (Bracket Order)
stoploss	Only For ROBO (Bracket Order)
trailingStopLoss	Only For ROBO (Bracket Order)
disclosedquantity	Quantity to disclose publicly (for equity trades)
duration	Order duration (DAY,IOC)
ordertag	It is optional to apply to an order to identify. The length of the tag should be less than 20 characters.
Place Orders
When an order is successfully placed, the API returns an order_id. The status of the order is not known at the moment of placing because of the aforementioned reasons.

All the orders placed after market hours will be treated as AMO orders.

All requests and its response structure is as below.
Place Order Request
{
"variety":"NORMAL",
"tradingsymbol":"SBIN-EQ",
"symboltoken":"3045",
"transactiontype":"BUY",
"exchange":"NSE",
"ordertype":"MARKET",
"producttype":"INTRADAY",
"duration":"DAY",
"price":"194.50",
"squareoff":"0",
"stoploss":"0",
"quantity":"1"
}
Place Order Response
{
"status":true,
"message":"SUCCESS",
"errorcode":"",
"data":{
 "script":"SBIN-EQ",
 "orderid":"200910000000111"
 "uniqueorderid":"34reqfachdfih"
 }
}

import http.client
import mimetypes
conn = http.client.HTTPSConnection(
    "apiconnect.angelone.in"
    )
payload = "{\n 
       \"exchange\": \"NSE\",
       \n    \"tradingsymbol\": \"INFY-EQ\",
       \n    \"quantity\": 5,
       \n    \"disclosedquantity\": 3,
       \n    \"transactiontype\": \"BUY\",
       \n    \"ordertype\": \"MARKET\",
       \n    \"variety\": \"STOPLOSS\",
       \n    \"producttype\": \"INTRADAY\"
       \n}"
headers = {
  'Authorization': 'Bearer AUTHORIZATION_TOKEN',
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-UserType': 'USER',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-PrivateKey': 'API_KEY'
}
conn.request("POST", 
"/rest/secure/angelbroking/order/
v1/placeOrder", 
payload, 
headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
Modify Order
As long as on order is open or pending in the system, certain attributes of it may be modified. It is important to sent the right value for :variety in the URL.

Modify Order Request
{
"variety":"NORMAL",
"orderid":"201020000000080",
"ordertype":"LIMIT",
"producttype":"INTRADAY",
"duration":"DAY",
"price":"194.00",
"quantity":"1",
"tradingsymbol":"SBIN-EQ",
"symboltoken":"3045",
"exchange":"NSE"
}
Modify Order Response
{
"status":true,
"message":"SUCCESS",
"errorcode":"",
"data":{
 "orderid":"201020000000080"
 "uniqueorderid":"34reqfachdfih"
  }
}

import http.client
import mimetypes
conn = http.client.HTTPSConnection(
    "apiconnect.angelone.in"
    )
payload = "{\n    
    \"variety\": \"NORMAL\",\n    
    \"orderid\": \"201020000000080\",\n    
    \"ordertype\": \"LIMIT\",\n    
    \"producttype\": \"INTRADAY\",\n    
    \"duration\": \"DAY\",\n    
    \"price\": \"194.00\",\n    
    \"quantity\": \"1\"\n
}"

headers = {
  'Authorization': 'Bearer AUTHORIZATION_TOKEN',
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-UserType': 'USER',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-PrivateKey': 'API_KEY'
}
conn.request("POST", 
"/rest/secure/angelbroking/order/
v1/modifyOrder",
 payload, 
 headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
Cancel Order
As long as on order is open or pending in the system, it can be cancelled.

Cancel Order Request
{
"variety":"NORMAL",
"orderid":"201020000000080",
}
Cancel Order Response
{
"status":true,
"message":"SUCCESS",
"errorcode":"",
"data":{
 "orderid":"201020000000080"
 "uniqueorderid":"34reqfachdfih"
  }
}

import http.client
import mimetypes
conn = http.client.HTTPSConnection(
    "apiconnect.angelone.in"
    )
payload = "{\n    
    \"variety\": \"NORMAL\",\n    
    \"orderid\": \"201020000000080\"\n
}"

headers = {
  'Authorization': 'Bearer AUTHORIZATION_TOKEN',
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-UserType': 'USER',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-PrivateKey': 'API_KEY'
}
conn.request("POST",
 "/rest/secure/angelbroking/order/
 v1/cancelOrder",
  payload,
   headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
Get Order Book
Get Order Status Response
{
"status":true,
"message":"SUCCESS",
"errorcode":"",
"data":[{
"variety":NORMAL,
"ordertype":LIMIT,
"producttype":INTRADAY,
"duration":DAY,
"price":"194.00",
"triggerprice":"0",
"quantity":"1",
"disclosedquantity":"0",
"squareoff":"0",
"stoploss":"0",
"trailingstoploss":"0",
"tradingsymbol":"SBIN-EQ",
"transactiontype":BUY,
"exchange":NSE,
"symboltoken":null,
"instrumenttype":"",
"strikeprice":"-1",
"optiontype":"",
"expirydate":"",
"lotsize":"1",
"cancelsize":"1",
"averageprice":"0",
"filledshares":"0",
"unfilledshares":"1",
"orderid":201020000000080,
"text":"",
"status":"cancelled",
"orderstatus":"cancelled",
"updatetime":"20-Oct-2020 13:10:59",
"exchtime":"20-Oct-2020 13:10:59",
"exchorderupdatetime":"20-Oct-2020 13:10:59",
"fillid":"",
"filltime":"",
"parentorderid":"",
"uniqueorderid":"34reqfachdfih",
"exchangeorderid":"1100000000048358"
 }]
}

import http.client
import mimetypes
conn = http.client.HTTPSConnection(
    " apiconnect.angelone.in "
    )
payload = ''
headers = {
  'Authorization': 'Bearer AUTHORIZATION_TOKEN',
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-UserType': 'USER',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-PrivateKey': 'API_KEY'
}
conn.request("GET", 
"/rest/secure/angelbroking/order/
v1/getOrderBook", 
payload, 
headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
Get Trade Book
It provides the trades for the current day

Get Trade Book Response
{
"status":true,
"message":"SUCCESS",
"errorcode":"",
"data":[{
"exchange":NSE,
"producttype":DELIVERY,
"tradingsymbol":"ITC-EQ",
"instrumenttype":"",
"symbolgroup":"EQ",
"strikeprice":"-1",
"optiontype":"",
"expirydate":"",
"marketlot":"1",
"precision":"2",
"multiplier":"-1",
"tradevalue":"175.00",
"transactiontype":"BUY",
"fillprice":"175.00",
"fillsize":"1",
"orderid":"201020000000095",
"fillid":"50005750",
"filltime":"13:27:53",
 }]
}
PythonNodeJsJavaRGO

import http.client
import mimetypes
conn = http.client.HTTPSConnection(
    " apiconnect.angelone.in "
    )
payload = ''
headers = {
  'Authorization': 'Bearer AUTHORIZATION_TOKEN',
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-UserType': 'USER',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-PrivateKey': 'API_KEY'
}
conn.request("GET", 
"/rest/secure/angelbroking/order/
v1/getTradeBook", 
payload, 
headers)

res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
Get LTP Data
Get LTP Data Request
{
"exchange":"NSE",
"tradingsymbol":"SBIN-EQ"
"symboltoken":"3045"
}
Get LTP Data Response
{
"status":true,
"message":"SUCCESS",
"errorcode":"",
"data":{
"exchange":"NSE",
"tradingsymbol":"SBIN-EQ",
"symboltoken":"3045",
"open":"186",
"high":"191.25",
"low":"185",
"close":"187.80",
"ltp":"191",
 }
}

import http.client
import mimetypes
conn = http.client.HTTPSConnection(
    "apiconnect.angelone.in"
    )
payload = "{\n    
    \"exchange\": \"NSE\",\n    
    \"tradingsymbol\": \"SBIN-EQ\",\n     
    \"symboltoken\":\"3045\"\n
}"

headers = {
  'Authorization': 'Bearer AUTHORIZATION_TOKEN',
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-UserType': 'USER',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-PrivateKey': 'API_KEY'
}
conn.request("POST", 
"/rest/secure/angelbroking/order/
v1/getLtpData", 
payload, 
headers
)

res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
Individual Order Status
This API allows you to retrieve the status of individual orders using the "uniqueorderid" you receive in the response when placing, modifying, or canceling orders.

Individual Order Status Request
https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/details/05ebf91b-bea4-4a1d-b0f2-4259606570e3
Individual Order Status Response
{
     "status": true,
     "message": "SUCCESS",
     "errorcode": "",
     "data": {
          "variety": "NORMAL",
          "ordertype": "LIMIT",
          "producttype": "DELIVERY",
          "duration": "DAY",
          "price": 2298.25,
          "triggerprice": 0,
          "quantity": "1",
          "disclosedquantity": "0",
          "squareoff": 0,
          "stoploss": 0,
          "trailingstoploss": 0,
          "tradingsymbol": "RELIANCE-EQ",
          "transactiontype": "BUY",
          "exchange": "NSE",
          "symboltoken": "2885",
          "instrumenttype": "",
          "strikeprice": -1,
          "optiontype": "",
          "expirydate": "",
          "lotsize": "1",
          "cancelsize": "0",
          "averageprice": 0,
          "filledshares": "0",
          "unfilledshares": "1",
          "orderid": "231010000000970",
          "text": "Your order has been rejected due to Insufficient Funds. Available funds - Rs. 937.00 . You require Rs. 2298.25 funds to execute this order.",
          "status": "rejected",
          "orderstatus": "rejected",
          "updatetime": "10-Oct-2023 09:00:16",
          "exchtime": "",
          "exchorderupdatetime": "",
          "fillid": "",
          "filltime": "",
          "parentorderid": "",
          "ordertag": "",
          "uniqueorderid": "05ebf91b-bea4-4a1d-b0f2-4259606570e3"
     }
}
NOTE:
Unique Order ID - This identifier will be included in the response every time you interact with our APIs, whether you're placing an order, modifying it, canceling it, or checking your order book. This unique identifier simplifies the process of tracking and managing your orders with precision.


PythonNodeJsJavaRGO

import http.client

conn = http.client.HTTPSConnection("apiconnect.angelone.in")

headers = {
  'X-PrivateKey': 'API_KEY',
  'Accept': 'application/json',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-UserType': 'USER',
  'Authorization': 'Bearer AUTHORIZATION_TOKEN',
  'Accept': 'application/json',
  'X-SourceID': 'WEB',
  'Content-Type': 'application/json'
}

conn.request("GET", "/rest/secure/angelbroking/
order/v1/details/05ebf91b-bea4-4a1d-b0f2-4259606570e3", "", headers)

res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))

 Portfolio
A portfolio is a collection of financial investments like stocks, bonds, commodities, cash, and cash equivalents, including long-term equity holdings and short-term positions. The portfolio APIs return instruments in a portfolio with updated profit and loss computations.

Request Type	APIs	Endpoint	Description
GET	Get Holding	https://apiconnect.angelone.in/rest/secure/angelbroking/portfolio/v1/getHolding	To retrieve holding
GET	Get All Holding	https://apiconnect.angelone.in/rest/secure/angelbroking/portfolio/v1/getAllHolding	To retrieve all holding
GET	Get Position	https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/getPosition	To retrieve positIon
POST	Convert Position	https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/convertPosition	To convert position
Get Holdings
Holdings comprises of the user's portfolio of long-term equity delivery stocks. An instrument in a holding's portfolio remains there indefinitely until its sold or is delisted or changed by the exchanges. Underneath it all, instruments in the holdings reside in the user's DEMAT account, as settled by exchanges and clearing institutions.

Get Holding Response
{
     "tradingsymbol": "TATASTEEL-EQ",
     "exchange": "NSE",
     "isin": "INE081A01020",
     "t1quantity": 0,
     "realisedquantity": 2,
     "quantity": 2,
     "authorisedquantity": 0,
     "product": "DELIVERY",
     "collateralquantity": null,
     "collateraltype": null,
     "haircut": 0,
     "averageprice": 111.87,
     "ltp": 130.15,
     "symboltoken": "3499",
     "close": 129.6,
     "profitandloss": 37,
     "pnlpercentage": 16.34
}

import http.client
import mimetypes
conn = http.client.HTTPSConnection(
    " apiconnect.angelone.in "
    )
payload = ''
headers = {
  'Authorization': 'Bearer AUTHORIZATION_TOKEN',
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-UserType': 'USER',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-PrivateKey': 'API_KEY'
}
conn.request("GET", 
"/rest/secure/angelbroking/portfolio/
v1/getHolding", 
payload, 
headers)

res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
Get All Holdings
This endpoint offers a more comprehensive view of your entire investments, including individual stock holdings and a summary of your total investments. In addition to the updates for individual stock holdings, we have introduced a new section in the response called "totalholding," which provides a summary of your entire investments, including:

totalholdingvalue: The total value of all your holdings.
totalinvvalue: The total investment value.
totalprofitandloss: The total profit and loss across all holdings.
totalpnlpercentage: The total profit and loss percentage for your entire portfolio.
Get Holding Response
{
     "status": true,
     "message": "SUCCESS",
     "errorcode": "",
     "data": {
          "holdings": [
               {
                    "tradingsymbol": "TATASTEEL-EQ",
                    "exchange": "NSE",
                    "isin": "INE081A01020",
                    "t1quantity": 0,
                    "realisedquantity": 2,
                    "quantity": 2,
                    "authorisedquantity": 0,
                    "product": "DELIVERY",
                    "collateralquantity": null,
                    "collateraltype": null,
                    "haircut": 0,
                    "averageprice": 111.87,
                    "ltp": 130.15,
                    "symboltoken": "3499",
                    "close": 129.6,
                    "profitandloss": 37,
                    "pnlpercentage": 16.34
               },
               {
                    "tradingsymbol": "PARAGMILK-EQ",
                    "exchange": "NSE",
                    "isin": "INE883N01014",
                    "t1quantity": 0,
                    "realisedquantity": 2,
                    "quantity": 2,
                    "authorisedquantity": 0,
                    "product": "DELIVERY",
                    "collateralquantity": null,
                    "collateraltype": null,
                    "haircut": 0,
                    "averageprice": 154.03,
                    "ltp": 201,
                    "symboltoken": "17130",
                    "close": 192.1,
                    "profitandloss": 94,
                    "pnlpercentage": 30.49
               },
               {
                    "tradingsymbol": "SBIN-EQ",
                    "exchange": "NSE",
                    "isin": "INE062A01020",
                    "t1quantity": 0,
                    "realisedquantity": 8,
                    "quantity": 8,
                    "authorisedquantity": 0,
                    "product": "DELIVERY",
                    "collateralquantity": null,
                    "collateraltype": null,
                    "haircut": 0,
                    "averageprice": 573.1,
                    "ltp": 579.05,
                    "symboltoken": "3045",
                    "close": 570.5,
                    "profitandloss": 48,
                    "pnlpercentage": 1.04
               }
          ],
          "totalholding": {
               "totalholdingvalue": 5294,
               "totalinvvalue": 5116,
               "totalprofitandloss": 178.14,
               "totalpnlpercentage": 3.48
          }
     }
}

import http.client
import mimetypes
conn = http.client.HTTPSConnection(
    " apiconnect.angelone.in "
    )
payload = ''
headers = {
  'Authorization': 'Bearer AUTHORIZATION_TOKEN',
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-UserType': 'USER',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-PrivateKey': 'API_KEY'
}
conn.request("GET", 
"/rest/secure/angelbroking/portfolio/v1/getAllHolding", 
payload, 
headers)

res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
Get Position
This API returns two sets of positions, net and day. net is the actual, current net position portfolio, while day is a snapshot of the buying and selling activity for that particular day.

Get Position Response
{
     "status": true,
     "message": "SUCCESS",
     "errorcode": "",
     "data": [
          {
               "exchange": "NSE",
               "symboltoken": "2885",
               "producttype": "DELIVERY",
               "tradingsymbol": "RELIANCE-EQ",
               "symbolname": "RELIANCE",
               "instrumenttype": "",
               "priceden": "1",
               "pricenum": "1",
               "genden": "1",
               "gennum": "1",
               "precision": "2",
               "multiplier": "-1",
               "boardlotsize": "1",
               "buyqty": "1",
               "sellqty": "0",
               "buyamount": "2235.80",
               "sellamount": "0",
               "symbolgroup": "EQ",
               "strikeprice": "-1",
               "optiontype": "",
               "expirydate": "",
               "lotsize": "1",
               "cfbuyqty": "0",
               "cfsellqty": "0",
               "cfbuyamount": "0",
               "cfsellamount": "0",
               "buyavgprice": "2235.80",
               "sellavgprice": "0",
               "avgnetprice": "2235.80",
               "netvalue": "- 2235.80",
               "netqty": "1",
               "totalbuyvalue": "2235.80",
               "totalsellvalue": "0",
               "cfbuyavgprice": "0",
               "cfsellavgprice": "0",
               "totalbuyavgprice": "2235.80",
               "totalsellavgprice": "0",
               "netprice": "2235.80"
          }
     ]
}

import http.client
import mimetypes
conn = http.client.HTTPSConnection(
    " apiconnect.angelone.in "
    )
payload = ''
headers = {
  'Authorization': 'Bearer AUTHORIZATION_TOKEN',
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-UserType': 'USER',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-PrivateKey': 'API_KEY'
}
conn.request("GET", 
"/rest/secure/angelbroking/order/
v1/getPosition", 
payload, 
headers)

res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
Convert Position
Each position has one margin product. These products affect how the user's margin usage and free cash values are computed, and a user may wish to convert or change a position's margin product on timely basis.

Position Conversion Request
{
     "exchange": "NSE",
     "symboltoken": "2885",
     "oldproducttype": "DELIVERY",
     "newproducttype": "INTRADAY",
     "tradingsymbol": "RELIANCE-EQ",
     "symbolname": "RELIANCE",
     "instrumenttype": "",
     "priceden": "1",
     "pricenum": "1",
     "genden": "1",
     "gennum": "1",
     "precision": "2",
     "multiplier": "-1",
     "boardlotsize": "1",
     "buyqty": "1",
     "sellqty": "0",
     "buyamount": "2235.80",
     "sellamount": "0",
     "transactiontype": "BUY",
     "quantity": 1,
     "type": "DAY"
}
Position Conversion Response
{
     "status": true,
     "message": "SUCCESS",
     "errorcode": "",
     "data": null
}
PythonNodeJsJavaRGO

import http.client
import mimetypes
conn = http.client.HTTPSConnection(
    " apiconnect.angelone.in "
    )
payload = "{\n    
    \"exchange\": \"NSE\",\n    
    \"symboltoken\": \"2885\",\n    
    \"oldproducttype\": \"DELIVERY\",\n    
    \"newproducttype\": \"INTRADAY\",\n    
    \"tradingsymbol\": \"RELIANCE-EQ\",\n    
    \"symbolname\": \"RELIANCE\",\n    
    \"instrumenttype\": \"\",\n    
    \"priceden\": \"1\",\n    
    \"pricenum\": \"1\",\n   
    \"genden\": \"1\",\n   
    \"gennum\": \"1\",\n    
    \"precision\": \"2\",\n    
    \"multiplier\": \"-1\",\n    
    \"boardlotsize\": \"1\",\n    
    \"buyqty\": \"1\",\n    
    \"sellqty\": \"0\",\n    
    \"buyamount\": \"2235.80\",\n    
    \"sellamount\": \"0\",\n    
    \"transactiontype\": \"BUY\",\n    
    \"quantity\": 1,\n    
    \"type\": \"DAY\"\n
}"

headers = {
  'Authorization': 'Bearer AUTHORIZATION_TOKEN',
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-UserType': 'USER',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-PrivateKey': 'API_KEY'
}
conn.request("POST",
 "/rest/secure/angelbroking/order/
 v1/convertPosition", 
 payload, 
 headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))


Postback/Webhook
Postback URL provides real time order updates for the orders placed via APIs. The Postback URL can be specified while creating the API Key. Updates will be sent to the mapped url against the API key used to execute the orders.

Sample Response

{
    "variety": "NORMAL",
    "ordertype": "MARKET",
    "producttype": "DELIVERY",
    "duration": "DAY",
    "price": 0.0,
    "triggerprice": 0.0,
    "quantity": "1000",
    "disclosedquantity": "0",
    "squareoff": 0.0,
    "stoploss": 0.0,
    "trailingstoploss": 0.0,
    "tradingsymbol": "SBIN-EQ",
    "transactiontype": "BUY",
    "exchange": "NSE",
    "symboltoken": "3045",
    "ordertag": "10007712",
    "instrumenttype": "",
    "strikeprice": -1.0,
    "optiontype": "",
    "expirydate": "",
    "lotsize": "1",
    "cancelsize": "0",
    "averageprice": 584.7,
    "filledshares": "74",
    "unfilledshares": "926",
    "orderid": "111111111111111",
    "text": "",
    "status": "open",
    "orderstatus": "open",
    "updatetime": "09-Oct-2023 18:22:02",
    "exchtime": "09-Oct-2023 18:21:12",
    "exchorderupdatetime": "09-Oct-2023 18:21:12",
    "fillid": "",
    "filltime": "",
    "parentorderid": "",
    "clientcode": "DUMMY123"
}
NOTE:
Postback service only allows the updates on HTTPS port 443
For AMO orders, postback notifications will not be sent immediately at the time of placing the order after market hours. These notifications will be sent at 9:00 AM when those orders are sent to the exchange for processing.
We are providing order status such as open, pending, executed, cancelled, partially executed and so on the postback call for the orders placed during market hours.


Live Market Data API
The Live Market Data API provides real-time market data for specific symbols, allowing clients to make informed trading and investment decisions. The API offers three distinct modes: LTP, OHLC, and FULL, each delivering varying levels of comprehensive market information.

https://apiconnect.angelone.in/rest/secure/angelbroking/market/v1/quote/
Modes
Modes	Description
LTP Mode	Retrieve the latest Last Traded Price (LTP) for a specified exchange and symbol.
OHLC Mode	Retrieve the Open, High, Low, and Close prices for a given exchange and symbol.
Full Mode	Access an extensive set of data for a specified exchange and symbol. This mode provides a comprehensive range of data points, including LTP, open, high, low, close prices, last trade quantity, exchange feed time, exchange trade time, net change, percent change, average price, trade volume, open interest, circuit limits, total buying and selling quantity, 52-week low, 52-week high, and depth information for the best five buy and sell orders.
Supported Exchanges
All exchanges are supported.

Number of tokens supported in one request:
The market data API allows you to fetch data for 50 symbols in just one request with a rate limit of 1 request per second

Request Format
Mode	Sample Request
Full Mode	{ "mode": "FULL", "exchangeTokens": { "NSE": ["3045","881"], "NFO": ["58662"]} }
OHLC Mode	{ "mode": "OHLC", "exchangeTokens": { "NSE": ["3045","881"], "NFO": ["58662"]} }
LTP Mode	{ "mode": "LTP", "exchangeTokens": { "NSE": ["3045","881"], "NFO": ["58662"]} }
Response Format
The response is a JSON object containing the requested stock market data:

status: A boolean indicating whether the request was successful.
message: A string describing the status of the request.
errorcode: A string providing specific error codes, if any.
data: An object containing the fetched market data and any unfetched data with errors.
Sample Response (FULL Mode):
{
     "status": true,
     "message": "SUCCESS",
     "errorcode": "",
     "data": {
          "fetched": [
               {
                    "exchange": "NSE",
                    "tradingSymbol": "SBIN-EQ",
                    "symbolToken": "3045",
                    "ltp": 568.2,
                    "open": 567.4,
                    "high": 569.35,
                    "low": 566.1,
                    "close": 567.4,
                    "lastTradeQty": 1,
                    "exchFeedTime": "21-Jun-2023 10:46:10",
                    "exchTradeTime": "21-Jun-2023 10:46:09",
                    "netChange": 0.8,
                    "percentChange": 0.14,
                    "avgPrice": 567.83,
                    "tradeVolume": 3556150,
                    "opnInterest": 0,
                    "lowerCircuit": 510.7,
                    "upperCircuit": 624.1,
                    "totBuyQuan": 839549,
                    "totSellQuan": 1284767,
                    "52WeekLow": 430.7,
                    "52WeekHigh": 629.55,
                    "depth": {
                         "buy": [
                              {
                                   "price": 568.2,
                                   "quantity": 511,
                                   "orders": 2
                              },
                              {
                                   "price": 568.15,
                                   "quantity": 411,
                                   "orders": 2
                              },
                              {
                                   "price": 568.1,
                                   "quantity": 31,
                                   "orders": 2
                              },
                              {
                                   "price": 568.05,
                                   "quantity": 1020,
                                   "orders": 8
                              },
                              {
                                   "price": 568,
                                   "quantity": 1704,
                                   "orders": 28
                              }
                         ],
                         "sell": [
                              {
                                   "price": 568.25,
                                   "quantity": 3348,
                                   "orders": 5
                              },
                              {
                                   "price": 568.3,
                                   "quantity": 4447,
                                   "orders": 13
                              },
                              {
                                   "price": 568.35,
                                   "quantity": 3768,
                                   "orders": 11
                              },
                              {
                                   "price": 568.4,
                                   "quantity": 8500,
                                   "orders": 40
                              },
                              {
                                   "price": 568.45,
                                   "quantity": 4814,
                                   "orders": 17
                              }
                         ]
                    }
               }
          ],
          "unfetched": []
     }
}
Sample Response (OHLC Mode):
{
     "status": true,
     "message": "SUCCESS",
     "errorcode": "",
     "data": {
          "fetched": [
               {
                    "exchange": "NSE",
                    "tradingSymbol": "SBIN-EQ",
                    "symbolToken": "3045",
                    "ltp": 571.8,
                    "open": 568.75,
                    "high": 568.75,
                    "low": 567.05,
                    "close": 566.5
               }
          ],
          "unfetched": []
     }
}
Sample Response (LTP Mode):
{
     "status": true,
     "message": "SUCCESS",
     "errorcode": "",
     "data": {
          "fetched": [
               {
                    "exchange": "NSE",
                    "tradingSymbol": "SBIN-EQ",
                    "symbolToken": "3045",
                    "ltp": 571.75
               }
          ],
          "unfetched": []
     }
}
Sample Response (LTP Mode where data cannot be fetched):
{
     "success": true,
     "message": "SUCCESS",
     "errorCode": "",
     "data": {
          "fetched": [],
          "unfetched": [
               {
                    "exchange": "MCX",
                    "symbolToken": "",
                    "message": "Symbol token cannot be empty",
                    "errorCode": "AB4018"
               }
          ]
     }
}
Field Description
Field	Data Type	Description
success	Boolean	Indicates whether the API request was successful.
message	String	Provides success or error message.
errorCode	String	Displays the error code if there was an issue with the request. Otherwise, it is blank.
data	Object	Contains the fetched and unfetched data.
data.fetched	Array	Array of fetched data objects.
exchange	Enum ( Values - NSE, NFO,BSE, MCX, CDS, NCDEX )	The exchange for the fetched data.
tradingSymbol	String	The trading symbol for the fetched data.
symbolToken	String	The token for the fetched symbol.
ltp	Float	The last trading price for the fetched symbol.
open	Float	The opening price for the fetched symbol.
high	Float	The highest price for the fetched symbol.
low	Float	The lowest price for the fetched symbol.
close	Float	The previous closing price for the fetched symbol.
lastTradeQty	Integer	The quantity of the last trade executed for the fetched symbol.
exchFeedTime	String	The exchange feed time for the fetched symbol.
exchTradeTime	String	The exchange trade time for the fetched symbol.
netChange	Float	The net change for the fetched symbol.
percentChange	Float	The percent change for the fetched symbol.
avgPrice	Float	The average price for the fetched symbol.
tradeVolume	Integer	The trade volume for the fetched symbol.
opnInterest	Integer	The open interest for the fetched symbol.
upperCircuit	Float	Maximum price increase allowed before trading pauses temporarily.
lowerCircuit	Float	Maximum price decrease allowed before trading pauses temporarily.
totBuyQuan	Integer	The total buy quantity for the fetched symbol.
totSellQuan	Integer	The total sell quantity for the fetched symbol.
52WeekHigh	Float	The yearly highest price for the fetched symbol.
52WeekLow	Float	The yearly lowest price for the fetched symbol.
depth.buy	Array	Array of buy depth objects.
depth.buy[n].price	Float	The price at the nth level of buy depth.
depth.buy[n].quantity	Integer	The quantity at the nth level of buy depth.
depth.buy[n].orders	Integer	The number of buy orders at the nth level of market depth.
depth.sell	Array	Array of sell depth objects.
depth.sell[n].price	Float	The price at the nth level of sell depth.
depth.sell[n].quantity	Integer	The quantity at the nth level of sell depth.
depth.sell[n].orders	Integer	The number of sell orders at the nth level of market depth.


Historical API
Historical API provides past data of the indices and instruments. When a successful request is placed, corresponding data is returned. A single API endpoint provides the data for all segments. The exchange parameter in the request body is used to specify the segment whose data is required.

https://apiconnect.angelone.in/rest/secure/angelbroking/historical/v1/getCandleData
Exchange Constants
Param	Value	Description
exchange	NSE	NSE Stocks and Indices
NFO	NSE Futures and Options
BSE	BSE Stocks and Indices
BFO	BSE Future and Options
CDS	Currency Derivatives
MCX	Commodities Exchange
Interval Constants
Interval	Description
ONE_MINUTE	1 Minute
THREE_MINUTE	3 Minute
FIVE_MINUTE	5 Minute
TEN_MINUTE	10 Minute
FIFTEEN_MINUTE	15 Minute
THIRTY_MINUTE	30 Minute
ONE_HOUR	1 Hour
ONE_DAY	1 Day
Max Days in one Request
The API can provide data of multiple days in one request. Below is the list of Max no of days upto which data can be provided for the requested intervals:

Interval	Max Days in one Request
ONE_MINUTE	30
THREE_MINUTE	60
FIVE_MINUTE	100
TEN_MINUTE	100
FIFTEEN_MINUTE	200
THIRTY_MINUTE	200
ONE_HOUR	400
ONE_DAY	2000
Get Candle Data
All requests and its response structure is as below.
Get Candle Data Request
{
     "exchange": "NSE",
     "symboltoken": "99926000",
     "interval": "ONE_HOUR",
     "fromdate": "2023-09-06 11:15",
     "todate": "2023-09-06 12:00"
}
Get Candle Data Response
{
     "status": true,
     "message": "SUCCESS",
     "errorcode": "",
     "data": [
          [
               "2023-09-06T11:15:00+05:30",
               19571.2,
               19573.35,
               19534.4,
               19552.05,
               0
          ]
     ]
}

NOTE:
In Get Candle Data Request fromdate and todate format should be "yyyy-MM-dd hh:mm"
The response is an array of records, where each record in turn is an array of the following values — [timestamp, open, high, low, close, volume].

PythonNodeJsJavaRGO

import http.client

conn = http.client.HTTPSConnection("apiconnect.angelone.in")
payload = "{\r\n     \"exchange\": \"NSE\",\r\n    
 \"symboltoken\": \"3045\",\r\n     \"interval\": \"ONE_MINUTE\",\r\n  
    \"fromdate\": \"2021-02-08 09:00\",\r\n     \"todate\": \"2021-02-08 09:16\"\r\n}"
headers = {
  'X-PrivateKey': 'API_KEY',
  'Accept': 'application/json',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-UserType': 'USER',
  'Authorization': 'Bearer AUTHORIZATION_TOKEN',
  'Accept': 'application/json',
  'X-SourceID': 'WEB',
  'Content-Type': 'application/json'
}
conn.request("POST", "/rest/secure/angelbroking/historical/v1/getCandleData", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
    
 
Get Historical OI Data
Historical OI Data is available for live F&O contracts. Historical OI can be fetched using the token from the scrip master and passing it into the request body.

https://apiconnect.angelone.in/rest/secure/angelbroking/historical/v1/getOIData
Get OI Data Request
{
     "exchange": "NFO",
     "symboltoken": "46823",
     "interval": "THREE_MINUTE",
     "fromdate": "2024-06-07 09:15",
     "todate": "2024-06-07 15:30"
}
Get OI Data Response
{
     "status": true,
     "message": "SUCCESS",
     "errorcode": "",
     "data": [
          {
               "time": "2024-08-19T12:24:00+05:30",
               "oi": 166100
          }
     ]
}


import http.client

conn = http.client.HTTPSConnection("apiconnect.angelone.in")
payload = "{\r\n     \"exchange\": \"NFO\",\r\n    
 \"symboltoken\": \"46823\",\r\n     \"interval\": \"ONE_MINUTE\",\r\n  
    \"fromdate\": \"2021-02-08 09:00\",\r\n     \"todate\": \"2021-02-08 09:16\"\r\n}"
headers = {
  'X-PrivateKey': 'API_KEY',
  'Accept': 'application/json',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-UserType': 'USER',
  'Authorization': 'Bearer AUTHORIZATION_TOKEN',
  'Accept': 'application/json',
  'X-SourceID': 'WEB',
  'Content-Type': 'application/json'
}
conn.request("POST", "/rest/secure/angelbroking/historical/v1/getOIData", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
    
 WebSocket Streaming 2.0
Web Socket URL
Features
Request Headers for Authentication
Response Headers for Authentication Errors
Heartbeat message
Request Contract
JSON Request
Smaple
Field Description
Response Contract
Section-1) Payload
Section-2) Best Five Data
Error Response
Sample
Error Code
WebSocket URL
wss://smartapisocket.angelone.in/smart-stream
Features
Simplified and consistent request (JSON) and response (binary) structure.

Simplified heartbeat message and response.

Each client code (Angel One trading account id) can have up to three concurrent WebSocket connection

No need to kill the connection and reconnect for subscribing and unsubscribing. The existing open connection can be used to subs and unsubs in real-time

Any failure in subscription requests will not impact existing subscriptions and the client will continue to get the feed.

If the client sends an unsubs request for the tokens which are not subscribed then the system will gracefully ignore the request without impacting the feed for currently subscribed tokens

The total limit/quota of token subscriptions is 1000 per WebSocket session.

For example: If the client subscribes to Infosys NSE with LTP, Quote, and SnapQuote mode then this will be counted as 3 subscriptions.


Duplicate subscriptions to the same token and mode will be gracefully ignored and will not be counted towards the quota


The client will receive one tick per token_mode combination

For example: If the client subscribes to Infosys NSE with LTP, Quote, and SnapQuote mode then 1 tick will be published for each mode, containing respective fields.


The recommendation is to subscribe to one mode at a time for a token.


Request Headers for Authentication
Field	Mandatory	Description
Authorization	Yes	jwt auth token received from Login API
x-api-key	Yes	API key
x-client-code	Yes	client code (Angel Onetrading account id)
x-feed-token	Yes	feed token received fromLogin API

Response Headers for Authentication Errors
Field	Mandatory	Description	Valid Values
x-error-message	No	

Along with HTTP status code 401, the responseheader will contain textual description of why auth failed.

Invalid Header - Invalid Auth token

Invalid Header - Invalid Client Code

Invalid Header - Invalid API Key Invalid

Header - Invalid Feed Token

For Users using Browser Based clients for websocket
For users using browser based clients for websocket streaming, please append the query params in the url in the given format to make connection

wss://smartapisocket.angelone.in/smart-stream?clientCode=&feedToken=&apiKey=
Query Param	Mandatory	Description
clientCode	Yes	Angel One Client Code
feedToken	Yes	feedToken received in login response
apiKey	Yes	Your API Key

Note : Please note that all error handling and status codes will remain the same.


Heartbeat message
The client must send a heartbeat message for each WebSocket connection every 30 sec to keep the connection alive.

Heartbeat request (text):

ping

Heartbeat response (text):

pong

Request Contract
JSON Request

Sample
{
     "correlationID": "abcde12345",
     "action": 1,
     "params": {
          "mode": 1,
          "tokenList": [
               {
                    "exchangeType": 1,
                    "tokens": [
                         "10626",
                         "5290"
                    ]
               },
               {
                    "exchangeType": 5,
                    "tokens": [
                         "234230",
                         "234235",
                         "234219"
                    ]
               }
          ]
     }
}

Field Description
Field	Type	Mandatory (M) / Optional(O)	Description	Valid Values
correlationID	String	O	

A 10 character alphanumeric ID client may provide which will be returned by the server in error response to indicate which request generated error response.

Clients can use this optional ID for tracking purposes between request and corresponding error response.
action	Integer	M	

action

1 (Subscribe)

0 (Unsubscribe)
params	JSON Object	M		
mode	Integer	M	

Subscription Type as per this.

1 (LTP)

2 (Quote)

3 (Snap Quote)
tokenList[]	array of JSONObjects	M	

list of tokens per exchange
tokenList[].exchangeType	Integer	M	

exchange type

1 (nse_cm)

2 (nse_fo)

3 (bse_cm)

4 (bse_fo)

5 (mcx_fo)

7 (ncx_fo)

13 (cde_fo)
tokenList[].tokens	List of Strings	M	

tokens to subscribe.Refer Master Scrip for token by stock

Response Contract for LTP, Quote and Snap Quote mode
Response is in binary format with Little Endian byte order.


Section-1) Payload

Field	DataType	Size (in bytes)	Field Start Position(Index in Byte Array)	Description	Valid Values
1	Subscription Mode	byte/int8	1	0	

Subscription Type such as LTP, Quote, Snap Quote

1 (LTP)

2 (Quote)

3 (Snap Quote)
2	Exchange Type	byte/int8	1	1		

1 (nse_cm)

2 (nse_fo)

3 (bse_cm)

4 (bse_fo)

5 (mcx_fo)

7 (ncx_fo)

13 (cde_fo)
3	Token	byte array	25	2	

Token Id in characters encoded as byte array. One byte represents one utf-8 encoded character.

Null char signifies the end of characters i.e. \0000u in Java
4	Sequence Number	int64/long	8	27		
5	Exchange Timestamp	int64/long	8	35	

Exchange feed timestamp in epoch milliseconds
6	Last Traded Price (LTP)(If mode is ltp, the packet ends here.packet size = 51 bytes)	int32	8	43	

All prices are in paise. For currencies, the int 32 price values should be divided by 10000000.0 to obtain four decimal places. For everything else, the price values should be divided by 100.
7	Last traded quantity	int64/long	8	51		
8	Average traded price	int64/long	8	59		
9	Volume traded for the day	int64/long	8	67		
10	Total buy quantity	double	8	75		
11	Total sell quantity	double	8	83		
12	Open price of the day	int64/long	8	91		
13	High price of the day	int64/long	8	99		
14	Low price of the day	int64/long	8	107		
15	Close price(If mode is quote,the packet ends here.packet size = 123 bytes)	int64/long	8	115		
16	Last traded timestamp	int64/long	8	123		
17	Open Interest	int64/long	8	131		
18	Open Interest change % (this is a dummy field. contains garbage value)	double	8	139		
19	Best Five Data	Array containing 10 packets. Each packet having 20 bytes.	200	147	

sequence of best five buys data,followed by best five sells.(refer Section-2) Best Five Data)
20	Upper circuit limit		8	347		
21	Lower circuit limit		8	355		
22	52 week high price		8	363		
23	52 week low price(If mode is snapquote, the packet ends here. packet size = 379 bytes)		8	371		
NOTE - Sequence number for index feed is not available. please ignore the sequence number for index feed in the websocket response.


Section-2) Best Five Data

Field	DataType	Size (in bytes)	Field Start Position(Index in Byte Array)	Description	Valid Values
Buy/Sell Flag	int16	2	0	Flag to indicate whether this packet is for buy or sell data	

1 (buy)

0 (sell)
Quantity	int64	8	2	Buy/Sell Quantity	
Price	int64	8	10	Buy/Sell Price	
Number of Orders	int16	2	18	Buy/Sell Orders	


Error Response
Sample

{
     "correlationID": "abcde12345",
     "errorCode": "E1002",
     "errorMessage": "Invalid Request. Subscription Limit Exceeded"
}

Error Codes
Error Code	Error Message
E1001	Invalid Request Payload.
E1002	Invalid Request. Subscription Limit Exceeded.
NOTE:
Packet Received Time is a dummy value and will be deprecated soon.


Websocket Order Status
Websocket Order Status API will function in providing order status updates through websocket server connection and provide Order responses similar to the one received in Postback/Webhook. The connection can be made to the Websocket Server API using below url and input parameters.

To connect to the WebSocket, clients need to use the following URL:-

wss://tns.angelone.in/smart-order-update
In the WebSocket connection request, include the following Header key:-

Authorization: Bearer AUTHORIZATION_TOKEN
Please note that there is a connection limit for each user. Each client code is limited to 3 connections.
Initial Response: Upon successfully connecting to the WebSocket, you will receive an initial response in the following format:

{
     "user-id": "Your_client_code",
     "status-code": "200",
     "order-status": "AB00",
     "error-message": "",
     "orderData": {
          "variety": "",
          "ordertype": "",
          "ordertag": "",
          "producttype": "",
          "price": 0,
          "triggerprice": 0,
          "quantity": "0",
          "disclosedquantity": "0",
          "duration": "",
          "squareoff": 0,
          "stoploss": 0,
          "trailingstoploss": 0,
          "tradingsymbol": "",
          "transactiontype": "",
          "exchange": "",
          "symboltoken": "",
          "instrumenttype": "",
          "strikeprice": 0,
          "optiontype": "",
          "expirydate": "",
          "lotsize": "0",
          "cancelsize": "0",
          "averageprice": 0,
          "filledshares": "",
          "unfilledshares": "",
          "orderid": "",
          "text": "",
          "status": "",
          "orderstatus": "",
          "updatetime": "",
          "exchtime": "",
          "exchorderupdatetime": "",
          "fillid": "",
          "filltime": "",
          "parentorderid": ""
     }
}
The order-status field can have values like:
Sr. No	Status Code	Description
1	AB00	after-successful connection
2	AB01	open
3	AB02	cancelled
4	AB03	rejected
5	AB04	modified
6	AB05	complete
7	AB06	after market order req received
8	AB07	cancelled after market order
9	AB08	modify after market order req received
10	AB09	open pending
11	AB10	trigger pending
12	AB11	modify pending
Client Interaction:
The client application should periodically send a ping message to the server and expect a pong message from the server every 10 seconds. This helps check the liveliness of the WebSocket connection.

Sample Response:
Here's an example of a response you might receive from the WebSocket:

{
     "user-id": "Your_client_code",
     "status-code": "200",
     "order-status": "AB03",
     "error-message": "",
     "orderData": {
          "variety": "NORMAL",
          "ordertype": "LIMIT",
          "ordertag": "10007712",
          "producttype": "DELIVERY",
          "price": 551,
          "triggerprice": 0,
          "quantity": "1",
          "disclosedquantity": "0",
          "duration": "DAY",
          "squareoff": 0,
          "stoploss": 0,
          "trailingstoploss": 0,
          "tradingsymbol": "SBIN-EQ",
          "transactiontype": "BUY",
          "exchange": "NSE",
          "symboltoken": "3045",
          "instrumenttype": "",
          "strikeprice": -1,
          "optiontype": "",
          "expirydate": "",
          "lotsize": "1",
          "cancelsize": "0",
          "averageprice": 0,
          "filledshares": "0",
          "unfilledshares": "1",
          "orderid": "111111111111111",
          "text": "Adapter is Logged Off",
          "status": "rejected",
          "orderstatus": "rejected",
          "updatetime": "25-Oct-2023 23:53:21",
          "exchtime": "",
          "exchorderupdatetime": "",
          "fillid": "",
          "filltime": "",
          "parentorderid": ""
     }
}
Error Codes:
Sr. No	Error Code	Description
1	401	If the AUTHORIZATION_TOKEN is invalid, you will receive a 401 Response Code.
2	403	If the AUTHORIZATION_TOKEN is expired, you will receive a 403 Response Code.
3	429	If you breach the connection limit, you will receive a 429 Response Code.


nstruments
Request Type	Endpoint	Description
GET	https://margincalculator.angelone.in/OpenAPI_File/files/OpenAPIScripMaster.json	Retrieve the CSV dump of all tradable instruments
POST	https://apiconnect.angelone.in/order-service/rest/secure/angelbroking/order/v1/getLtpData	Retrieve LTP quotes for one or more instruments
GET	https://apiconnect.angelone.in/rest/secure/angelbroking/marketData/v1/nseIntraday	NSE Scrips Allowed for Intraday
GET	https://apiconnect.angelone.in/rest/secure/angelbroking/marketData/v1/bseIntraday	BSE Scrips Allowed for Intraday

Various kinds of instruments exist between multiple exchanges and segments that trade. Any application that facilitates trading needs to have a master list of these instruments. The instruments API provides a consolidated, import-ready CSV list of instruments available for trading.

Fetching the full instrument list
The instrument list API returns a gzipped CSV dump of instruments across all exchanges that can be imported into a database. The dump is generated once every day and hence last_price is not real time.

https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json

This is the only URL for fetching instrument data as below:.

[{“token":"2885","symbol":"RELIANCE-EQ","name":"RELIANCE","expiry":"","strike":"-1.000000","lotsize":"1","instrumenttype":"","exch_seg":"nse_cm","tick_size":"5.000000”}, …] 
Fetching LTP quotes for instrument
Note: Authorization header is mandatory here.

Request:
{
     "exchange": "NSE",
     "tradingsymbol": "SBIN-EQ",
     "symboltoken": "3045"
}
Response:
{
     "status": true,
     "message": "SUCCESS",
     "errorcode": "",
     "data": {
          "exchange": "NSE",
          "tradingsymbol": "SBIN-EQ",
          "symboltoken": "3045",
          "open": "18600",
          "high": "19125",
          "low": "18500",
          "close": "18780",
          "ltp": "19100"
     }
}

Fetching Token for Individual Scrips
Tokens of Individual scrips can be looked up by the use of Search Scrip API.

https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/searchScrip

Note: Please note that only one Scrip is permitted per request.

Request:
{
     "exchange": "NSE",
     "searchscrip": "SBIN"
}
Response:
{
     "status": true,
     "message": "SUCCESS",
     "errorcode": "",
     "data": [
          {
               "exchange": "NSE",
               "tradingsymb{ol": "SBIN-AF",
               "symboltoken": "11128"
          },
          {
               "exchange": "NSE",
               "tradingsymbol": "SBIN-BE",
               "symboltoken": "4884"
          },
          {
               "exchange": "NSE",
               "tradingsymbol": "SBIN-BL",
               "symboltoken": "12740"
          },
          {
               "exchange": "NSE",
               "tradingsymbol": "SBIN-EQ",
               "symboltoken": "3045"
          },
          {
               "exchange": "NSE",
               "tradingsymbol": "SBIN-IQ",
               "symboltoken": "28450"
          },
          {
               "exchange": "NSE",
               "tradingsymbol": "SBIN-RL",
               "symboltoken": "16382"
          },
          {
               "exchange": "NSE",
               "tradingsymbol": "SBIN-U3",
               "symboltoken": "22351"
          },
          {
               "exchange": "NSE",
               "tradingsymbol": "SBIN-U4",
               "symboltoken": "22353"
          }
     ]
}

CSV response columns
Column	Description
exchange_tokenstring	The numerical identifier issued by the exchange representing the instrument.
tradingsymbolstring	Exchange tradingsymbol of the instrument
namestring	Name of the company (for equity instruments)
expirystring	Expiry date (for derivatives)
strikefloat	Strike (for options)
tick_sizefloat	Value of a single price tick
lot_sizeint	Quantity of a single lot
instrument_typestring	EQ, FUT, CE, PE
PythonNodeJsJavaRGO

import http.client
import mimetypes
conn = http.client.HTTPSConnection(
    "apiconnect.angelone.in"
    )
payload = "{\n     \"exchange\": \"NSE\",\n 
    \"tradingsymbol\": \"SBIN-EQ\",\n     
    \"symboltoken\": \"3045\"\n}"
headers = {
  'Authorization': 'Bearer AUTHORIZATION_TOKEN',
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-UserType': 'USER',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-PrivateKey': 'API_KEY'
}
conn.request("POST", 
"/order-service/rest/secure/angelbroking/order/
v1/getLtpData", 
payload, 
headers)

res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
Scrips Allowed for Intraday trading
To find out which of the scrips are allowed for Intraday trading along with their respective multipliers for margin trading, you can use the following APIs.

For NSE
https://apiconnect.angelone.in/rest/secure/angelbroking/marketData/v1/nseIntraday

Response:
{
     "status": true,
     "message": "SUCCESS",
     "errorcode": "",
     "data": [
          {
               "Exchange": "NSE",
               "SymbolName": "CHEMPLASTS",
               "Multiplier": "5.0"
          },
          {
               "Exchange": "NSE",
               "SymbolName": "SANGHVIMOV",
               "Multiplier": "5.0"
          }
     ]
}

For BSE
https://apiconnect.angelone.in/rest/secure/angelbroking/marketData/v1/bseIntraday

Response:
{
     "status": true,
     "message": "SUCCESS",
     "errorcode": "",
     "data": [
          {
               "Exchange": "BSE",
               "SymbolName": "TAALENT",
               "Multiplier": "1.0"
          },
          {
               "Exchange": "BSE",
               "SymbolName": "ARE&M",
               "Multiplier": "5.0"
          }
     ]
}


import http.client
import mimetypes
conn = http.client.HTTPSConnection(
    " apiconnect.angelone.in "
    )
payload = ''
headers = {
  'Authorization': 'Bearer AUTHORIZATION_TOKEN',
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-UserType': 'USER',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-PrivateKey': 'API_KEY'
}
conn.request("GET", 
"/rest/secure/angelbroking/marketData/v1/nseIntraday", 
payload, 
headers)

res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))