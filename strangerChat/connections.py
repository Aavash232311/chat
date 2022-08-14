import json
from chat.ClientNodes.binary_search_tree import BinaryTree, root as rt
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer

disconnect = {
    'type': 'chat_message',
    'message': "USER OFFLINE",
    'direction': None,
    'status': 'alert',
}


class Connection(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_group_name = None
        self.room_name = None
        self.anonymous_id = None

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['chat_id']
        self.anonymous_id = int(self.room_name)
        self.room_group_name = 'chat_' + self.room_name

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
        tree = BinaryTree()
        # remove connection with any connected socket
        layer = get_channel_layer()
        node = tree.clear_requested(rt, self.anonymous_id)

        if node is not None:
            async_to_sync(layer.group_send)('chat_' + str(node.data), disconnect)
        else:
            current_node = tree.object_by_key(rt, self.anonymous_id)
            async_to_sync(layer.group_send)('chat_' + str(current_node.dict["requested"]), disconnect)

        tree.removeNode(rt, self.anonymous_id)

    def receive(self, text_data):
        load_json = json.loads(text_data)
        message = str(load_json['message']).strip()
        tree = BinaryTree()
        anonymous_id = self.room_group_name.split('_')[1]
        anonymous_id = int(anonymous_id)
        broadcast_id = None
        valid_connection = False

        searched = tree.object_by_key(rt, anonymous_id)
        if searched is not None and searched.dict is not None and searched.dict["requested"] is not None:
            # if searched user     second user
            check = searched.dict["requested"]
            broadcast_id = int(check)
            valid_connection = True
        else:
            # if user searching user  first user
            searching_user = tree.searching_user_requested_node(rt, anonymous_id)
            if searching_user is not None:
                current_key = searching_user["requested"]
                if current_key is not None:
                    broadcast_id = int(searching_user['id'])
                    valid_connection = True

        if valid_connection:
            def direction(d):
                return {
                    'type': 'chat_message',
                    'message': message,
                    'direction': d,
                    'status': 'commercial',
                }

            second_layer = get_channel_layer()

            # # to second user
            async_to_sync(second_layer.group_send)("chat_" + str(broadcast_id), direction("left"))

            # echo
            async_to_sync(self.channel_layer.group_send)(self.room_group_name, direction("right"))

    def chat_message(self, event):
        self.send(text_data=json.dumps({
            'message': event["message"],
            'status': event["status"],
            'direction': event["direction"]
        }))
