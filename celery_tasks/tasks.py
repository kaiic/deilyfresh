import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE","dailyfresh.settings")
django.setup()

#使用celery
from celery import Celery
from django.core.mail import send_mail
from django.conf import settings
from django.template import loader, RequestContext
# from goods.models import GoodsType,IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner

#创建一个Celery类的实例对象
from apps.goods.models import IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner,GoodsType

app = Celery('celery_tasks.tasks',broker='redis://127.0.0.1:6379/8')



#定义任务函数
@app.task
def send_register_active_email(to_email,username,token):
    '''激活邮件'''
    #组织邮件信息
    subject = '天天生鲜欢迎信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = '<h1>%s,欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活您的账号<br/>' \
                   '<a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' % (
                   username, token, token)

    # 参数：邮箱标题，正文，发件人，收件人，HTML正文
    send_mail(subject, message, sender, receiver, html_message=html_message)


@app.task
def generate_static_index_html():
    '''产生首页静态页面'''
    # 获取商品种类信息
    types = GoodsType.objects.all()

    # 获取轮播商品信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')  # 0 1 2 3 升序

    # 获取促销活动信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

    # 获取首页分类商品展示信息
    # type_goods_banners = IndexTypeGoodsBanner.objects.all()
    for type in types:  # GoodsType
        # 获取type种类首页分类商品的图片展示信息
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
        # 获取type种类首页分类商品的文字展示信息
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
        # 动态给type增加属性，分别保存首页商品的图片展示信息和文字展示信息
        type.image_banners = image_banners
        type.title_banners = title_banners

    # 组织模板上下文
    context = {
        'types': types,
        'goods_banners': goods_banners,
        'promotion_banners': promotion_banners
    }
    #使用模板
    # 1.加载模板文件
    temp = loader.get_template('static_index.html')
    # 2.定义模板上下文
    # context = RequestContext(request,context)
    # 3.模板渲染
    static_index_html = temp.render(context)
    # 生成首页对应的静态页面
    save_path =os.path.join(settings.BASE_DIR,'static/index.html')
    #创建文件
    with open(save_path,'w', encoding='utf-8') as f:
        f.write(static_index_html)
