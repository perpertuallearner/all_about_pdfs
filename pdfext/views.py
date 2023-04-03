from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.conf import settings
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdftypes import resolve1
from pdfminer.psparser import PSLiteral, PSKeyword
from pdfminer.utils import decode_text
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
import json
import os
import pdfquery

from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from .models import Pdfext
import operator
from django.urls import reverse_lazy
from django.contrib.staticfiles.views import serve

from django.db.models import Q


def home(request):
    context = {
        'pdfexts': Pdfext.objects.all()
    }
    return render(request, 'pdfext/home.html', context)

def search(request):
    template='pdfext/home.html'

    query=request.GET.get('q')

    result=Pdfext.objects.filter(Q(title__icontains=query) | Q(author__username__icontains=query) | Q(content__icontains=query))
    paginate_by=2
    context={ 'pdfexts':result }
    return render(request,template,context)
   


def getfile(request):
   return serve(request, 'File')


class PdfextListView(ListView):
    model = Pdfext
    template_name = 'pdfext/home.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'pdfexts'
    ordering = ['-date_posted']
    paginate_by = 2


class UserPdfextListView(ListView):
    model = Pdfext
    template_name = 'pdfext/user_pdfexts.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'pdfexts'
    paginate_by = 2

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Pdfext.objects.filter(author=user).order_by('-date_posted')


class PdfextDetailView(DetailView):
    model = Pdfext
    template_name = 'pdfext/pdfext_detail.html'


class PdfextCreateView(LoginRequiredMixin, CreateView):
    model = Pdfext
    template_name = 'pdfext/pdfext_form.html'
    fields = ['title', 'content', 'file']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PdfextUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Pdfext
    template_name = 'pdfext/pdfext_form.html'
    fields = ['title', 'content', 'file']

    def form_valid(self,form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        pdfext = self.get_object()
        if self.request.user == pdfext.author:
            return True
        return False

    

class PdfextDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Pdfext
    success_url = '/'
    template_name = 'pdfext/pdfext_confirm_delete.html'

    def delete(self, request: HttpRequest, *args: str, **kwargs: any) -> HttpResponse:
        pdfext = self.get_object()
        pdfext.file.delete(save=False)
        pdfext.converted_file.delete(save=False)
        return super().delete(request, *args, **kwargs)
    
    def test_func(self):
        pdfext = self.get_object()
        if self.request.user == pdfext.author:
            return True
        return False


# class PdfextDownloadView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
#     print("comes to pdfextdownload")
#     model = Pdfext
#     template_name = 'pdfext/pdfext_convert.html'
#     fields = ['title', 'content', 'file']
#     success_url = 'pdfext-detail'


class PdfextConvertView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Pdfext
    template_name = 'pdfext/pdfext_convert.html'
    fields = ['title', 'content', 'file','json_data']
    success_url = '/'

    
    def start_convert(self, form):
        pdfext = self.get_object();
      

    def get(self, request: HttpRequest, *args: str, **kwargs: any) -> HttpResponse:
        mydata = Pdfext.objects.filter(id=kwargs['pk']).values_list('file', flat=True)
        pdffilename = settings.MEDIA_ROOT+"/"+mydata[0]
        pdf = pdfquery.PDFQuery(pdffilename)
        pdf.load()
        text_elements = pdf.pq('LTTextBoxHorizontal')
        # text = []
        keys = []
        my_pdf_dict = {}
        my_pdf_dict_cleaned = {}
        # text = [t.text for t in text_elements] 
        for t in text_elements:
            parsed_text = t.text.replace('\uf063','').strip().lower()
            if(parsed_text):
                if(parsed_text not in my_pdf_dict):
                    my_pdf_dict[parsed_text]=''
                    keys.append(parsed_text)
                # text.append(parsed_text) 
        # print(text)
        value_elements = pdf.pq("Annot")
        for v in value_elements:
            attvalue = ''
            atttext = ''
            attrslist = v.items()
            for attritem in attrslist:
                if(attritem[0]=='T'):
                    atttext = attritem[1].strip().lower()
                if(attritem[0] == 'V'):
                    attvalue = attritem[1].strip().lower()
            if(attvalue):
                # print(atttext+ " = "+attvalue)
                if(atttext in my_pdf_dict.keys()):
                    my_pdf_dict[atttext] = attvalue
                    keys.append(atttext)
        for key,value in my_pdf_dict.items():
            if(not value and ':' in key):
                    print("comes here for debug")
                    #since the value is empty and text has : we
                    #assume that the data is already part of the
                    #text
                    values_after_split = key.split(':',1)
                    print(values_after_split)
                    atttext = values_after_split[0].strip().lower()
                    attvalue = values_after_split[1].strip().lower()
                    my_pdf_dict_cleaned[atttext] = attvalue
            else:
                my_pdf_dict_cleaned[key] = value
            # print(v.items()[7],end='\t')
            # print(v.items()[9])
        # print(my_pdf_dict)
        xmloutfilename = pdffilename.replace(".pdf",".xml")
        pdf.tree.write(xmloutfilename, pretty_print=True)
        # with open(outfilename) as xml_file:
        #     data_dict = xmltodict.parse(xml_file.read())
        # json_data = json.dumps(my_pdf_dict)
        # print(my_pdf_dict)
        pdfext = Pdfext.objects.get(id=kwargs['pk'])
        pdfext.json_data = my_pdf_dict_cleaned
        outfilename = pdffilename.replace(".pdf",".json")
        with open(outfilename, 'w', encoding='utf-8') as f:
            json.dump(my_pdf_dict_cleaned, f, ensure_ascii=False, indent=4)
        pdfext.converted_file = outfilename
        pdfext.save(force_update=True)
        # print(pdfext.title)
        # print(pdfext.json_data)

        
        # for k,v in json_data:
        #     print(k)
        #     keys.update(set(k))  # gather up all keys
        # key_order = sorted(keys)  # or whichever order you like
        # print(key_order)
        context = {
             "object":pdfext,
             "key_order": keys,
             "data":my_pdf_dict_cleaned,
        }
        # for page_layout in extract_pages(pdffilename):
        #     for element in page_layout:
        #         if isinstance(element, LTTextContainer):
        #             print(element.get_text().strip())
        return render(request,'pdfext/pdfext_convert.html',context)
        # return super().get(request, *args, **kwargs)
    
   
    
    def post(self, request: HttpRequest, *args: str, **kwargs: any) -> HttpResponse:
        print("enters post ")
        mydata = Pdfext.objects.filter(id=kwargs['pk']).values_list('file', flat=True)
        print(mydata[0])
        return super().post(request, *args, **kwargs)

    def form_valid(self,form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        pdfext = self.get_object()
        if self.request.user == pdfext.author:
            return True
        return False


def about(request):
    return render(request, 'pdfext/about.html', {'title': 'About'})


def downloadjson(request, **kwargs: any):
    mydata = Pdfext.objects.filter(id=kwargs['pk']).values_list('converted_file', flat=True)
    jsonfilename = mydata[0]
    file1 = open(jsonfilename)
    content = file1.read()
    response = HttpResponse(content, content_type='application/json')
    response['Content-Length'] = os.path.getsize(jsonfilename)
    filenametodownload = os.path.splitext(os.path.basename(jsonfilename))[0]
    response['Content-Disposition'] = 'attachment; filename=%s' % '{fname}.json'.format(fname=filenametodownload)
    response['Location'] = '/pdfext/'+str(kwargs['pk'])+"/"
    return response
    # return JsonResponse(json.dumps(content),safe=True,)
    # return render(request, 'pdfext/user_pdfexts.html')
