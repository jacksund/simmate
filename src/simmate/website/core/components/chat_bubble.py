# -*- coding: utf-8 -*-

from simmate.website.core.models import Feedback
from simmate.website.htmx.components import HtmxComponent


class ChatBubble(HtmxComponent):

    template_name = "core/chat_bubble.html"

    # State
    is_open: bool = False
    chat_history: list = None

    def mount(self):
        # Initialize the chat history on first load
        if self.chat_history is None:
            self.chat_history = [
                {
                    "sender": "bot",
                    "text": "Hi there! Please leave your feedback or report any issues here.",
                },
            ]

    def toggle_chat(self):
        self.is_open = not self.is_open

    def submit_message(self):
        message = self.post_data.get("message", "").strip()
        if not message:
            return

        # Add user message to history
        self.chat_history.append({"sender": "user", "text": message})

        # Save to Feedback table
        Feedback.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            message=message,
            url_path=self.request.META.get("HTTP_REFERER", ""),
        )

        # Default fallback response
        self.chat_history.append(
            {
                "sender": "bot",
                "text": "Thank you for your feedback! It has been recorded, and I have notified our team.",
            }
        )

        # Clear the input box
        self.form_data["message"] = ""

        # Keep chat bubble open after submission
        self.is_open = True
