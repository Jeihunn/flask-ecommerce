from datetime import datetime
import pytz
from extensions import db
from flask_login import UserMixin
from slugify import slugify


def get_current_time():
    return datetime.now(pytz.timezone("Asia/Baku"))


class UserFavorite(db.Model):
    __tablename__ = 'user_favorite'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey(
        'product.id'), primary_key=True)

    product = db.relationship('Product', back_populates='favorited_by')
    user = db.relationship('User', back_populates='favorites')

    def __init__(self, user_id, product_id):
        self.user_id = user_id
        self.product_id = product_id

    def __str__(self):
        return self.product_id


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_superuser = db.Column(db.Boolean(), nullable=False, default=False)
    profile_photo = db.Column(db.String(255), default="default_user.webp")

    comments = db.relationship('Comment', back_populates='user')
    favorites = db.relationship(
        'UserFavorite', back_populates='user', cascade='all, delete')

    def __init__(self, first_name, last_name, email, password, is_superuser):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.password = password
        self.is_superuser = is_superuser

    def add_favorite(self, product):
        favorite = UserFavorite.query.filter_by(
            user_id=self.id, product_id=product.id).first()
        if not favorite:
            favorite = UserFavorite(user_id=self.id, product_id=product.id)
            db.session.add(favorite)
            db.session.commit()

    def remove_favorite(self, product):
        favorite = UserFavorite.query.filter_by(
            user_id=self.id, product_id=product.id).first()
        if favorite:
            db.session.delete(favorite)
            db.session.commit()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self):
        db.session.add(self)
        db.session.commit()


product_category = db.Table('product_category',
                            db.Column('product_id', db.Integer, db.ForeignKey(
                                'product.id'), primary_key=True),
                            db.Column('category_id', db.Integer, db.ForeignKey(
                                'category.id'), primary_key=True)
                            )


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean(), nullable=False, default=False)
    slug = db.Column(db.String(255), unique=True)

    products = db.relationship(
        'Product', secondary=product_category, back_populates='categories')

    def __init__(self, title, is_active, slug):
        self.title = title
        self.is_active = is_active
        self.slug = slug

    def __str__(self):
        return self.title

    def generate_unique_slug(self):
        base_slug = slugify(self.title)
        slug = base_slug
        counter = 1
        while Category.query.filter_by(slug=slug).first() is not None:
            slug = f"{base_slug}-{counter}"
            counter += 1
        self.slug = slug

    def save(self):
        db.session.add(self)
        db.session.commit()


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False,
                         default="default-product-image.jpg")
    product_id = db.Column(db.Integer, db.ForeignKey(
        'product.id'), nullable=False)

    product = db.relationship('Product', back_populates='images')

    def __init__(self, filename, product_id):
        self.filename = filename
        self.product_id = product_id

    def save(self):
        db.session.add(self)
        db.session.commit()

    def __str__(self):
        return self.filename


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float(), nullable=False)
    discounted_price = db.Column(db.Float(), nullable=False)
    is_active = db.Column(db.Boolean(), nullable=False, default=False)
    cover_photo = db.Column(
        db.String(255), default="default-product-cover.png")
    slug = db.Column(db.String(255), unique=True)
    created_at = db.Column(db.DateTime, default=get_current_time)

    comments = db.relationship(
        'Comment', back_populates='product', cascade='all, delete')
    images = db.relationship(
        'Image', back_populates='product', cascade='all, delete')
    categories = db.relationship(
        'Category', secondary=product_category, back_populates='products')
    favorited_by = db.relationship(
        'UserFavorite', back_populates='product', cascade='all, delete')

    def __init__(self, title, description, price, discounted_price, is_active, slug):
        self.title = title
        self.description = description
        self.price = price
        self.discounted_price = discounted_price
        self.is_active = is_active
        self.slug = slug

    def __str__(self):
        return self.title

    def generate_unique_slug(self):
        base_slug = slugify(self.title)
        slug = base_slug
        counter = 1
        while Product.query.filter_by(slug=slug).first() is not None:
            slug = f"{base_slug}-{counter}"
            counter += 1
        self.slug = slug

    def save(self):
        db.session.add(self)
        db.session.commit()


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    review = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=get_current_time)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey(
        'product.id'), nullable=False)

    user = db.relationship('User', back_populates='comments')
    product = db.relationship('Product', back_populates='comments')

    def __init__(self, review, user_id, product_id):
        self.review = review
        self.user_id = user_id
        self.product_id = product_id

    def save(self):
        db.session.add(self)
        db.session.commit()


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=get_current_time)

    def __init__(self, name, email, subject, message):
        self.name = name
        self.email = email
        self.subject = subject
        self.message = message

    def save(self):
        db.session.add(self)
        db.session.commit()


class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    is_active = db.Column(db.Boolean(), nullable=False, default=True)

    def __init__(self, name, email):
        self.name = name
        self.email = email

    def save(self):
        db.session.add(self)
        db.session.commit()
