from flask import flash, abort, render_template, redirect, request, url_for
from start import app
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import login_manager
from flask_login import login_user, logout_user, login_required, current_user
from models import Product, Category, Comment, User, Contact, Subscriber
from forms import LoginForm, RegisterForm, CommentForm, ContactForm, SubscribeForm
from flask_paginate import get_page_parameter


# <==================== Context Processor ====================>

@app.context_processor
def categories_global():
    categories = Category.query.filter_by(
        is_active=True).order_by(Category.title.asc())
    return dict(categories=categories)


@app.context_processor
def favorites_count_global():
    favorites_count = 0
    if current_user.is_authenticated:
        favorites_count = len(
            [favorite.product for favorite in current_user.favorites if favorite.product.is_active])
    return dict(favorites_count=favorites_count)


@app.context_processor
def subscribe_form_global():
    subscribe_form = SubscribeForm()
    return dict(subscribe_form=subscribe_form)


# <==================== END Context Processor ====================>


# <==================== Auth ====================>

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/login/', methods=['GET', 'POST'])
def login_view():
    if current_user.is_authenticated:
        return redirect(url_for('index_view'))

    login_form = LoginForm()
    if request.method == "POST":
        user = User.query.filter_by(email=login_form.email.data).first()
        if login_form.validate():
            if user and check_password_hash(user.password, login_form.password.data):
                login_user(user)
                flash("You have successfully logged in.", "success")
                return redirect(url_for('index_view'))
            else:
                flash("Invalid email or password", "danger")
        else:
            for field, errors in login_form.errors.items():
                for error in errors:
                    flash(f"{error}", "danger")

    context = {
        "login_form": login_form,
    }
    return render_template("login.html", **context)


@app.route('/register/', methods=['GET', 'POST'])
def register_view():
    register_form = RegisterForm()
    if request.method == "POST":
        register_form = RegisterForm(request.form)
        if register_form.validate_on_submit():
            user = User(
                first_name=register_form.first_name.data,
                last_name=register_form.last_name.data,
                email=register_form.email.data,
                password=generate_password_hash(register_form.password.data),
                is_superuser=False
            )
            user.save()
            flash("Registration successful! You can now login.", "success")
            return redirect(url_for('login_view'))
        else:
            for field, errors in register_form.errors.items():
                for error in errors:
                    flash(f"{error}", "danger")

    context = {
        "register_form": register_form,
    }
    return render_template("register.html", **context)


@app.route('/logout/')
@login_required
def logout_view():
    logout_user()
    return redirect(url_for('login_view'))

# <==================== END Auth ====================>


# <==================== Page ====================>

@app.route('/', methods=['GET', 'POST'])
def index_view():
    page = request.args.get(get_page_parameter(), type=int, default=1)
    products = Product.query.filter_by(
        is_active=True).order_by(Product.created_at.desc()).paginate(page=page, per_page=9)
    context = {
        "products": products,
    }
    return render_template("shop.html", **context)


@app.route('/product/<product_slug>/', methods=['GET', 'POST'])
def detail_view(product_slug):
    product = Product.query.filter_by(
        slug=product_slug, is_active=True).first()

    if not product:
        abort(404)

    comments = Comment.query.filter_by(
        product_id=product.id).order_by(Comment.created_at.desc())
    categories = product.categories
    related_products = Product.query.filter(Product.categories.any(Category.id.in_(
        [category.id for category in categories])), Product.id != product.id, Product.is_active == True).limit(5).all()

    comment_form = CommentForm()
    if request.method == "POST":
        comment_form = CommentForm(request.form)
        if comment_form.validate_on_submit():
            comment = Comment(
                review=comment_form.review.data,
                user_id=current_user.id,
                product_id=product.id
            )
            comment.save()
            flash("Your comment has been successfully saved.", "success")
            return redirect(url_for('detail_view', product_slug=product_slug))

    context = {
        "product": product,
        "comments": comments,
        "related_products": related_products,
        "comment_form": comment_form,
    }

    if current_user.is_authenticated:
        favorites = [
            favorite.product for favorite in current_user.favorites if favorite.product.is_active]
        context["favorites"] = favorites

    return render_template("detail.html", **context)


@app.route('/category/<category_slug>/', methods=['GET', 'POST'])
def category_view(category_slug):
    category = Category.query.filter_by(
        slug=category_slug, is_active=True).first()

    if not category:
        abort(404)

    page = request.args.get(get_page_parameter(), type=int, default=1)
    products = Product.query.filter(Product.id.in_(
        [p.id for p in category.products]), Product.is_active == True).order_by(Product.created_at.desc()).paginate(page=page, per_page=9)
    context = {
        "products": products,
        "category": category,
        "selected_category_slug": category_slug,
    }
    return render_template("shop.html", **context)


@app.route('/contact/', methods=['GET', 'POST'])
def contact_view():
    contact_form = ContactForm()
    if request.method == "POST":
        contact_form = ContactForm(request.form)
        if contact_form.validate_on_submit():
            contact = Contact(
                name=contact_form.name.data,
                email=contact_form.email.data,
                subject=contact_form.subject.data,
                message=contact_form.message.data,
            )
            contact.save()
            flash('Your message has been sent successfully!', 'success')
            return redirect(url_for('contact_view'))
        else:
            for field, errors in contact_form.errors.items():
                for error in errors:
                    flash(f"Error in {field}: {error}", "danger")
    context = {
        "contact_form": contact_form
    }
    return render_template("contact.html", **context)


@app.route('/search/', methods=['GET'])
def search_products_view():
    query = request.args.get('query')
    page = request.args.get(get_page_parameter(), type=int, default=1)
    products = Product.query.filter(Product.title.ilike(
        f'%{query}%'), Product.is_active == True).order_by(Product.created_at.desc()).paginate(page=page, per_page=9)
    context = {
        'query': query,
        'products': products
    }
    return render_template('shop.html', **context)


@app.route('/user/favorites/', methods=['GET', 'POST'])
@login_required
def favorites_view():
    favorites = [
        favorite.product for favorite in current_user.favorites if favorite.product.is_active]

    context = {
        "favorites": favorites,
    }
    return render_template("favorites.html", **context)


@app.route('/add_favorite/<string:product_slug>/')
@login_required
def add_favorite_view(product_slug):
    product = Product.query.filter_by(slug=product_slug).first()
    current_user.add_favorite(product)
    return redirect(request.referrer)


@app.route('/remove_favorite/<string:product_slug>/')
@login_required
def remove_favorite_view(product_slug):
    product = Product.query.filter_by(slug=product_slug).first()
    current_user.remove_favorite(product)
    return redirect(request.referrer)


@app.route('/subscribe/', methods=['POST'])
def subscribe_view():
    subscribe_form = SubscribeForm()
    if request.method == "POST":
        subscribe_form = SubscribeForm(request.form)
        if subscribe_form.validate_on_submit():
            subscriber = Subscriber(
                name=subscribe_form.name.data,
                email=subscribe_form.email.data
            )
            flash('You have successfully subscribed!', 'subscribe_form_success')
            subscriber.save()
            return redirect(request.referrer)
        else:
            for field, errors in subscribe_form.errors.items():
                for error in errors:
                    flash(f"Error in {field}: {error}",
                          "subscribe_form_danger")
    return redirect(request.referrer)


# <==================== END Page ====================>
