from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Post, Category, Tag
from comments.forms import CommentForm
from django.views.generic import ListView, DetailView


class IndexView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'
    paginate_by = 1

    def get_context_data(self, **kwargs):  # 发送给客户端的context，django通过这个方法实现
        # 只需要重写这个方法，在其中插入我们要加入的数据，再返回给客户端。
        context = super().get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        is_paginated = context.get('is_paginated')
        pagination_data = self.pagination_data(paginator, page, is_paginated)
        context.update(pagination_data)
        return context

    def pagination_data(self, paginator, page, is_paginated):
        if not is_paginated:
            return {}
        left = []
        right = []
        left_has_more = False
        right_has_more = False
        first = False
        last = False
        page_number = page.number
        total_pages = paginator.num_pages
        page_range = paginator.page_range
        if page_number == 1:
            right = page_range[page_number:page_number + 2]
            if right[-1] < total_pages - 1:
                right_has_more = True
            if right[-1] < total_pages:
                last = True
        elif page_number == total_pages:
            left = page_range[(page_number - 3) if (page_number - 3) > 0 else 0: page_number - 1]
            # 左边需要判断溢出
            if left[0] > 2:
                left_has_more = True
            if left[0] > 1:
                first = True
        else:
            left = page_range[(page_number - 3) if (page_number - 3) > 0 else 0:page_number - 1]
            right = page_range[page_number:page_number + 2]
            if right[-1] < total_pages - 1:
                right_has_more = True
            if right[-1] < total_pages:
                last = True
            if left[0] > 2:
                left_has_more = True
            if left[0] > 1:
                first = True
        data = {
            'left': left,
            'right': right,
            'left_has_more': left_has_more,
            'right_has_more': right_has_more,
            'first': first,
            'last': last,
        }
        return data


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get(self, request, *args, **kwargs):  # 主方法，get调用其他的辅助方法，整个过程都在get中发生
        # get等价与detail函数
        response = super().get(request, *args, **kwargs)
        self.object.increase_views()
        return response  # 传递给浏览器的HTTP响应就是get方法返回的HttpResponse对象

    # def get_object(self, queryset=None):
    #     post = super().get_object(queryset=None)
    #     md = markdown.Markdown(extensions=['markdown.extensions.extra',
    #                                        'markdown.extensions.codehilite',
    #                                        TocExtension(slugify=slugify)
    #                                        ])
    #     post.body = md.convert(post.body)
    #     post.toc = md.toc
    #     return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = CommentForm()
        comment_list = self.object.comment_set.all()
        context.update(
            {
                'form': form, 'comment_list': comment_list
            }
        )
        return context


# 总结：共同点：都执行了父类方法，然后对父类方法的返回值进行一些操作，最后返回这个修改后的返回值。


class ArchivesView(IndexView):

    def get_queryset(self):
        return super().get_queryset().filter(created_time__year=self.kwargs.get('year'),
                                             created_time__month=self.kwargs.get('month')
                                             )


class CategoryView(IndexView):

    def get_queryset(self):
        cate = get_object_or_404(Category, pk=self.kwargs.get('pk'))
        return super().get_queryset().filter(category=cate)


# 首先是需要根据从 URL 中捕获的分类 id（也就是 pk）获取分类，这
# 和  category 视图函数中的过程是一样的。不过注意一点的是，在类视图中，从
# URL 捕获的命名组参数值保存在实例的  kwargs 属性（是一个字典）里，非命名组
# 参数值保存在实例的  args 属性（是一个列表）里。所以我们使
# 了  self.kwargs.get('pk') 来获取从 URL 捕获的分类 id 值。
class TagView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'

    def get_queryset(self):
        tag = get_object_or_404(Tag, pk=self.kwargs.get('pk'))
        return super().get_queryset().filter(tags=tag)


def search(request):
    q = request.GET.get('q')
    error_msg = ''
    if not q:
        error_msg = '请输入关键词'
        return render(request, 'blog/index.html', {'error_msg': error_msg})
    post_list = Post.objects.filter(Q(title__icontains=q) | Q(body__icontains=q))
    #     这里  icontains 是查询表达式（Field lookups），我们在之前
    # 也使用过其他类似的查询表达式，其用法是在模型需要筛选的属性后面跟上两个下划
    # 线。
    return render(request, 'blog/index.html', {'error_msg': error_msg,
                                               'post_list': post_list
                                               })
