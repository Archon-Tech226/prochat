from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Board


@login_required
def board_view(request, board_id):
    board = get_object_or_404(Board, id=board_id)
    return render(request, 'whiteboard/board.html', {'board': board})


@login_required
def create_board(request):
    if request.method == 'POST':
        board = Board.objects.create(
            name=request.POST.get('name', 'New Board'),
            created_by=request.user
        )
        return board_view(request, board.id)
    return render(request, 'whiteboard/create.html')