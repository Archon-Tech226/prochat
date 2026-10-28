from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Task


@login_required
def task_list(request):
    tasks = Task.objects.filter(owner=request.user)
    return render(request, 'tasks/list.html', {'tasks': tasks})


@login_required
def create_task(request):
    if request.method == 'POST':
        Task.objects.create(
            owner=request.user,
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            due_date=request.POST.get('due_date') or None,
            priority=request.POST.get('priority', 'medium'),
        )
        return redirect('task_list')
    return render(request, 'tasks/create.html')


@login_required
def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, owner=request.user)
    task.status = 'done'
    task.save()
    return JsonResponse({'status': 'ok'})


@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, owner=request.user)
    task.delete()
    return redirect('task_list')