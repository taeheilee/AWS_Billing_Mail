import json
import datetime
# 라이브러리 및 AWS 자격 증명 설정: 코드의 첫 부분에서는 필요한 라이브러리를 가져오고, AWS 자격 증명 (액세스 키, 시크릿 키) 및 리전을 설정

access_key=''
secret_key=''
region=''

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# 필요한 패키지 목록
required_packages = ['json', 'boto3', 'pandas']


def main(self):

    # 패키지 설치 함수 호출
    for package in required_packages:
    install(package)

    import boto3
    from botocore.exceptions import ClientError
    import pandas as pd

     
    # AWS의 Cost Explorer 서비스를 사용하기 위해 boto3.client('ce', ...)를 사용하여 클라이언트를 생성
    billing_client = boto3.client('ce',
                                  aws_access_key_id=access_key,
                                  aws_secret_access_key=secret_key)
     
    # 날짜(yyyy-MM-dd)를 가져와 문자열로 변환
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days = 1) 
    str_today = str(today) 
    str_yesterday = str(yesterday)
     
    # 전날의 총 비용을 파씽
    response_total = billing_client.get_cost_and_usage( 
       TimePeriod={ 
         'Start': str_yesterday,
         'End': str_today,
         #'Start': "2023-05-16",
        # 'End': "2023-05-17"
         },
       Granularity='DAILY', 
       Metrics=[ 'UnblendedCost',] 
    )
     
    total_cost = response_total["ResultsByTime"][0]['Total']['UnblendedCost']['Amount']
    print(total_cost)
    total_cost=float(total_cost)
    total_cost=round(total_cost, 3)
    total_cost = '$' + str(total_cost)
     
    # 총 비용
    print('Total cost for yesterday: ' + total_cost)
     
    # 개별 리소스에 대한 자세한 청구 받기
    response_detail = billing_client.get_cost_and_usage(
        TimePeriod={
           'Start': str_yesterday,
           'End': str_today,
        },
        Granularity='DAILY',
        Metrics=['UnblendedCost'],
        GroupBy=[
            {
                'Type': 'DIMENSION',
                'Key': 'SERVICE'
            },
            {
                'Type': 'DIMENSION',
                'Key': 'USAGE_TYPE'
            }
        ]
    )

     # 개별 리소스 비용 가공 및 출력: 리소스별로 비용을 가공하고, 이를 데이터프레임으로 변환하여 출력
    resources = {'Service':[],'Usage Type':[],'Cost':[]}
     
    for result in response_detail['ResultsByTime'][0]['Groups']:
        group_key = result['Keys']
        service = group_key[0]
        usage_type = group_key[1]
        cost = result['Metrics']['UnblendedCost']['Amount']
        cost=float(cost)
        cost=round(cost, 3)
         
        if cost > 0:
            cost = '$' + str(cost)
            resources['Service'].append(service)
            resources['Usage Type'].append(usage_type)
            resources['Cost'].append(cost)
             
    df = pd.DataFrame(resources)
    html_table = df.to_html(index=False)
             
    print(resources)        
     
    message = '익일 AWS 테스트 계정 비용' 

     # 이메일 보고서 작성 및 전송: 특정 포맷의 HTML 이메일 보고서를 작성하고, Amazon SES를 사용하여 해당 보고서를 지정된 이메일 주소로 전송
    html = """
            <html>
              <head>
                <style>
                  body {{
                    font-family: Arial, sans-serif;
                    color: white;
                    background-color: black;
                  }}
                  h2 {{
                    color: white;
                    font-size: 25px;
                    text-align: center;
                  }}
                  h1 {{
                    color: #333333;
                    font-size: 40px;
                    text-align: center;
                    background-color: yellow;
                  }}
                  p {{
                    color: white;
                    font-size: 30px;
                    line-height: 1.5;
                    margin-bottom: 20px;
                    text-align: center;
                  }}
                  p1 {{
                     font-size: 10px;
                     text-align: center;
                      margin-left: auto;
                     margin-right: auto;
                  }}
                </style>
              </head>
              <body>
                <p> 테스트 계정 비용 보고서 {} </p>
                <h2> {} </h2>
                <h1> <strong> <em> 합계: {} </em></strong> </h1>
                <p1>{}</p1>
              </body>
            </html>
            """.format(str_yesterday,message,total_cost,html_table)
             
 
     
    ses_client = boto3.client('ses', 
                              region_name=region, 
                              aws_access_key_id=access_key,
                              aws_secret_access_key=secret_key)
     
    message = {
        'Subject': {'Data': 'AWS training account cost report'},
        'Body': {'Html': {'Data': html}}
    }
     
    
    try:
      response = ses_client.send_email(
        Source="sender@mail.com",
        Destination={'ToAddresses': ["receiver@mail.com"]},
        Message=message
    )
      print("이메일 발송 성공! 메시지 ID:", response['MessageId'])
    except Exception as e:
      print("이메일 발송 오류:", str(e))

     # 주간 비용 보고서 생성 및 전송 (금요일에만 실행): today.weekday()를 사용하여 현재 요일이 금요일인 경우에만 주간 비용
    if today.weekday() == 4:
        print('week')
        week = today - datetime.timedelta(days = 7) 
        str_week = str(week)
         
        response_total = billing_client.get_cost_and_usage( 
           TimePeriod={ 
             'Start': str_week, 
             'End': str_today }, 
           Granularity='MONTHLY', 
           Metrics=[ 'UnblendedCost',] 
        )
         
        print(response_total)
        length=len(response_total["ResultsByTime"])
        print(length)

         # 주간 비용 보고서 생성 로직: 금요일인 경우, 지난 주의 총 비용을 계산하고, 해당 주의 각 리소스에 대한 비용을 세부적으로 가져와 합산
        if (length==2):
            total_cost_1 = response_total["ResultsByTime"][0]['Total']['UnblendedCost']['Amount']
            total_cost_2 = response_total["ResultsByTime"][1]['Total']['UnblendedCost']['Amount']
            total_cost_1=float(total_cost_1)
            total_cost_2=float(total_cost_2)
            total_cost = total_cost_1+total_cost_2
            total_cost=round(total_cost, 3)
            total_cost = '$' + str(total_cost)
             
            # 주간 비용 출력 및 데이터 가공: 주간 총 비용을 출력하고, 각 리소스에 대한 주간 비용을 세부적으로 가공하여 데이터프레임으로 변환
            print('Total cost for the week: ' + total_cost)
             
            # 개별 리소스에 대한 자세한 청구 받기
            response_detail = billing_client.get_cost_and_usage(
                TimePeriod={
                    'Start': str_week,
                    'End': str_today
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    },
                    {
                        'Type': 'DIMENSION',
                        'Key': 'USAGE_TYPE'
                    }
                ]
            )
             
            resources = {'Service':[],'Usage Type':[],'Cost':[]}
            resources_1 = {'Service':[],'Usage Type':[],'Cost':[]}
             
            for result in response_detail['ResultsByTime'][0]['Groups']:
                group_key = result['Keys']
                service = group_key[0]
                usage_type = group_key[1]
                cost = result['Metrics']['UnblendedCost']['Amount']
                cost=float(cost)
                cost=round(cost, 3)
                 
                if cost > 0:
                    cost = '$' + str(cost)
                    resources['Service'].append(service)
                    resources['Usage Type'].append(usage_type)
                    resources['Cost'].append(cost)
                     
            for result in response_detail['ResultsByTime'][1]['Groups']:
                group_key = result['Keys']
                service = group_key[0]
                usage_type = group_key[1]
                cost = result['Metrics']['UnblendedCost']['Amount']
                cost=float(cost)
                cost=round(cost, 3)
 
                if cost > 0:
                    cost = '$' + str(cost)
                    resources_1['Service'].append(service)
                    resources_1['Usage Type'].append(usage_type)
                    resources_1['Cost'].append(cost)
             
             # 주간 비용 데이터 병합: 전날과 이번 주의 리소스별 비용 데이터를 병합        
            for key, value in resources_1.items():
                if key in resources:
                    resources[key] += value
                else:
                    resources[key] = value
        else:
            total_cost = response_total["ResultsByTime"][0]['Total']['UnblendedCost']['Amount']
            total_cost=float(total_cost)
            total_cost=round(total_cost, 3)
            total_cost = '$' + str(total_cost)
             
            # 총 비용
            print('이번주 총 비용: ' + total_cost)
             
            # 개별 리소스에 대한 자세한 청구 받기
            response_detail = billing_client.get_cost_and_usage(
                TimePeriod={
                    'Start': str_week,
                    'End': str_today
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    },
                    {
                        'Type': 'DIMENSION',
                        'Key': 'USAGE_TYPE'
                    }
                ]
            )
             
            resources = {'Service':[],'Usage Type':[],'Cost':[]}
             
            for result in response_detail['ResultsByTime'][0]['Groups']:
                group_key = result['Keys']
                service = group_key[0]
                usage_type = group_key[1]
                cost = result['Metrics']['UnblendedCost']['Amount']
                cost=float(cost)
                cost=round(cost, 3)
                 
                if cost > 0:
                    cost = '$' + str(cost)
                    resources['Service'].append(service)
                    resources['Usage Type'].append(usage_type)
                    resources['Cost'].append(cost)
                     
        print(type(resources))
                 
        df = pd.DataFrame(resources)
        html_table = df.to_html(index=False)
                 
        print(resources)        
        # 이메일 보고서 작성 및 전송 (주간): 주간 비용에 대한 이메일 보고서를 작성하고 이메일로 전송 
        message = '주간 AWS 테스트 계정 비용' 
         
        html = """
                <html>
                  <head>
                    <style>
                      body {{
                        font-family: Arial, sans-serif;
                        color: white;
                        background-color: black;
                      }}
                      h2 {{
                        color: white;
                        font-size: 25px;
                        text-align: center;
                      }}
                      h1 {{
                        color: #333333;
                        font-size: 40px;
                        text-align: center;
                        background-color: yellow;
                      }}
                      p {{
                        color: white;
                        font-size: 30px;
                        line-height: 1.5;
                        margin-bottom: 20px;
                        text-align: center;
                      }}
                      p1 {{
                         font-size: 10px;
                         text-align: center;
                          margin-left: auto;
                         margin-right: auto;
                      }}
                    </style>
                  </head>
                  <body>
                    <p> 이번 주 테스트 계정 비용 보고서 {} and {} </p>
                    <h2> {} </h2>
                    <h1> <strong> <em> 합계: {} </em></strong> </h1>
                    <p1>{}</p1>
                  </body>
                </html>
                """.format(str_week,str_today,message,total_cost,html_table)
                      
        ses_client = boto3.client('ses', region_name=region,
                                  aws_access_key_id=access_key,
                                  aws_secret_access_key=secret_key)
         
        message = {
            'Subject': {'Data': 'AWS training account cost report'},
            'Body': {'Html': {'Data': html}}
        }
         
        response = ses_client.send_email(
            Source='sender@mail.com',
            Destination={'ToAddresses': [ 'receiver@mail.com']},
            Message=message
        )
         
        print(response)
