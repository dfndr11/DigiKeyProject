import requests
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
import time

#                                                     CHANGE THESE
server = 'ANTHONYDESKTOP\MSSQLSERVER01'
database = 'DigikeyData'
client_secret = "CHANGE_THIS (Must be through an Organization not Sandbox)"
client_id = "CHANGE_THIS (Must be through an Organization not Sandbox)"
suggested_parts_input = ["175-MAX1258EVC16-ND", "102-CPT-2745-L100-ND"]
product_change_notifications_input = ["609-4647-ND", "AUIPS2051LTR-ND", "495-1789-2-ND", "175-MAX1258EVC16-ND"]  # Must be DigiKey Part Number


DB = {'servername': server, 'database': database, 'driver': 'SQL Server Native Client 11.0'}
engine = create_engine('mssql+pyodbc://' + DB['servername'] + '/' + DB['database'] + '?driver=' + DB['driver'])

DigiKeyDataExcel = pd.read_excel(r'C:\Users\antho\PycharmProjects\DigikeyProject\DigikeyData.xlsx')

query = '''    select * from DigikeyData.dbo.DigikeyData    '''
sql_data = pd.read_sql(query, engine)

refresh_token = str(DigiKeyDataExcel["refresh_token"][0])
access_token = str(DigiKeyDataExcel["access_token"][0])


# ----------------------------------------------------------------------------------------------------------------------


def getNewToken():                           # Gets a new access token (expires every 30 min)
    refresh_params = {
        "client_secret": client_secret,
        "client_id": client_id,
        "refresh_token": str(DigiKeyDataExcel["refresh_token"][0]),
        "grant_type": "refresh_token"
    }
    response = requests.post("https://api.digikey.com/v1/oauth2/token", data=refresh_params)
    print(response)
    responseData = response.json()
    print(responseData)
    print("----")
    data = {
        "client_secret": [client_secret],
        "client_id": [client_id],
        "refresh_token": [str(responseData["refresh_token"])],
        "access_token": [str(responseData["access_token"])]
    }
    print(data)
    temp_dataframe = pd.DataFrame(data)
    print(temp_dataframe)

    ExcelExport = pd.ExcelWriter("DigikeyData.xlsx")
    temp_dataframe.to_excel(ExcelExport)
    ExcelExport.save()
    temp_dataframe.to_sql('DigikeyData', con=engine, if_exists='replace', schema='dbo', index=False,
                          chunksize=5000)


def getSuggested(part_num):            # Gets the suggested products of a certain product
    DigiKeyDataExcel = pd.read_excel(r'C:\Users\antho\PycharmProjects\DigikeyProject\DigikeyData.xlsx')
    part_number = part_num
    print(part_number)
    params = {
        "X-DIGIKEY-Client-Id": client_id,
        "Authorization": "Bearer " + str(DigiKeyDataExcel["access_token"][0]),
        "DigiKeyPartNumber": part_number
    }
    response = requests.get("https://api.digikey.com/Search/v3/Products/"+params["DigiKeyPartNumber"]+"/WithSuggestedProducts", headers=params)
    print(response)
    data = response.json()
    print(data)
    print(data["SuggestedProducts"])
    product_dataframe = pd.DataFrame()
    product_dict = {
        "OriginalProductPartNumber": part_number,
        "OriginalBoolean": "True"
    }
    for y in data["Product"]:  # For each object in the main product
        print(type(y))
        print(type(data["Product"][y]))
        print(y)
        if type(y) == str and type(data["Product"][y]) != list and type(
                data["Product"][y]) != dict:
            product_dict[y] = str(data["Product"][y])
        elif type(data["Product"][y]) == dict and y != 'LimitedTaxonomy':
            for key, value in data["Product"][y].items():
                print(key, value)
                product_dict[str(y) + "_" + str(key)] = str(value)
    product_details_dict_no_lists = product_dict
    product_parameters_list = data["Product"]["Parameters"]
    product_standardpricing_list = data["Product"]["StandardPricing"]
    Max = max(len(product_parameters_list), len(product_standardpricing_list))
    for y in range(Max):
        if y < len(product_parameters_list):
            for key, value in product_parameters_list[y].items():
                product_details_dict_no_lists["Parameters_" + str(key)] = str(value)
        if y < len(product_standardpricing_list):
            for key, value in product_standardpricing_list[y].items():
                product_details_dict_no_lists["StandardPricing_" + str(key)] = str(value)
        product_dataframe = product_dataframe.append(product_details_dict_no_lists, ignore_index=True)

    suggested_dataframe = pd.DataFrame()
    for x in range(len(data["SuggestedProducts"])):  # for each suggested product returned
        suggested_dict = {
            "OriginalProductPartNumber": part_number
        }
        for y in data["SuggestedProducts"][x]:  # For each object in the current product
            print(type(y))
            print(type(data["SuggestedProducts"][x][y]))
            print(y)
            if type(y) == str and type(data["SuggestedProducts"][x][y]) != list and type(data["SuggestedProducts"][x][y]) != dict:
                suggested_dict[y] = str(data["SuggestedProducts"][x][y])
            elif type(data["SuggestedProducts"][x][y]) == dict:
                for key, value in data["SuggestedProducts"][x][y].items():
                    print(key, value)
                    suggested_dict[str(y) + "_" + str(key)] = str(value)
        details_dict_no_lists = suggested_dict
        parameters_list = data["SuggestedProducts"][x]["Parameters"]
        standardpricing_list = data["SuggestedProducts"][x]["StandardPricing"]
        Max = max(len(parameters_list), len(standardpricing_list))
        for y in range(Max):
            if y < len(parameters_list):
                for key, value in parameters_list[y].items():
                    details_dict_no_lists["Parameters_" + str(key)] = str(value)
            if y < len(standardpricing_list):
                for key, value in standardpricing_list[y].items():
                    details_dict_no_lists["StandardPricing_" + str(key)] = str(value)
            suggested_dataframe = suggested_dataframe.append(details_dict_no_lists, ignore_index=True)
    suggested_dataframe = suggested_dataframe.sort_index(axis=1)

    final_dataframe = pd.DataFrame()
    final_dataframe = final_dataframe.append(product_dataframe, ignore_index=True)
    final_dataframe = final_dataframe.append(suggested_dataframe, ignore_index=True)
    final_dataframe = final_dataframe.sort_index(axis=1)

    now = datetime.now()
    dt_string = str(now.strftime("_%d/%m/%Y_%H:%M:%S"))
    print("date and time =", dt_string)
    #suggested_dataframe.to_sql('SuggestedProductsInfo_' + str(part_num) + dt_string, con=engine, if_exists='replace', schema='dbo', index=False, chunksize=5000)
    return final_dataframe


def getChanges(num):                       # Gets the PCN of a product
    query = '''    select * from DigikeyData.dbo.DigikeyData    '''
    sql_data = pd.read_sql(query, engine)

    DigiKeyDataExcel = pd.read_excel(r'C:\Users\antho\PycharmProjects\DigikeyProject\DigikeyData.xlsx')
    params = { # 175-MAX1258EVC16-ND
        "X-DIGIKEY-Client-Id": client_id,
        "Authorization": "Bearer " + str(sql_data["access_token"][0]),  # 102-1130-ND
        "DigiKeyPartNumber": num
    }
    try:
        response = requests.get("https://api.digikey.com/ChangeNotifications/v3/Products/" + params["DigiKeyPartNumber"], headers=params)
        print(response)
        data = response.json()
        print(data)
        df = pd.DataFrame()
        dict = {}
        for x in data["ProductChangeNotifications"]:
            for key, value in x.items():
                dict[str(key)] = value
            df = df.append(dict, ignore_index=True)
        return df
    except:
        print("An error occurred while getting PCN for this product")


def getDetails(num):                       # Gets product information of a certain product
    query = '''    select * from DigikeyData.dbo.DigikeyData    '''
    sql_data = pd.read_sql(query, engine)

    DigiKeyDataExcel = pd.read_excel(r'C:\Users\antho\PycharmProjects\DigikeyProject\DigikeyData.xlsx')
    params = {
        "X-DIGIKEY-Client-Id": client_id,
        "Authorization": "Bearer " + str(sql_data["access_token"][0]),  # 102-1130-ND
        "DigiKeyPartNumber": num
    }
    response = requests.get("https://api.digikey.com/Search/v3/Products/" + params["DigiKeyPartNumber"], headers=params)
    print(response)
    data = response.json()
    print(data)


def getNewCodes():              # This is used for the initial OAuth2 to set up the project
    params = {
        "client_secret": client_secret,
        "client_id": client_id,
        "code": "",  # Get this from the redirect url in the browser
        "redirect_uri": "https://www.google.com/",
        "grant_type": "authorization_code"
    }

    response = requests.post("https://api.digikey.com/v1/oauth2/token", data=params)
    print(response)
    print(response.json())


# ----------------------------------------------------------------------------------------------------------------------


getNewToken()  # Automated sequence
suggested_df = pd.DataFrame()
for x in suggested_parts_input:
    suggested_df = suggested_df.append(getSuggested(str(x)), ignore_index=True)
ExcelExport = pd.ExcelWriter("SuggestedProductsInfo.xlsx")
suggested_df.to_excel(ExcelExport)
ExcelExport.save()
suggested_df.to_sql('SuggestedProducts_Results', con=engine, if_exists='replace', schema='dbo', index=False, chunksize=5000)
print("---")
print("Getting PCN...")
print("---")
pcn_df = pd.DataFrame()
for x in product_change_notifications_input:
    pcn_df = pcn_df.append(getChanges(str(x)), ignore_index=True)
ExcelExport = pd.ExcelWriter("PCN_Info.xlsx")
pcn_df.to_excel(ExcelExport)
ExcelExport.save()
pcn_df.to_sql('PCN_Results', con=engine, if_exists='replace', schema='dbo', index=False, chunksize=5000)


"""while True:  # Testing sequence
    user_input = input("COMMAND:")
    if "getNewToken" in user_input:
        getNewToken()
    elif "getChanges" in user_input:
        num = input("Part Number:")
        getChanges(num)
    elif "getSuggested" in user_input:
        num = input("Part Number:")
        getSuggested(num)
    elif "getDetails" in user_input:
        num = input("Part Number:")
        getDetails(num)
    elif "getNewCodes" in user_input:
        getNewCodes()"""