from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def job_list(request):
    return render(request, 'jobs/list.html')