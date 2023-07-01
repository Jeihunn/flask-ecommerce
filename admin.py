import os
import uuid
from flask import request, redirect, url_for, flash
from start import db, app
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from werkzeug.security import generate_password_hash
from models import Image, User, Category, Product, Comment, Contact, UserFavorite, Subscriber
from werkzeug.utils import secure_filename
from flask_login import current_user
from werkzeug.datastructures import FileStorage
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, EqualTo, Optional, Email, ValidationError
from wtforms import StringField, EmailField
from flask_admin import expose


class UserAdmin(ModelView):
    form_columns = ['first_name', 'last_name',
                    'email', 'password', 'confirm_password', 'is_superuser', 'profile_photo']
    column_list = ['id', 'first_name', 'last_name',
                   'email', 'is_superuser']
    column_sortable_list = ['id', 'first_name',
                            'last_name', 'email', 'is_superuser']
    column_filters = ['id', 'first_name', 'last_name', 'email']
    column_searchable_list = ['id', 'first_name', 'last_name', 'email']
    column_default_sort = ('id', True)

    column_labels = {
        'id': 'ID',
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'email': 'Email',
        'is_superuser': 'Superuser',
    }

    form_extra_fields = {
        'email': EmailField('Email', validators=[DataRequired(), Email()]),
        'confirm_password': StringField('Confirm Password', validators=[Optional(), Length(min=8, max=30), EqualTo('password', message='Passwords must match')]),
        'profile_photo': FileField('Profile Photo', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only!')])

    }

    def save_profile_photo(self, form, model):
        if 'profile_photo' in form:
            profile_photo = form.profile_photo.data
            if profile_photo and isinstance(profile_photo, FileStorage):
                filename = secure_filename(profile_photo.filename)
                base_name, ext = os.path.splitext(filename)
                unique_filename = f"{base_name}_{uuid.uuid4().hex}{ext}"
                photo_path = os.path.join(
                    app.config['UPLOAD_FOLDER'], 'profile', unique_filename)
                profile_photo.save(photo_path)
                model.profile_photo = unique_filename

    def on_model_change(self, form, model, is_created):
        self.save_profile_photo(form, model)
        if is_created:
            model.password = generate_password_hash(form.password.data)
        else:
            if form.confirm_password.data != "":
                model.password = generate_password_hash(form.password.data)
            if not form.password.data.count("pbkdf2:sha256:"):
                model.password = generate_password_hash(form.password.data)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_superuser

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login_view'))
        else:
            return redirect(url_for('index_view'))


class CategoryAdmin(ModelView):
    form_columns = ['title', 'is_active']
    column_list = ['id', 'title', 'is_active', 'slug']
    column_searchable_list = ['title']
    column_sortable_list = ['id', 'title', 'is_active', 'slug']
    column_filters = ['id', 'title', 'slug', 'is_active']
    column_searchable_list = ['id', 'title', 'slug']
    column_default_sort = ('id', True)

    column_labels = {
        'id': 'ID',
        'title': 'Title',
        'is_active': 'Active',
        'email': 'Email',
        'slug': 'Slug',
    }

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.generate_unique_slug()

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_superuser

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login_view'))
        else:
            return redirect(url_for('index_view'))


class ProductAdmin(ModelView):
    form_columns = ['title', 'description',
                    'price', 'discounted_price', 'is_active', 'cover_photo', 'image_files', 'categories', 'created_at']
    column_list = ['id', 'title', 'price',
                   'discounted_price', 'is_active', 'slug', 'categories', 'created_at']
    column_sortable_list = ['id', 'title', 'price',
                            'discounted_price', 'is_active', 'slug', 'created_at']
    column_filters = ['id', 'title', 'slug', 'categories', 'created_at']
    column_searchable_list = ['id', 'title', 'slug', 'created_at']
    column_default_sort = ('id', True)

    column_labels = {
        'id': 'ID',
        'title': 'Title',
        'price': 'Price',
        'discounted_price': 'Discounted Price',
        'is_active': 'Active',
        'slug': 'Slug',
        'categories': 'Categories',
        'created_at': 'Created At',
    }

    form_extra_fields = {
        'cover_photo': FileField('Cover Photo', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only!')]),
        'image_files': FileField('Images', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'webp'], 'Images only!')], render_kw={'multiple': 'True'})
    }

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.generate_unique_slug()
            if form.image_files.data == None:
                image = Image(filename="default-product-image.jpg",
                              product_id=model.id)
                image.save()

        if form.image_files.data != None:
            Image.query.filter_by(product_id=model.id).delete()
            self.save_images(form, model)
        self.save_cover_photo(form, model)

    def save_cover_photo(self, form, model):
        cover_photo_file = request.files.get(form.cover_photo.name)
        if cover_photo_file and cover_photo_file.filename != '':
            original_filename = secure_filename(cover_photo_file.filename)
            base_name, ext = os.path.splitext(original_filename)
            unique_filename = f"{base_name}_{uuid.uuid4().hex}{ext}"
            save_path = os.path.join(
                app.config['UPLOAD_FOLDER'], 'product_cover', unique_filename)
            cover_photo_file.save(save_path)
            model.cover_photo = unique_filename
            db.session.commit()

    def save_images(self, form, model):
        image_files = request.files.getlist(form.image_files.name)
        if image_files:
            for image_file in image_files:
                if image_file.filename != '':
                    filename = secure_filename(image_file.filename)
                    base_name, ext = os.path.splitext(filename)
                    unique_filename = f"{base_name}_{uuid.uuid4().hex}{ext}"
                    save_path = os.path.join(
                        app.config['UPLOAD_FOLDER'], 'product_images', unique_filename)
                    image_file.save(save_path)
                    image = Image(filename=unique_filename,
                                  product_id=model.id)
                    db.session.add(image)
        db.session.commit()

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_superuser

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login_view'))
        else:
            return redirect(url_for('index_view'))


class ImageAdmin(ModelView):
    column_list = ['id', 'product.id', 'product.title', 'filename']
    column_sortable_list = ['product.id', 'product.title']
    form_columns = ['product', 'image']
    column_filters = ['product.id', 'product.title', 'filename']
    column_searchable_list = ['product.id', 'product.title', 'filename']
    column_default_sort = ('id', True)

    column_labels = {
        'id': 'ID',
        'product.id': 'Product ID',
        'product.title': 'Product Title',
        'filename': 'Filename',
    }

    form_extra_fields = {
        'image': FileField('Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only!')])
    }

    def save_product_photo(self, form, model):
        product_photo = request.files.get(form.image.name)
        if product_photo and product_photo.filename != '':
            original_filename = secure_filename(product_photo.filename)
            base_name, ext = os.path.splitext(original_filename)
            unique_filename = f"{base_name}_{uuid.uuid4().hex}{ext}"
            save_path = os.path.join(
                app.config['UPLOAD_FOLDER'], 'product_images', unique_filename)
            product_photo.save(save_path)
            model.filename = unique_filename
            db.session.commit()

    def on_model_change(self, form, model, is_created):
        if is_created:
            if form.image.data != None:
                self.save_product_photo(form, model)
            else:
                raise ValidationError('Image file cannot be left blank.')
        else:
            if form.image.data != None:
                Image.query.filter_by(product_id=model.id).delete()
                self.save_product_photo(form, model)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_superuser

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login_view'))
        else:
            return redirect(url_for('index_view'))


class CommentAdmin(ModelView):
    column_list = ['user', 'user.email',
                   'product', 'review', 'created_at']
    column_sortable_list = ['id',  ('user', 'user.first_name'), 'user.email', (
        'product', 'product.title'), 'review', 'created_at']
    column_filters = ['user.first_name', 'user.last_name',
                      'user.email', 'product.title', 'review', 'created_at']
    column_searchable_list = ['user.first_name', 'user.last_name',
                              'user.email', 'product.title', 'review', 'created_at']
    column_default_sort = ('id', True)

    column_labels = {
        'user': 'User',
        'user.email': 'User Email',
        'product': 'Product',
        'review': 'Review',
        'created_at': 'Created At',
    }

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_superuser

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login_view'))
        else:
            return redirect(url_for('index_view'))


class UserFavoriteAdmin(ModelView):
    column_list = ['user_id', 'user', 'user.email',
                   'product_id', 'product.title', 'product.is_active']
    column_sortable_list = ['user_id', ('user', 'user.first_name'),
                            'user.email', 'product_id', 'product.title', 'product.is_active']
    column_filters = ['user_id', 'user.first_name', 'user.last_name',
                      'user.email', 'product_id', 'product.title', 'product.is_active']
    column_searchable_list = ['user_id', 'user.first_name',
                              'user.last_name', 'user.email', 'product_id', 'product.title']
    column_default_sort = ('user_id', True)

    column_labels = {
        'user_id': 'User ID',
        'user': 'User',
        'user.email': 'User Email',
        'product_id': 'Product ID',
        'product.title': 'Product Title',
        'product.is_active': 'Product Active',
    }

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_superuser

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login_view'))
        else:
            return redirect(url_for('index_view'))


class ContactAdmin(ModelView):
    column_list = ['id', 'name', 'email', 'subject', 'message', 'created_at']
    column_sortable_list = ['id', 'name', 'email', 'subject', 'created_at']
    column_filters = ['name', 'email', 'subject', 'message', 'created_at']
    column_searchable_list = ['name', 'email',
                              'subject', 'message', 'created_at']
    column_default_sort = ('id', True)

    column_labels = {
        'id': 'ID',
        'name': 'Name',
        'email': 'Email',
        'subject': 'Subject',
        'message': 'Message',
        'created_at': 'Created At',
    }

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_superuser

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login_view'))
        else:
            return redirect(url_for('index_view'))


class SubscriberAdmin(ModelView):
    column_list = ['id', 'name', 'email', 'is_active']
    column_sortable_list = ['id', 'name', 'email', 'is_active']
    column_filters = ['id', 'name', 'email', 'is_active']
    column_searchable_list = ['id', 'name', 'email', 'is_active']
    column_default_sort = ('id', True)

    column_labels = {
        'id': 'ID',
        'name': 'Name',
        'email': 'Email',
        'is_active': 'Active',
    }

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_superuser

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login_view'))
        else:
            return redirect(url_for('index_view'))


class CustomAdminIndexView(AdminIndexView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'Dashboard'

    @expose('/')
    def index(self):
        self.name = 'Dashboard'

        user_count = len(User.query.all())
        superuser_count = len(User.query.filter(
            User.is_superuser == True).all())

        category_count = len(Category.query.all())
        category_is_active_count = len(
            Category.query.filter(Category.is_active == True).all())

        product_count = len(Product.query.all())
        product_is_active_count = len(Product.query.filter(
            Product.is_active == True).all())

        comment_count = len(Comment.query.all())
        comment_lasted_created = None
        comment = Comment.query.order_by(Comment.created_at.desc()).first()
        if comment is not None:
            comment_lasted_created = comment.created_at
        unique_product_count = len(Comment.query.with_entities(
            Comment.product_id).distinct().all())
        unique_user_count = len(Comment.query.with_entities(
            Comment.user_id).distinct().all())

        contact_count = len(Contact.query.all())
        contact_lasted_created = None
        contact = Contact.query.order_by(Contact.created_at.desc()).first()
        if contact is not None:
            contact_lasted_created = contact.created_at

        subscriber_count = len(Subscriber.query.all())
        subscriber_is_active_count = len(
            Subscriber.query.filter(Subscriber.is_active == True).all())

        favorite_product_count = len(UserFavorite.query.with_entities(
            UserFavorite.product_id).distinct().all())

        context = {
            'user_count': user_count,
            'superuser_count': superuser_count,
            'product_count': product_count,
            "product_is_active_count": product_is_active_count,
            "category_count": category_count,
            "category_is_active_count": category_is_active_count,
            "comment_count": comment_count,
            "comment_lasted_created": comment_lasted_created,
            "unique_product_count": unique_product_count,
            "unique_user_count": unique_user_count,
            "contact_count": contact_count,
            "contact_lasted_created": contact_lasted_created,
            "subscriber_count": subscriber_count,
            "subscriber_is_active_count": subscriber_is_active_count,
            "favorite_product_count": favorite_product_count,
        }
        return self.render('admin/dashboard.html', **context)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_superuser

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login_view'))
        return redirect(url_for('index_view'))


admin = Admin(app, name='Admin Panel', template_mode='bootstrap4',
              index_view=CustomAdminIndexView())


admin.add_view(UserAdmin(User, db.session))
admin.add_view(CategoryAdmin(Category, db.session))
admin.add_view(ProductAdmin(Product, db.session))
admin.add_view(ImageAdmin(Image, db.session))
admin.add_view(CommentAdmin(Comment, db.session))
admin.add_view(UserFavoriteAdmin(UserFavorite, db.session))
admin.add_view(ContactAdmin(Contact, db.session))
admin.add_view(SubscriberAdmin(Subscriber, db.session))
