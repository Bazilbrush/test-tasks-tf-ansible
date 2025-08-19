
setx AZURE_STORAGE_CONNECTION_STRING ""
The following is a list of powershell invocations i used to test the endponts
# helllo kube
Invoke-RestMethod -Uri "http://localhost:3000/"
# send message
$body = @{
    connect_str = ""
    queue_name  = "one-test"
    content     = @{
        priority = 3
        body     = "From docker"
    }
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri "http://localhost:3000/send" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

# receiveall
$connectStr = ""
$encodedConnectStr = [System.Web.HttpUtility]::UrlEncode($connectStr)
Invoke-RestMethod -Uri "http://localhost:3000/receiveall?connect_str=$encodedConnectStr&queue_name=one-test"

# receivebyid
$connectStr = ""
$encodedConnectStr = [System.Web.HttpUtility]::UrlEncode($connectStr)
$message_id = "978600f3-05ad-4ced-8aac-0b6804e83085"
Invoke-RestMethod -Uri "http://localhost:3000/receivebyid?connect_str=$encodedConnectStr&queue_name=one-test&msgid=$message_id"

# peekbyid
$connectStr = ""
$encodedConnectStr = [System.Web.HttpUtility]::UrlEncode($connectStr)
$message_id = "d5fb5b86-51b9-482f-bd9a-45b556b801a5"
Invoke-RestMethod -Uri "http://localhost:3000/peekbyid?connect_str=$encodedConnectStr&queue_name=one-test&msgid=$message_id"

# check
$connectStr = ""
$encodedConnectStr = [System.Web.HttpUtility]::UrlEncode($connectStr)
Invoke-RestMethod -Uri "http://localhost:3000/check?connect_str=$encodedConnectStr&queue_name=one-test"


# docker 
docker build -t queues:latest .
docker run -d -p 3000:3000 queues:latest

docker run -d -p 3000:3000 localhost:5000/queues:latest