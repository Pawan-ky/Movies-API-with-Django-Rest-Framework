from rest_framework.response import Response
from rest_framework import status
# from rest_framework.decorators import api_view
from rest_framework.views import APIView
# from rest_framework import mixins
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from rest_framework.throttling import UserRateThrottle,AnonRateThrottle, ScopedRateThrottle  
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters



from rest_framework.permissions import IsAuthenticated,IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from watchlist_app.api.pagination import WatchListCPagination, WatchListLOPaginantion, WatchListPagination

from watchlist_app.api.permissions import IsAdminorReadOnly,IsReviewUserorReadOnly
from watchlist_app.models import WatchList,StreamPlatform,Reviews
from watchlist_app.api.serializers import (WatchListSerializer,StreamPlatformSerializer,
                                        ReviewSerializer)

from watchlist_app.api.throttle import ReviewCreateThrottle,ReviewListThrottle

# filtering/paginatino
class UserReviewList(generics.ListAPIView):
    # throttle_classes = [ReviewListThrottle,AnonRateThrottle]
    # permission_classes = [IsAuthenticated]
    # queryset = Reviews.objects.all()          override this method
    serializer_class = ReviewSerializer

    def get_queryset(self):
        username = self.kwargs['username']
        return Reviews.objects.filter(review_user__username=username)


# concrete generic view class 
class ReviewCreateGCV(generics.CreateAPIView):
    throttle_classes = [ReviewCreateThrottle]
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Reviews.objects.all()

    def perform_create(self,serializer):
        pk = self.kwargs.get('pk')
        movie = WatchList.objects.get(pk=pk)

        user = self.request.user
        queryset = Reviews.objects.filter(watchlist=movie,review_user=user)
        if queryset.exists():
            raise ValidationError("You reviewed this moview already")
        
        if movie.number_rating ==0:
            movie.avg_rating = serializer.validated_data['rating']
        else:
            movie.avg_rating = (movie.avg_rating*movie.number_rating+serializer.validated_data['rating'])/(movie.number_rating+1)
        movie.number_rating +=1 
        movie.save() 


        serializer.save(watchlist=movie,review_user=user)

class ReviewListGCV(generics.ListAPIView):
    throttle_classes = [ReviewListThrottle,AnonRateThrottle]

    # permission_classes = [IsAuthenticated]
    # queryset = Reviews.objects.all()          override this method
    serializer_class = ReviewSerializer
    
    # third party filtering
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['review_user__username', 'active']

    def get_queryset(self):
        pk = self.kwargs['pk']
        return Reviews.objects.filter(watchlist=pk)

class ReviewDetailGCV(generics.RetrieveUpdateDestroyAPIView):
    # throttle_classes = [ReviewListThrottle,AnonRateThrottle]
    
    throttle_classes = [ScopedRateThrottle ]
    throttle_scope = 'review_detail'
    permission_classes = [IsReviewUserorReadOnly]

    queryset = Reviews.objects.all()
    serializer_class = ReviewSerializer

#  GenericAPIView and mixins

# class ReviewDetailGV(mixins.RetrieveModelMixin,generics.GenericAPIView):
#     queryset = Reviews.objects.all()
#     serializer_class = ReviewSerializer

#     def get(self, request, *args, **kwargs):
#         return self.retrieve(request, *args, **kwargs) 


# class ReviewListGV(mixins.ListModelMixin,
#                   mixins.CreateModelMixin,
#                   generics.GenericAPIView):
#     queryset = Reviews.objects.all()
#     serializer_class = ReviewSerializer

#     def get(self, request, *args, **kwargs):
#         return self.list(request, *args, **kwargs)

#     def post(self, request, *args, **kwargs):
#         return self.create(request, *args, **kwargs)

class WatchListGV(generics.ListAPIView):
    serializer_class = WatchListSerializer
    queryset = WatchList.objects.all()
    pagination_class = WatchListCPagination
    
    # third party filtering
    # filter_backends = [DjangoFilterBackend]
    # filterset_fields = ['title', 'platform__name']
    
    # filter_backends = [filters.SearchFilter]
    # filterset_fields = ['=title', 'platform__name']
    
    # filter_backends = [filters.OrderingFilter]
    # filterset_fields = ['avg_rating']
    

# class based views
class WatchListAV(APIView):
    permission_classes = [IsAdminorReadOnly]
    def get(self, request):
        movies = WatchList.objects.all()
        serializer = WatchListSerializer(movies, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = WatchListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WatchDetailAV(APIView):
    permission_classes = [IsAdminorReadOnly]
    def get(self,request, pk):
        try:
            movie =  WatchList.objects.get(pk=pk)
        except WatchList.DoesNotExist:
            return Response({"error":"movie not found"},status=status.HTTP_404_NOT_FOUND)
        serializer = WatchListSerializer(movie)
        return Response(serializer.data)
    
    def put(self, request, pk):
        try:
            movie = WatchList.objects.get(pk=pk)
        except WatchList.DoesNotExist:
            return Response({"error":"movie not found"},status=status.HTTP_404_NOT_FOUND)
        serializer = WatchListSerializer(movie, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        try:
            movie = WatchList.objects.get(pk=pk)
        except WatchList.DoesNotExist:
            return Response({"error":"movie not found"},status=status.HTTP_404_NOT_FOUND)
        movie.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# using model viewset
# read only model viewset can be used
# class StreamPlatformViewsSet(viewsets.ModelViewSet):
#     queryset =  StreamPlatform.objects.all()
#     serializer_class = StreamPlatformSerializer
#     permission_classes = [IsAdminorReadOnly]

# using viewsets alone
# class StreamPlatformViewsSet(viewsets.ViewSet):
#     def list(self, request):
#         queryset = StreamPlatform.objects.all()
#         serializer = StreamPlatformSerializer(queryset, many=True,context={'request': request})
#         return Response(serializer.data)

#     def retrieve(self, request, pk=None):
#         queryset = StreamPlatform.objects.all()
#         platform = get_object_or_404(queryset, pk=pk)
#         serializer = StreamPlatformSerializer(platform,context={'request': request})
#         return Response(serializer.data)
#     def create(self,request):
#         serializer = StreamPlatformSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StreamPlatformAV(APIView):
    permission_classes = [IsAdminorReadOnly]
    def get(self, request):
        platform = StreamPlatform.objects.all()
        serializer = StreamPlatformSerializer(platform, many=True,context={'request': request})
        return Response(serializer.data)
    
    def post(self, request):
        serializer = StreamPlatformSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StreamPlatformDetailAV(APIView):
    permission_classes = [IsAdminorReadOnly]
    def get(self,request, pk):
        try:
            platform = StreamPlatform.objects.get(pk=pk)
        except StreamPlatform.DoesNotExist:
            return Response({"error":"platform not found"},status=status.HTTP_404_NOT_FOUND)
        serializer = StreamPlatformSerializer(platform,context={'request': request})
        return Response(serializer.data)
    def put(self,request,pk):
        try:
            platform = StreamPlatform.objects.get(pk=pk)
        except StreamPlatform.DoesNotExist:
            return Response({"error":"platform not found"},status=status.HTTP_404_NOT_FOUND)
        serializer = StreamPlatformSerializer(platform, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self,pk):
        try:
            platform = StreamPlatform.objects.get(pk=pk)
        except StreamPlatform.DoesNotExist:
            return Response({"error":"platform not found"},status=status.HTTP_404_NOT_FOUND)
        platform.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)









# function based views
# @api_view(['GET','POST'])
# def movie_list(request):
#     if request.method == 'GET':
#         movies = Movie.objects.all()
#         serializer = WatchListSerializer(movies, many=True)
#         return Response(serializer.data)
#     if request.method == 'POST':
#         serializer = WatchListSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# @api_view(['GET','PUT','DELETE'])
# def movie_detail(request, pk):
#     if request.method == 'GET':
#         try:
#             movie = Movie.objects.get(pk=pk)
#         except Movie.DoesNotExist:
#             return Response({"error":"movie not found"},status=status.HTTP_404_NOT_FOUND)
#         serializer = WatchListSerializer(movie)
#         return Response(serializer.data)
#     if request.method == 'PUT':
#         movie = Movie.objects.get(pk=pk)
#         serializer = WatchListSerializer(movie, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#     if request.method == 'DELETE':
#         movie = Movie.objects.get(pk=pk)
#         movie.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)