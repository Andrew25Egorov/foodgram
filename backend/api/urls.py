from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import UserViewSet

app_name = 'api'

router = DefaultRouter()
#router_v1.register('categories', CategoryViewSet, 'category')
#router_v1.register('genres', GenreViewSet, 'genre')
#router_v1.register('titles', TitleViewSet, 'title')
#router_v1.register(
#    r'titles/(?P<title_id>\d+)/reviews', ReviewViewSet, basename='review'
#)
#router_v1.register(
#    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
#    CommentViewSet,
#    basename='comment',
#)
router.register(r'users', UserViewSet, basename='users')

#auth_patterns = [
#    path('token/', TokenView.as_view()),
#    path('signup/', SignUpView.as_view()),
#]

urls = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]

#urlpatterns = [path('v1/', include(api_v1_urls))]