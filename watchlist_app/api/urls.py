from django.urls import path,include
from watchlist_app.api.views import MovieListAV,MovieDetailAV 
# from watchlist_app.api.views import movie_list,movie_detail

urlpatterns = [

    path("list/",MovieListAV.as_view(),name="movie_list"),
    path('<int:pk>',MovieDetailAV.as_view(),name="movie_detail")
    # function based view urls
    # path("list/",movie_list,name="movie_list"),
    # path('<int:pk>',movie_detail,name="movie_detail"),
]