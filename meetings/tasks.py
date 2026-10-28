from celery import shared_task


@shared_task
def summarise_meeting(meeting_id):
    from meetings.models import Meeting
    from django.conf import settings
    import google.generativeai as genai
    import json

    try:
        meeting = Meeting.objects.get(id=meeting_id)

        if not meeting.transcript:
            return

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')

        response = model.generate_content(
            f'''Summarise this meeting transcript. Return ONLY a JSON object with:
{{
  "summary": "2-3 sentence summary",
  "action_items": ["action 1", "action 2"],
  "key_decisions": ["decision 1", "decision 2"]
}}

Transcript:
{meeting.transcript}'''
        )

        # Parse JSON response
        text = response.text.strip()
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        text = text.strip()

        data = json.loads(text)

        meeting.summary      = data.get('summary', '')
        meeting.action_items = data.get('action_items', [])
        meeting.save()

        # Push to all attendees via WebSocket
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'meeting_{meeting_id}',
            {
                'type':         'meeting_summary',
                'summary':      meeting.summary,
                'action_items': meeting.action_items,
            }
        )

    except Exception as e:
        print(f'Meeting summary error: {e}')