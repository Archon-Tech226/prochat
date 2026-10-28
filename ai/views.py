from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import StreamingHttpResponse, JsonResponse
from django.conf import settings
from .models import AIConversation, AIMessage
import google.generativeai as genai
import json


# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)


def get_system_prompt(role):
    prompts = {
        'student':    'You are a helpful AI tutor for students. Help with homework, explain concepts clearly, and encourage learning.',
        'freelancer': 'You are a helpful AI assistant for freelancers. Help with proposals, client communication, invoices, and project management.',
        'worker':     'You are a helpful AI assistant for professionals. Help with reports, presentations, meeting summaries, and workplace tasks.',
        'company':    'You are a helpful AI assistant for businesses. Help with team management, announcements, meeting notes, and business communication.',
    }
    return prompts.get(role, 'You are a helpful AI assistant.')


@login_required
def ai_chat(request):
    conversations = AIConversation.objects.filter(user=request.user).order_by('-created_at')[:10]
    return render(request, 'ai/chat.html', {'conversations': conversations})


@login_required
def stream_response(request):
    """SSE endpoint — streams Gemini API response token by token"""
    query    = request.GET.get('q', '')
    convo_id = request.GET.get('convo_id', None)

    if not query:
        return JsonResponse({'error': 'No query'}, status=400)

    # Get or create conversation
    if convo_id:
        try:
            conversation = AIConversation.objects.get(id=convo_id, user=request.user)
        except AIConversation.DoesNotExist:
            conversation = AIConversation.objects.create(user=request.user)
    else:
        conversation = AIConversation.objects.create(user=request.user)

    # Save user message
    AIMessage.objects.create(conversation=conversation, role='user', content=query)

    # Get role-based system prompt
    try:
        role = request.user.userprofile.role
    except Exception:
        role = 'worker'

    system_prompt = get_system_prompt(role)

    def generate():
        try:
            model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                system_instruction=system_prompt
            )

            full_response = ''

            response = model.generate_content(
                query,
                stream=True,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=1000,
                    temperature=0.7,
                )
            )

            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    yield f'data: {json.dumps({"text": chunk.text, "convo_id": conversation.id})}\n\n'

            # Save assistant response
            AIMessage.objects.create(
                conversation=conversation,
                role='assistant',
                content=full_response
            )
            yield f'data: {json.dumps({"done": True, "convo_id": conversation.id})}\n\n'

        except Exception as e:
            yield f'data: {json.dumps({"error": str(e)})}\n\n'

    response = StreamingHttpResponse(generate(), content_type='text/event-stream')
    response['Cache-Control']    = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@login_required
def translate_message(request):
    if request.method == 'POST':
        data        = json.loads(request.body)
        text        = data.get('text', '')
        target_lang = data.get('target_lang', 'English')

        try:
            model    = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(
                f'Translate this to {target_lang}. Return ONLY the translated text, nothing else:\n\n{text}'
            )
            return JsonResponse({'translated': response.text})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'POST required'}, status=400)


@login_required
def summarise_document(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        text = data.get('text', '')

        try:
            model    = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(
                f'Summarise this document in 3-5 bullet points:\n\n{text}'
            )
            return JsonResponse({'summary': response.text})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'POST required'}, status=400)