import requests
import time
import openpyxl
import datetime
import sys
import os
import json
import pandas as pd
from decimal import Decimal

Adress= "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8" # ETH USDC Ethereum

def getUnixTime():
    timeArray = time.localtime(fromdate)
    unixTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)

    return(unixTime)

def task(Adress, startTime, endTime):

    fromdate = int(startTime.timestamp()) # 轉成時間戳 1620176400
    lastdate = int(endTime.timestamp())   # 轉成時間戳 1620216000
    print(f"fromdate:{fromdate}")
    print(f"lastdate:{lastdate}")

    # Making a get request 
    request_url='https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'
    
    query = '''
        query
        {
            poolHourDatas(
                where:{
                    pool:"'''+str(Adress)+'''",
                    periodStartUnix_gte:'''+str(fromdate)+''',
                    periodStartUnix_lte:'''+str(lastdate)+''',
                   
                },
                orderBy:periodStartUnix,
                orderDirection:asc
                
            )
            {
                periodStartUnix
                liquidity
                open
                high
                low
                close
                pool{
                    totalValueLockedUSD
                    totalValueLockedToken0
                    totalValueLockedToken1
                    token0
                        {decimals
                        }
                    token1
                        {decimals
                        }
                    }
                feeGrowthGlobal0X128
                feeGrowthGlobal1X128
    
            }
        }
    '''

    request_headers = {
        'Content-Type': 'application/json'
    }

    data = {
        'query': query
    }

    #print(f'request ========== Start Time : {startTime} end Time : {endTime} \n')


    try:
        response  = requests.post(request_url, headers=request_headers, data=json.dumps(data))

        if response.status_code == 200:

            # 解析查询结果
            result = json.loads(response.text)
            
            pair_hour_datas = result['data']['poolHourDatas']
            #for item in pair_hour_datas:
            #    date = item['periodStartUnix']
            #    volumeUSD = item['pool']['volumeUSD']
            #    tvlUSD = item['pool']['totalValueLockedUSD']
            #    collectedFeesUSD = item['pool']['collectedFeesUSD']
            #    feeGrowthGlobal0X128 = item['feeGrowthGlobal0X128']
            #    feeGrowthGlobal1X128 = item['feeGrowthGlobal1X128']
            #    print(f'Date: {date}, Volume USD: {volumeUSD}, tvl USD: {tvlUSD}, feeGrowthGlobal0X128: {feeGrowthGlobal0X128} \n')
            
            
            dpd = pd.json_normalize(pair_hour_datas)
         
            '''
            dpd['date'] = pd.to_datetime(dpd['periodStartUnix'], unit='s')
            
            decimal0 = int(dpd['pool.token0.decimals'].iloc[0])
            decimal1 = int(dpd['pool.token1.decimals'].iloc[0])
            decimal = decimal1 - decimal0

            # Convert the columns to numeric values
            dpd['fg0'] = ((dpd['feeGrowthGlobal0X128'].apply(lambda x: Decimal(x)) / (2 ** 128)) / (10 ** decimal0))
            dpd['fg1'] = ((dpd['feeGrowthGlobal1X128'].apply(lambda x: Decimal(x)) / (2 ** 128)) / (10 ** decimal1))
            
            #Calculate F0G and F1G (fee earned by an unbounded unit of liquidity in one period)
            
            dpd['fg0shift'] = (dpd['fg0'].shift(-1))
            dpd['fg1shift'] = (dpd['fg1'].shift(-1))
            
            dpd['fee0token'] = (dpd['fg0'] - dpd['fg0shift'])
            dpd['fee1token'] = (dpd['fg1'] - dpd['fg1shift'])

            dpd['fg0'] = dpd['fg0'].apply(lambda x: format(x, '.18f'))  # 格式化为18位小数的字符串
            dpd['fg1'] = dpd['fg1'].apply(lambda x: format(x, '.18f'))

            dpd['fg0shift'] = dpd['fg0shift'].apply(lambda x: format(x, '.18f'))
            dpd['fg1shift'] = dpd['fg1shift'].apply(lambda x: format(x, '.18f'))
            
            dpd['fee0token'] = dpd['fee0token'].apply(lambda x: format(x, '.18f'))
            dpd['fee1token'] = dpd['fee1token'].apply(lambda x: format(x, '.18f'))
            '''
            return dpd
        else:
            # Handle error if the API request was not successful
            print("Rresponse Error: Failed to fetch data from the API")
            return None

    except Exception as e:
        print('\n==== Exception {0} : {1}'.format('[task]', e))
        return None

def main_func():
    fileName = (f"uniswap_backtest_subgraph.csv")

    # 檢查檔案是否存在 
    if os.path.isfile(fileName):
        # 檔案存在 從最後一筆期數接繼抓取
        existing_data = pd.read_csv(fileName)
        last_date = existing_data['periodStartUnix'].iloc[-1]
        last_datetime = datetime.datetime.fromtimestamp(last_date) + datetime.timedelta(hours=1)
        startTime = last_datetime
    else:
        startTime = datetime.datetime(2021, 6, 1, 0, 0, 0)

    delta = datetime.timedelta(days=0, hours=23)
    endTime =  startTime + delta
    stopTime = datetime.datetime(2023, 8, 30, 23, 00, 00)


    count = 0
    flag = True
    
    while flag:

            #if(count > 2 ):
            #    flag = False
            #    break


            if(stopTime >= startTime):
                if(stopTime < endTime):
                    endTime = stopTime

                count += 1
                print('\n=====================================================')
                print('startTime : ' + startTime.strftime('%Y-%m-%d %H:%M:%S'))
                print('endTime   : ' + endTime.strftime('%Y-%m-%d %H:%M:%S'))

                dpd = task(Adress, startTime, endTime)

                if dpd is not None:
                # 檢查檔案是否存在
                    if os.path.isfile(fileName):
                        
                        existing_data = pd.read_csv(fileName)

                        last_date = existing_data['periodStartUnix'].iloc[-1]
                        last_datetime = datetime.datetime.fromtimestamp(last_date) + datetime.timedelta(hours=1)

                        first_period_start_unix = dpd['periodStartUnix'].iloc[0]

                        if last_datetime != datetime.datetime.fromtimestamp(first_period_start_unix):
                            print("有跳期的狀況 ==== \n")
                            print(dpd)
                            print("========= \n")
                            #flag = False
                            #break


                        last_index = existing_data.index[-1] if not existing_data.empty else -1
                         
                        # Append data with adjusted index
                        dpd.index += last_index + 1
                        dpd.to_csv(fileName, mode='a', header=False)

                    else:
                        
                        dpd.to_csv(fileName, index=True)                
                        print(f"檔案不存在 建立新檔 {fileName} (added {dpd.shape[0]} rows) \n" )



                    startTime = endTime + datetime.timedelta(hours=1)
                    endTime =  startTime + delta
                    
                    time.sleep(1)
                else:
                    print(f"沒有抓到資料 \n" )
                    flag = False
            else:
                print('\n=====================================================')

                print('stopTime : ' + stopTime.strftime('%Y-%m-%d %H:%M:%S'))

                print(f"資料已抓完 stop \n" )
                flag = False

main_func()

