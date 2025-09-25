# -*- coding: utf-8 -*-

from django.contrib.auth.models import User

from simmate.database.base_data_types import DatabaseTable, table_column


class ChatbotHistory(DatabaseTable):
    """
    This stores chatbot conversations and associated metadata. These chats are
    periodically reviewed by our team to enhance the chatbot's accuracy, improve
    AI functionality, and monitor usage.
    """

    user = table_column.ForeignKey(
        User,
        on_delete=table_column.PROTECT,
        null=True,
        blank=True,
        related_name="chatbot_conversations",
    )
    """
    The user that is sending messages and talking with the chatbot
    """

    summary = table_column.TextField(blank=True, null=True)
    """
    A short 1-2 sentence summary of the converstation. This is generated using
    an LLM *after* a chat is inactive for >24 hrs.
    """

    messages = table_column.JSONField(null=True, blank=True)
    """
    The list of messages in the converstation. Note that images, dataframes,
    and plots are ommitted and replaced with text like "(( IMAGE 123 ))"
    """
    # OPTIMIZE: I could store in a separate table, but I think this is easy enough

    # TODO: user feedback and review
    # user_rating = table_column.IntegerField(blank=True, null=True)
    # user_feedback = table_column.TextField(blank=True, null=True)
    # is_reviewed = table_column.BooleanField(default=False, blank=True, null=True)
    # review_comments = table_column.TextField(blank=True, null=True)

    # OPTIMIZE: maybe I could write these to a zip file instead...?
    # plotly_figures = table_column.JSONField(null=True, blank=True)
    # dataframes = table_column.JSONField(null=True, blank=True)
    # images = table_column.JSONField(null=True, blank=True)

    @classmethod
    def from_streamlit(
        cls,
        chat_id: int,
        user_id: int,
        chat_history: dict,
    ) -> int:

        messages = [
            {"type": m.type, "content": m.content} for m in chat_history.messages
        ]

        # if this is a new chat, we need to create a new entry
        if not chat_id:
            new_chat = cls(user_id=user_id, messages=messages)
            new_chat.save()
            return new_chat.id
        # otherwise grab and update the existing chat entry
        else:
            cls.objects.filter(id=chat_id).update(user_id=user_id, messages=messages)
            return chat_id
