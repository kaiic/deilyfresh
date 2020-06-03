from django.urls import path, re_path
from apps.order.views import OrderPlaceView,OrderCommintView,OrderPayView,CheckPayView,CommentView
app_name = 'order'
urlpatterns = [
    re_path(r'^place$',OrderPlaceView.as_view(),name='place'),  #提交订单页面上显示
    re_path(r'^commint$',OrderCommintView.as_view(),name='commint'),  #订单创建
    re_path(r'^pay$',OrderPayView.as_view(),name='pay'),  #订单支付
    re_path(r'^check$',CheckPayView.as_view(),name='check'),  #c查询支付交易结果
    re_path(r'^comment/(?P<order_id>.+)$',CommentView.as_view(),name='comment'),  #订单评论
]
