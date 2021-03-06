import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from chat.models import RoomMember, Message


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        # noinspection PyAttributeOutsideInit
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        # noinspection PyAttributeOutsideInit
        self.room_group_name = "chat_%s" % self.room_name

        # Join room group
        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        room_member_id = text_data_json["room_member_id"]
        text = text_data_json["text"]
        room_member = RoomMember.objects.get(id=room_member_id)
        Message.objects.create(room_member=room_member, room=room_member.room, text=text)

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "chat_message", "username": room_member.user.username, "text": text}
        )

    # Receive message from room group
    def chat_message(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps(event))
