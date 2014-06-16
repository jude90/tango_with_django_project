from django.shortcuts import render_to_response

# Create your views here.
from django.http import HttpResponse
from django.template import RequestContext
from rango.models import Category, Page
from rango.forms import CategoryForm, PageForm

from rango.forms import UserForm, UserProfileForm
def decode_url(name_url):
    if name_url.find(' '):
        return name_url.replace(' ','_')
    elif name_url.find('_'):
        return name_url.replace('_',' ')
def index(request):
    
    context       = RequestContext(request)
    category_list = Category.objects.order_by('-likes')[:5]
    page_list     = Page.objects.order_by('-views')[:5]
    context_dict  = {'categories':category_list,
                     'pages':page_list}

    #print category_list
    for category in category_list:
        category.url = category.name.replace(' ','_')
        #category.url = decode_url(category.name)

    return render_to_response('rango/index.html', context_dict, context)

def about(request):
    context = RequestContext(request)
    context_dict = {'name':"ASka dfhf"}
    return render_to_response('rango/about.html',context_dict)

def category(request, category_name_url):
    context = RequestContext(request)
    #decode parameter from url
    category_name = category_name_url.replace('_',' ')
    #category_name = decode_url(category_name_url)
    
    context_dict = {'category_name':category_name}
    context_dict['category_name_url'] = category_name_url
    try:
        category = Category.objects.get(name=category_name)

        pages = Page.objects.filter(category=category)
        
        # ORM objects
        context_dict['pages'] = pages
        context_dict['category'] = category


    except Category.DoesNotExist:
        # We get here if we didn't find the specified category.
        # Don't do anything - the template displays the "no category" message for us.
        pass
    return render_to_response('rango/category.html',context_dict,context)

def add_category(request):
    context = RequestContext(request)

    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save(commit=True)

            return index(request)
        else:
            print form.errors
    else:
        form = CategoryForm()
    return render_to_response('rango/add_category.html',{'form':form},context)

def add_page(request,category_name_url):
    context = RequestContext(request)

    category_name = category_name_url.replace('_',' ')
    if request.method =='POST':
        form = PageForm(request.POST)

        if form.is_valid():
            page = form.save(commit=False)

            try:
                cat = Category.objects.get(name=category_name)
                page.category = cat
            except Category.DoesNotExist:
                return render_to_response('/rango/add_category.html',{},context)

            page.views = 0
            page.save()
            return category(request,category_name_url)
        else:
            print form.errors
    else:
        # create a empty form 
        form = PageForm()
    return render_to_response('rango/add_page.html',
                              {'category_name_url':category_name_url,
                              'category_name':category_name,
                              'form':form},
                              context)


def register(request):
    context = RequestContext(request)

    registered = False
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form    = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid():
            user = user_form.save()
            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()
            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user
            # Did the user provide a profile picture?
            # If so, we need to get it from the input form and put it in the UserProfile model.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            profile.save()
            registered = True
        else:
            # Invalid form or forms - mistakes or something else?
            # Print problems to the terminal.
            # They'll also be shown to the user.
            print user_form.errors , profile_form.errors
    else:
        # Not a HTTP POST, so we render our form using two ModelForm instances.
        # These forms will be blank, ready for user input.
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render_to_response('rango/register.html',
                             {'user_form': user_form, 'profile_form': profile_form, 'registered': registered},
                              context)

def user_login(request):
    context = RequestContext(request)

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request,user)
                return HttpResponseRedirect('/rango/')
            else:
                return HttpResponse('Your Rango account is disabled.')
        else:
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse('Invalid login details')
    else:
        # The request is not a HTTP POST, so display the login form.
        # This scenario would most likely be a HTTP GET.
        return render_to_response('/rango/login.html',{},context)

