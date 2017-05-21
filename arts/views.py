from django.shortcuts import render
from .models import Article, Category, Site, AdvanceSearch
from django.contrib import messages


def index(request):
    return render(request, 'arts/index.html')


def detail(request):
    article = Article.objects.order_by('?').first()
    context = {'article': article}
    return render(request, 'arts/detail.html', context=context)


def advance(request):
    if request.method == "POST":
        adv_search = AdvanceSearch(site_id=request.POST['site'],
                                   category_id=request.POST['category'],
                                   author=request.POST['author'],
                                   keywords=request.POST['keywords'],
                                   date=request.POST['date'],
                                   rate=request.POST['rate'],)
        article_query_set = Article.get_article_query_set_advance(adv_search)
        if not article_query_set:
            message = messages.error(request, "Nie znaleziono artykułu o podanych kryteriach")
            context = {'message': message}
            return render(request, 'arts/index.html', context=context)

        article = article_query_set.order_by('?').first()
        context = {'article': article}
        return render(request, 'arts/detail.html', context=context)

    categories = Category.objects.all().order_by('category_name')
    sites = Site.objects.all().order_by('site_name')
    context = {'sites': sites, 'categories': categories}
    return render(request, 'arts/advance.html', context=context)


def poll(request):
    return render(request, 'arts/index.html')