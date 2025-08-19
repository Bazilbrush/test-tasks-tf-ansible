import os, re, json
from flask import Flask, request, jsonify
from azure.storage.queue import  QueueClient

app = Flask(__name__)


@app.post('/send')
def sendMessage():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Missing JSON body"}), 400

        connect_str = data.get("connect_str")
        queue_name = data.get("queue_name")
        content = data.get("content")

        # Input validation
        if not isinstance(content.get("priority"), int):
            return jsonify({"error": "The 'priority' attr must be an INT"}), 400
        if not isinstance(content.get("body"), str):
            return jsonify({"error": "The 'body' attr must be a STRING"}), 400

        queue_client = QueueClient.from_connection_string(connect_str, queue_name)
        queue_client.send_message(json.dumps(content))

        return jsonify({"status": "Message sent successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def sendDlqMessage(connect_str, queue_name, content):
    #validation
    if not isinstance(content["priority"], int):
        raise ValueError("The 'priority' attr must be an INT")
    if not isinstance(content["body"], str):
        raise ValueError("The 'body' attr must be a STRING")

    dl_queue_client = QueueClient.from_connection_string(connect_str, f"{queue_name}-poison")
    
    dl_queue_client.send_message(json.dumps(content))


@app.get('/receiveall')
def receiveAllMessage():
    try:
        connect_str = request.args.get("connect_str")
        queue_name  = request.args.get("queue_name")

        if not connect_str or not queue_name:
            return jsonify({"error": "Missing required params: connect_str and queue_name"}), 400
        # list  all message IDs ina queue
        queue_client = QueueClient.from_connection_string(connect_str, queue_name)
        
        # Get messages from the queue
        messages = queue_client.receive_messages(max_messages=32)
        msg_ids = [msg.id for msg in messages]

        return jsonify(msg_ids), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get('/receivebyid')
def receiveMessageById():
    try:
        connect_str = request.args.get("connect_str")
        queue_name  = request.args.get("queue_name")
        message_id = request.args.get("msgid")

        queue_client = QueueClient.from_connection_string(connect_str, queue_name)
        #we just dequeued all the messages as this is all that a fifo can do
        messages = queue_client.receive_messages()   # this can take a lot of ram if there's too many messages, might wanna implement paging
        messageByid = [msg.content for msg in messages if msg.id == message_id] # get message by id
    
        if re.search(r'ERROR', messageByid[0]):
            sendDlqMessage(connect_str, queue_name, json.loads(messageByid[0]))
            print(f"DLQ-{messageByid}")
            return jsonify(f"DLQ-{messageByid}"), 200

        # return messageByid
        return jsonify(messageByid), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get('/peekbyid')
def peekMessageById ():
    try:
        connect_str = request.args.get("connect_str")
        queue_name  = request.args.get("queue_name")
        message_id = request.args.get("msgid")

        queue_client = QueueClient.from_connection_string(connect_str, queue_name)

        # Peek at messages in the queue
        peeked_messages = queue_client.peek_messages(max_messages=32)  #need to handle batches

        messageByid = [msg.content for msg in peeked_messages if msg.id == message_id]
        peeked_message = f"Peek-{messageByid}"

        return jsonify(peeked_message), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get('/check')
def checkMessagesInDlq():
    try:
        connect_str = request.args.get("connect_str")
        queue_name  = request.args.get("queue_name")
        dl_queue = f"{queue_name}-poison"
        queue_client = QueueClient.from_connection_string(connect_str, dl_queue)
        properties = queue_client.get_queue_properties()
        
        return jsonify(properties.approximate_message_count), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get('/')
def hello():
    namespace = os.environ.get("NAMESPACE", "default")
    message = f"Hello {namespace} Kube"  # just to make really sure it templates correctly, it's probably unnecessary
    return message, \
           200, \
           {'Content-Type': 'text/html; charset=utf-8'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)


