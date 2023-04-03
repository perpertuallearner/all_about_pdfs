from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
import os

def get_file_location(instance,filename):
		return 'Files/{0}/{1}'.format(instance.author.username,filename)

class Pdfext(models.Model):
	id = models.BigAutoField(primary_key=True)
	title = models.CharField(max_length=100)
	content = models.TextField()
	date_posted = models.DateTimeField(default=timezone.now)
	author = models.ForeignKey(User, on_delete=models.CASCADE)
	converted_file = models.FileField(null=True,default='',upload_to='Files')
	json_data = models.JSONField(default=dict)
	file = models.FileField(null=True,blank=True,upload_to=get_file_location)

	

	def __str__(self):
		return self.title

	def extension(self):
		name, extension = os.path.splitext(self.file.name)
		return extension

	def get_absolute_url(self):
		return reverse('pdfext-detail', kwargs={'pk': self.pk})

        
