from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.conf import settings
from django.core.mail import send_mail
from celery_tasks.tasks import send_register_active_email
from django.contrib.auth import authenticate,login,logout
from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection
from django.core.paginator import Paginator
import re

from django.views.generic import View
from apps.user.models import User,Address
from apps.goods.models import GoodsSKU
from apps.order.models import OrderInfo,OrderGoods
# Create your views here.

# /user/register
def register(request):
    '''显示注册页面'''
    if request.method == 'GET':
        #显示注册页面
        return render(request,'register.html')
    else:
        #进行注册处理
        # 1.接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 2.进行数据校验:all()函数，都为真才真
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', str(email)):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        # 是否同意协议
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None
        if user:
            # 用户名已存在
            return render(request, 'register.html', {'errmsg': '用户名已存在'})

        # 3.进行业务处理：进行用户注册
        # user = User()
        # user.username = username
        # user.password = password
        # ...
        # user.save()
        user = User.objects.create_user(username, email, password)
        user.is_active = 0  # 用户处于没有激活状态
        user.save()

        # 4.返回应答,跳转到首页
        url = reverse('goods:index')
        return redirect(url)

def register_handle(request):
    '''进行注册处理'''
    # 1.接收数据
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    email = request.POST.get('email')
    allow = request.POST.get('allow')
    # 2.进行数据校验:all()函数，都为真才真
    if not all([username,password,email]):
        #数据不完整
        return render(request,'register.html',{'errmsg':'数据不完整'})
    #校验邮箱
    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',str(email)):
        return render(request,'register.html',{'errmsg':'邮箱格式不正确'})
    #是否同意协议
    if allow != 'on':
        return render(request, 'register.html', {'errmsg': '请同意协议'})


    #校验用户名是否重复
    try:
        user = User.objects.get(username = username)
    except User.DoesNotExist:
        #用户名不存在
        user = None
    if user:
        #用户名已存在
        return render(request,'register.html',{'errmsg':'用户名已存在'})

    # 3.进行业务处理：进行用户注册
    # user = User()
    # user.username = username
    # user.password = password
    # ...
    # user.save()
    user = User.objects.create_user(username,email,password)
    user.is_active = 0  #用户处于没有激活状态
    user.save()

    #发送激活邮件，包含激活链接：http://127.0.0.1:8000/user/active/加密的用户id
    #激活链接需要包含用户名的身份信息，用户信息需要加密

    #加密用户的身份信息，生成激活的token
    serializer = Serializer(settings.SECRET_KEY,3600)
    info = {'confirm':user.id}
    token = serializer.dumps(info)

    #发邮件
    subject = '天天生鲜欢迎信息'
    message = '邮件正文'
    sender = settings.EMAIL_FROM
    receiver = [email]
    send_mail(subject,message,sender,receiver)
    #激活链接

    # 4.返回应答,跳转到首页
    url = reverse('goods:index')
    return redirect(url)

class RegisterView(View):
    '''注册'''
    def get(self,request):
        '''显示注册页面'''
        return render(request,'register.html')

    def post(self,request):
        '''进行注册处理'''
        # 1.接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 2.进行数据校验:all()函数，都为真才真
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', str(email)):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        # 是否同意协议
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None
        if user:
            # 用户名已存在
            return render(request, 'register.html', {'errmsg': '用户名已存在'})

        # 3.进行业务处理：进行用户注册
        # user = User()
        # user.username = username
        # user.password = password
        # ...
        # user.save()
        user = User.objects.create_user(username, email, password)      #django默认认证系统注册默认激活
        user.is_active = 0  # 设置用户处于没有激活状态
        user.save()

        # 发送激活邮件，包含激活链接：http://127.0.0.1:8000/user/active/加密的用户id
        # 激活链接需要包含用户名的身份信息，用户信息需要加密
        # itsdangerous实现加密用户的身份信息，生成激活的token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)  #返回的是一个bytes
        token = token.decode('utf8')    #解码

        # 发邮件,celery异步实现，使用delay发出任务
        send_register_active_email.delay(email,username,token)

        # 4.返回应答,跳转到首页
        url = reverse('goods:index')
        return redirect(url)
    
# 点击激活链接后进行激活
class ActiveView(View):
    '''用户激活'''
    def get(self,request,token):
        '''进行用户激活'''
        #进行解密，获取要激活的用户信息
        # serializer = Serializer('密钥'，过期时间)
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            #获取待激活用户的id
            user_id = info['confirm']

            #根据id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active=1
            user.save()
            #跳转到登录页面
            return redirect(reverse('user:login'))  #重定向，反向解析
        except SignatureExpired as e:
            #激活链接已过期
            return HttpResponse('激活链接已过期')

# 登录
# /user/login
class LoginView(View):
    '''登录'''
    def get(self,request):
        '''显示登录页面'''
        #判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username= ''
            checked = ''
        return render(request,'login.html',{'username':username,'checked':checked})

    def post(self,request):
        '''登录校验'''
        #接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        #校验数据
        if not all([username,password]):
            return render(request,'login.html',{'errmsg':'数据不完整'})

        # 业务处理
        # 使用django自带的认证系统authenticate(username,password),认证成功返回user对象，失败则返回None
        user = authenticate(username=username,password=password)
        # user1 = User.objects.get(username=username)
        # print(user1.password)
        # print(password)
        if user is not None:
            #用户名密码正确
            if user.is_active:
                #用户已激活
                #记录用户的登录状态
                login(request,user)

                #获取登录后所要跳转的地址
                #默认跳转到首页
                next_url = request.GET.get('next',reverse('goods:index'))

                # 跳转到next_url
                response = redirect(next_url)
                #判断是否需要记住用户名
                remember = request.POST.get('remember')
                if remember=='on':
                    #记住用户名
                    response.set_cookie('username',username,max_age=7*24*3600)
                else:
                    response.delete_cookie('username')
                #返回response
                return response
            else:
                #用户未激活
                return render(request,'login.html',{'errmsg':'账户未激活'})
        else:
            #用户名或密码错误
            return render(request,'login.html',{'errmsg':'用户名或密码错误'})

# /user/logout
class LogoutView(View):
    '''退出登录'''
    def get(self,request):
        '''退出登录'''
        # 清除用户的session信息，logout函数清除登录用户的session信息。
        logout(request)
        # 跳转首页
        return redirect(reverse('goods:index'))

# /user
class UserInfoView(LoginRequiredMixin,View):
    '''用户中心-信息页'''
    def get(self,request):
        '''显示'''
        # page='user'
        # request.user
        # 如果用户未登录->AnonymousUser类的一个实例
        # 如果登录了->User类的一个实例
        # request.user.is_authenticated()

        # 获取用户的个人信息
        user = request.user
        address = Address.objects.get_default_address(user)

        # 获取用户的历史浏览信息
        # from redis import StrictRedis
        # sr = StrictRedis(host='127.0.0.1',port='6379',db=9)
        # 拿redis链接
        con = get_redis_connection('default')

        # id格式
        history_key = 'history_%d'%user.id

        # 获取用户最新浏览的5个商品的id,作为列表返回
        sku_ids = con.lrange(history_key,0,4)

        # 从数据看看中查询用户浏览的商品的具体信息
        # goods_li = GoodsSKU.objects.filter(id__in=sku_ids)
        #
        # goods_res = []
        # for a_id in sku_ids:
        #     for goods in goods_li:
        #         if a_id==goods:
        #             goods_res.append(goods)

        # 遍历获取用户浏览的商品信息
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        # 组织上下文
        content = {'page':'user','address':address,'goods_li':goods_li}

        # 除了你给模板文件传递的模板变量之外，django框架会把request.user也传给模板文件
        return render(request,'user_center_info.html',content)

# /user/order
class UserOrderView(LoginRequiredMixin,View):
    '''用户中心-订单页'''
    def get(self,request,page):
        '''显示'''
        #page='order'
        #获取用户的订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')
        # 遍历获取订单商品的信息
        for order in orders:
            # 根据order_id查询订单商品信息
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)
            #遍历order_skus计算商品的小计
            for order_sku in order_skus:
                #计算小计
                amount = order_sku.count * order_sku.price
                # 动态给order_sku增加属性amount，保存订单商品的小计
                order_sku.amount = amount
            # 动态给order增加属性，保存订单的状态标题
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
            #动态给order增加属性，保存订单商品的信息
            order.order_skus = order_skus

        #分页
        paginator = Paginator(orders,1)
        # 处理页码
        # 获取page的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1
        if page > paginator.num_pages:
            page = 1

        # 获取第page页的Page实例对象
        order_page = paginator.page(page)

        # 1.总页数少于五页，页面显示所有页码
        # 2.如果当前页是前三页，显示1-5页
        # 如果当前页是后三页，显示后五页
        # 其他其他情况，显示当前页的前两页，当前页，后两页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif num_pages <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 组织上下文
        context={
            'order_page':order_page,
            'pages':pages,
            'page':'order'
        }
        # 使用模板
        return render(request,'user_center_order.html',context)

# /user/address
class AddressView(LoginRequiredMixin,View):
    '''用户中心-地址页'''
    def get(self,request):
        '''显示'''
        # page='address'

        # 获取登录用户对应的User对象
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认收货地址
        #     address = None
        address = Address.objects.get_default_address(user)

        # 使用模板
        return render(request,'user_center_site.html',{'page':'address','address':address})

    def post(self,request):
        '''地址添加'''
        # 接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 校验数据
        if not all([receiver,addr,phone]):
            return render(request,'user_center_site.html',{'errmsg':'数据不完整'})
        # 校验手机号
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$',phone):
            return render(request,'user_center_site.html',{'errmsg':'手机号格式不正确'})

        # 业务处理
        # 如果用户已存在默认收货地址，添加的地址不作为默认收货地址，否则做完默认收货地址
        # 获取登录用户对应的User对象
        user = request.user
        # try:
        #     address = Address.objects.get(user=user,is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认收货地址
        #     address = None
        address = Address.objects.get_default_address(user)

        if address:
            is_default = False
        else:
            is_default = True

        # 添加地址
        Address.objects.create(user=user,
                                receiver=receiver,
                                addr=addr,
                                zip_code=zip_code,
                                phone=phone,
                                is_default=is_default)
        # 返回应答,刷新地址页面
        return redirect(reverse('user:address'))    #get请求方式