from rest_framework import generics, permissions
from .models import EmotionalTag, Tag, UserStateTag, UserEmotionalTag, UserState
from .serializers import UserStateSerializer, EmotionalTagSerializer, TagSerializer
from django.db.models import Count, Case, When, IntegerField, Avg, DateField
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models.functions import Cast, TruncDate
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class UserStateView(generics.ListCreateAPIView):
    serializer_class = UserStateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = UserState.objects.filter(user=self.request.user)

        # Фильтрация по дате (YYYY-MM-DD)
        date = self.request.query_params.get('date', None)
        if date:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date=date_obj)
            except ValueError:
                pass

        # Фильтрация по периоду
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                queryset = queryset.filter(created_at__range=[start, end])
            except ValueError:
                pass

        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserStateDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserStateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserState.objects.filter(user=self.request.user)

class EmotionalTagListView(generics.ListCreateAPIView):
    queryset = EmotionalTag.objects.all()
    serializer_class = EmotionalTagSerializer

class TagListView(generics.ListCreateAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

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
                When(value__lte=1, then=1),
                When(value__range=(2, 3), then=2),
                When(value__range=(4, 6), then=3),
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


class TagsStatisticsView(APIView):
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=400)

        # Используем UserStateTag для точного подсчёта
        queryset = UserStateTag.objects.filter(
            user_state__user=request.user

        )

        if start_date:
            queryset = queryset.filter(user_state__created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(user_state__created_at__lte=end_date)

        # Группируем по тегу и считаем уникальные записи состояний
        top_tags = queryset.values(
            'tag_id', 'tag__name', 'tag__emoji'
        ).annotate(
            freq=Count('user_state', distinct=True)
        ).order_by('-freq')[:5]

        result = [{
            "id": item['tag_id'],
            "name": item['tag__name'],
            "emoji": item['tag__emoji'],
            "freq": item['freq']
        } for item in top_tags]

        return Response(result)


class EmotionalTagsStatisticsView(APIView):
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=400)

        # Используем UserEmotionalTag для точного подсчёта
        queryset = UserEmotionalTag.objects.filter(
            user_state__user=request.user
        )

        if start_date:
            queryset = queryset.filter(user_state__created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(user_state__created_at__lte=end_date)

        # Группируем по эмоциональному тегу и считаем уникальные записи состояний
        top_etags = queryset.values(
            'emotional_tag_id', 'emotional_tag__name', 'emotional_tag__emoji'
        ).annotate(
            freq=Count('user_state', distinct=True)
        ).order_by('-freq')[:5]

        result = [{
            "id": item['emotional_tag_id'],
            "name": item['emotional_tag__name'],
            "emoji": item['emotional_tag__emoji'],
            "freq": item['freq']
        } for item in top_etags]

        return Response(result)


class WeeklyMoodStatsView(APIView):
    def get(self, request):
        today = datetime.now().date()
        start_date = today - timedelta(days=6)

        stats = UserState.objects.filter(
            user=request.user,
            created_at__date__range=(start_date, today)
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            avg_mood=Avg('value')
        ).order_by('date')

        return Response([{
            "date": item['date'].strftime('%Y-%m-%d'),
            "average_mood": round(item['avg_mood'], 2)
        } for item in stats])


class MonthlyMoodStatsView(APIView):
    def get(self, request):
        today = datetime.now().date()
        start_date = today - relativedelta(months=1) + timedelta(days=1)

        stats = UserState.objects.filter(
            user=request.user,
            created_at__date__range=(start_date, today)
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            avg_mood=Avg('value')
        ).order_by('date')

        return Response([{
            "date": item['date'].strftime('%Y-%m-%d'),
            "average_mood": round(item['avg_mood'], 2)
        } for item in stats])


class YearlyMoodStatsView(APIView):
    def get(self, request):
        today = datetime.now().date()
        start_date = today - relativedelta(years=1) + timedelta(days=1)

        stats = UserState.objects.filter(
            user=request.user,
            created_at__date__range=(start_date, today)
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            avg_mood=Avg('value')
        ).order_by('date')

        return Response([{
            "date": item['date'].strftime('%Y-%m-%d'),
            "average_mood": round(item['avg_mood'], 2)
        } for item in stats])