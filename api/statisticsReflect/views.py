from django.db.models import Count, Case, When, IntegerField
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime

from api.emotions.models import UserState


class MoodStatisticsView(APIView):
    def get(self, request):
        # Получаем параметры дат из запроса
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Валидация дат
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=400)

        # Фильтрация по пользователю и дате
        queryset = UserState.objects.filter(user=request.user)
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        # Группировка значений по шкале 1-5
        stats = queryset.annotate(
            mood_group=Case(
                When(value__lte=2, then=1),
                When(value__range=(3, 4), then=2),
                When(value__range=(5, 6), then=3),
                When(value__range=(7, 8), then=4),
                When(value__gte=9, then=5),
                default=0,
                output_field=IntegerField()
            )
        ).values('mood_group').annotate(
            freq=Count('mood_group')
        ).order_by('mood_group')

        # Форматирование результата
        result = [{"state": item['mood_group'], "freq": item['freq']} for item in stats]

        return Response(result)