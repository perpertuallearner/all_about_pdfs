from django.urls import path
from .views import (
    PdfextListView,
    PdfextDetailView,
    PdfextCreateView,
    PdfextUpdateView,
    PdfextDeleteView,
    UserPdfextListView,
    PdfextConvertView,
)
from . import views

urlpatterns = [
    path('', PdfextListView.as_view(), name='pdfext-home'),
    path('user/<str:username>', UserPdfextListView.as_view(), name='user-pdfexts'),
    path('pdfext/<int:pk>/', PdfextDetailView.as_view(), name='pdfext-detail'),
    path('pdfext/new/', PdfextCreateView.as_view(), name='pdfext-create'),
    path('pdfext/<int:pk>/update/', PdfextUpdateView.as_view(), name='pdfext-update'),
    path('pdfext/<int:pk>/delete/', PdfextDeleteView.as_view(), name='pdfext-delete'),
    path('pdfext/<int:pk>/convert/', PdfextConvertView.as_view(), name='pdfext-convert'),
    path('media/Files/<int:pk>',PdfextDeleteView.as_view(),name='pdfext-delete' ),
    path('downloadjson/<int:pk>',views.downloadjson, name="downloadjson"),
    path('search/',views.search,name='search' ),
    path('about/', views.about, name='pdfext-about'),
]
