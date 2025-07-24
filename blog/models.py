import re

from django.db import models
from ckeditor.fields import RichTextField
from django.utils.text import slugify, Truncator
from django.conf import settings

class Post(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    content = RichTextField()
    author = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='blog_images/', blank=True, null=True)

    # SEO
    seo_title = models.CharField(max_length=255, blank=True,
        help_text=" SEO заголовок (title) — показывается в поисковике. До 60 символов.")

    seo_description = models.TextField(max_length=300, blank=True,
        help_text=" SEO описание (description) — краткое описание статьи. До 160 символов.")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        # Автозаполнение seo_title (ограничено 60 символами)
        if not self.seo_title:
            self.seo_title = Truncator(self.title).chars(60, truncate='...')

        # Автозаполнение seo_description (ограничено 160 символами)
        if not self.seo_description:
            plain_text = re.sub(r'<[^>]+>', '', self.content)
            plain_text = ' '.join(plain_text.split())
            self.seo_description = Truncator(plain_text).chars(160, truncate='...')

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
