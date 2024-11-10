import requests
import boto3
import json
import os

client = boto3.client('sqs', region_name='us-west-2')
sns = boto3.client('sns', region_name='us-west-2')
queue_url = os.environ.get("SQS_QUEUE_URL")
env = os.environ.get("ENVIRONMENT", "dev")
print(f"Cellborg Troop - QC Python container running in {env} environment")
if env == "dev":
    SNS_TOPIC = 'arn:aws:sns:us-west-2:865984939637:QCCompleteTopic'
else:
    SNS_TOPIC = f'arn:aws:sns:us-west-2:865984939637:QCComplete-{env}-Topic'

def send_sns(data):
    topic_arn = SNS_TOPIC
    print(f'Sending {data} SNS message to {SNS_TOPIC}')
    response = sns.publish(
        TopicArn = topic_arn,
        Message = json.dumps(data),
    )
    return response

def send_request(endpoint, data):
    url = f"http://127.0.0.1:8001{endpoint}"  # Replace with the actual IP address of container host
    response = requests.post(url, json = data, headers = {'Content-Type': 'application/json'})
    return response.json()

def send_shutdown_request():
    url = f"http://127.0.0.1:8001/shutdown"
    try:
        response = requests.post(url, json = {"status": "complete"}, headers = {'Content-Type': 'application/json'})
        response.raise_for_status()
    except requests.ConnectionError:
        print("Connection was closed by the server (expected behavior during shutdown).")
    except requests.RequestException as e:
        print(f"An error occurred: {e}")

#timeout setting
MAX_COUNT = 1000
currentCount=0

#polling loop
while True:
    
    response = client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=10, VisibilityTimeout=900)
    print("queueurl=",queue_url)
    print(response)

    #timeout check
    if currentCount>= MAX_COUNT:
        print("Server has hit timeout, shutting down...")
        send_shutdown_request()

    if 'Messages' not in response:
        print("No Message in ",queue_url, "topic:",SNS_TOPIC)
        currentCount+=1
        if currentCount%10==0:
            print(currentCount)
        continue
    
    for message in response['Messages']:
        
        try:
            queen_service_request_raw_data = message['Body']
            queen_service_request = json.loads(queen_service_request_raw_data)
            print(queen_service_request)
            request_type = queen_service_request["requestType"]
            project = queen_service_request["project"]
            user = queen_service_request["user"]

            #preplot qc
            if request_type == "QCPrePlot":
                
                dataset = queen_service_request["dataset"]
                species_mt = queen_service_request["mt"]
                qc_request = {
                    "user": user, 
                    "project": project, 
                    "dataset": dataset,
                    "mt": species_mt
                }            
                print("Sending QC request...",qc_request)
                #send pre-plot request to QCApi
                response = send_request('/qc_metrics', qc_request)
                print(response)
                if response['success']:
                    print("QC Pre-Plot Successful... Sending SNS message to clear dataset as completed...")
                    
                    # Send SNS message
                    data = {
                        "stage": "prePlot",
                        "user": user, 
                        "project": project, 
                        "dataset": dataset,
                        "complete": True
                     
                    } 
                    response = send_sns(data)
                    print(response)
                else:
                    print(f"Error in QC: {response.get('message')}")

            #doublet request
            elif request_type == "QCDoublet":
                dataset = queen_service_request["dataset"]
                countMax = queen_service_request["countMax"]
                countMin = queen_service_request["countMin"]
                geneMax = queen_service_request["geneMax"]
                geneMin = queen_service_request["geneMin"]
                mitoMax = queen_service_request["mitoMax"]
                mitoMin = queen_service_request["mitoMin"]

                qc_request = {
                    "user": user, 
                    "project": project, 
                    "dataset": dataset,
                    "countMax":countMax,
                    "countMin":countMin,
                    "geneMax":geneMax,
                    "geneMin":geneMin,
                    "mitoMax":mitoMax,
                    "mitoMin":mitoMin
                }  
                print("Sending QC request...",qc_request)
                #send qc doublet request to qc doublet endpoint
                response = send_request('/qc_doublets', qc_request)
                print(response)
                if response['success']:
                    print("QC Doublet Successful... Sending SNS message to clear dataset as completed...")
                    
                    # Send SNS message
                    data = {
                        "stage": "doublet",
                        "user": user, 
                        "project": project, 
                        "dataset": dataset,
                        "complete": True
                     
                    } 
                    response = send_sns(data)
                    print(response)
                else:
                    print(f"Error in QC: {response.get('message')}")

            #elif request_type == "QCFinishDoublet":
            #    doubletScore = request_type["doubletScore"]
            #
            #    qc_req = {
            #        user: user,
            #        project: project,
            #        dataset: dataset,
            #        doubletScore: doubletScore
            #    }
            #    print("Sending QC request...",qc_req)
            #    response = send_request('/qc_finish_doublet_endpoint', qc_req)
            #    print(response)
            #    if response['success']:
            #        print("QC Finish Doublet Successful... Sending SNS message to clear dataset as completed...")
            #        data = {
            #            "stage":"FinishDoublet",
            #            user:user,
            #            "project": project, 
            #            "dataset": dataset,
            #            "complete": True
            #        }
            #        response = send_sns(data)
            #        print(response)
            #    else:
            #        print(f"Error in QC: {response.get('message')}")

        except Exception as e:
            print("Error:", e)
        finally:
            #delete message once request is finished
            client.delete_message(QueueUrl=queue_url, ReceiptHandle=message['ReceiptHandle'])