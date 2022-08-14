from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from chat.ClientNodes.binary_search_tree import root as rt, BinaryTree
import random
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import time
from strangerChat.connections import disconnect


def home(request):
    return render(request, 'index.html')


class SearchNext(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []

    def post(self, request, *args, **kwargs):
        ids = int(request.data.get("anonymous_id"))
        time.sleep(1.5)
        tree = BinaryTree()
        current_user = tree.object_by_key(rt, ids)
        c_ref = current_user.dict['requested']
        current_user.dict["requested"] = None
        current_user.dict["active"] = True
        # searches for empty user
        channel_layer = get_channel_layer()

        # clear out previous connection
        second_user = tree.clear_requested(rt, ids)
        # searches user
        search_user = tree.makeSearch(rt, ids)
        user_found = False
        if search_user is not None:
            async_to_sync(channel_layer.group_send)("chat_" + str(search_user.data),
                                                    {"type": "chat_message", "message": search_user.dict["requested"],
                                                     "status": "test", 'direction': None})
            user_found = True
            current_user.dict["active"] = False

        # disconnect current user from everyone
        def alert_disconnect_message(anonymous_key, node):
            node.dict["requested"] = None
            node.active = True
            async_to_sync(channel_layer.group_send)('chat_' + str(anonymous_key), disconnect)

        if second_user is not None:
            alert = second_user.dict['id']
            alert_disconnect_message(alert, second_user)

        if c_ref is not None:
            # if the current got requested by someone
            alert_disconnect_message(c_ref, current_user)

        return Response({
            "token": ids,
            "socket": user_found
        })


class SyncChat(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []

    def get(self, request, *args, **kwargs):
        tree = BinaryTree()
        ids = random.randint(1, 10000000)
        while True:
            # 0(H)
            searched = tree.object_by_key(rt, ids)
            if searched is None:
                break
            else:
                ids = random.randint(1, 10000000)

        root = tree.insert(rt, ids, {
            "active": True,
            "id": ids,
            "requested": None
        })
        # O(H)
        search = tree.makeSearch(root, ids)

        user_found = False
        if search is not None:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)("chat_" + str(search.data),
                                                    {"type": "chat_message", "message": search.dict["requested"],
                                                     "status": "test", 'direction': None})
            user_found = True

            # O(H)
            get_current_node = tree.object_by_key(rt, ids)
            get_current_node.dict["active"] = False
        return Response({
            "token": ids,
            "socket": user_found
        })
