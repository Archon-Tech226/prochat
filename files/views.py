from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import UploadedFile
import os


@login_required
def file_list(request):
    files = UploadedFile.objects.filter(uploaded_by=request.user)
    return render(request, 'files/list.html', {'files': files})


@login_required
def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded = request.FILES['file']
        f = UploadedFile.objects.create(
            uploaded_by=request.user,
            file=uploaded,
            file_name=uploaded.name,
            file_type=uploaded.content_type,
            file_size=uploaded.size,
        )
        return JsonResponse({'status': 'ok', 'file_id': f.id, 'file_name': f.file_name})
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def delete_file(request, file_id):
    f = get_object_or_404(UploadedFile, id=file_id, uploaded_by=request.user)
    f.file.delete()
    f.delete()
    return redirect('file_list')