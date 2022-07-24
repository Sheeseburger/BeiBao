from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os
import ast # module for converting str to dict
from wardrobe import login_required,removeBg,color,random_name,get_temperature,get_look,item_check,allowed_file,outfit_add,filter_rows
from PIL import Image
from collections import Counter
import numpy as np

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = 'static/items/'

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///wardrobe.db")


if not os.environ.get("WEATHER_API_KEY"):
    raise RuntimeError("WEATHER_API_KEY not set")

@app.route("/")
@login_required
def index():
    """Show homepage"""
    rows = db.execute('SELECT type,picture,Users_Item.id AS id,name,bag FROM Users_Item JOIN Item ON item_id=Item.id WHERE user_id=? AND wish_list=0',session['user_id'])
    jacket,underjacket,pants = filter_rows(rows)
    return render_template("index.html",pants=pants,len_pants = len(pants),underjacket=underjacket,len_underjacket=len(underjacket),jacket=jacket,len_jacket=len(jacket))

@app.route('/delete',methods=["POST"])
def delete():
    """Delete button from wardrobe and wannabuy """
    id=request.form.get('delete_item') # get item id
    if not id:
        flash("Something went wrong,try again.")
        return redirect('/')
    rows = db.execute('SELECT * FROM Outfits_Item JOIN Users_Item on Users_Item.id=Outfits_Item.item_id WHERE Outfits_Item.item_id=? AND Users_Item.user_id=?',id,session['user_id'])
    print(rows)
    if rows:
        flash('Delete outfit with this item first')
        return redirect('/outfit')
    if int(request.form.get('action')) == 0:
        db.execute('UPDATE Users_Item SET bag=0 WHERE user_id=? AND id=?',session['user_id'],id)
        return redirect('/')
    else:
        path = request.form.get('delete_link')
        if not path:
            flash('something went wrong')
            return redirect('/outfit')
        db.execute('DELETE FROM Users_Item WHERE user_id=? AND id=?',session['user_id'],id) #deleting from DB
        os.remove(path) #deleting from static/items
        return redirect('/')

@app.route('/backpack_add',methods=['POST'])
def backpack_add():
    """Add button that insert items into backpack"""
    id = request.form.get('backpack_add')
    if not id:
        flash("Something went wrong,try again.")
        return redirect('/')
    db.execute('UPDATE Users_Item SET bag=1 WHERE user_id=? AND id=?',session['user_id'],id)
    flash("Your item was added to backpack")
    return redirect('/')

@app.route('/backpack_remove',methods=['POST'])
def backpack_remove():
    """Remove button from backpack"""
    id = request.form.get('backpack_remove')
    if not id:
        flash("Something went wrong,try again.")
        return redirect('/backpack')
    db.execute('UPDATE Users_Item SET bag=0 WHERE user_id=? AND id=?',session['user_id'],id)
    return redirect('/backpack')

@app.route('/backpack')
@login_required
def backpack():
    """Backpack view"""
    rows=db.execute('SELECT type,picture,Users_Item.id AS id,name,bag FROM Users_Item JOIN Item ON item_id=Item.id WHERE user_id=? AND bag=1',session['user_id'])
    jacket,underjacket,pants = filter_rows(rows)
    return render_template("backpack.html",pants=pants,len_pants = len(pants),underjacket=underjacket,len_underjacket=len(underjacket),jacket=jacket,len_jacket=len(jacket))

@app.route('/wannabuy',methods=['GET','POST'])
@login_required
def wannabuy():
    """Wannabuy page """
    if request.method == 'POST':
        if not request.files['photo']:
            flash('Add photo first.')
            return redirect('/wannabuy')
        file = request.files['photo']
        answer = img_process(file)
        if answer:
            db.execute('INSERT INTO Users_Item (user_id,picture,wish_list,dominant_color) VALUES (?,?,1,?)',session['user_id'],answer['path'],answer['color'])
            flash('Your item was added')
        else:
            flash('Something wrong with extension. (jpeg,png,jpg)')
        return redirect('/wannabuy')
    else:
        item = db.execute('SELECT DISTINCT name,type,id FROM Item')
        rows = db.execute('SELECT * FROM Users_Item WHERE user_id=? AND wish_list=true',session['user_id'])
        return render_template('wannabuy.html',rows=rows,len=len(rows),items=item)

@app.route('/create',methods=['POST','GET'])
@login_required
def create():
    if request.method =='POST':
        rows = request.form.getlist('cb') # request list of checked checkboxs
        buffer = [] # list of list of dicts
        for row in rows: # convert str to dict
            buffer.append(ast.literal_eval(row))
        rows = buffer
        pants_check = 0
        tshirt_check = 0
        tmp = []
        id = []
        for i in range(len(rows)):
            id.append(rows[i]['id'])
            if rows[i]['type'] == 'Pants':
                pants_check += 1
            elif rows[i]['name'] in ['T-shirt','Top']:
                tshirt_check += 1
            tmp.append(rows[i]['name'])
        counter = Counter(tmp)
        for count in counter:
            if counter[count] > 1:
                flash('Pick only one item of the type')
                return redirect('/create')
        if pants_check != 1 or tshirt_check > 1:
            flash('Pick at least one pair of pants and no more than one item per item type')
            return redirect('/create')
        outfit_add(id)
        return redirect('/')
    else:
        rows = db.execute('SELECT picture,Users_Item.id AS id,type,name FROM Users_Item JOIN Item ON item_id=Item.id WHERE user_id=? AND wish_list=0 ORDER BY type DESC,name',session['user_id'])
        return render_template('create.html',rows=rows,len=len(rows))

@app.route('/outfit')
@login_required
def outfit():
    """Present outfit page """
    rows = db.execute('SELECT outfits_id,Outfits_Item.item_id,picture FROM Outfits_Item JOIN Users_Outfits ON Outfits_Item.outfits_id = Users_Outfits.id JOIN Users_Item ON Outfits_Item.item_id=Users_Item.id WHERE Users_Outfits.user_id=?',session['user_id'])
    if rows:
        tmp = [rows[0]['picture']]
        output = [] # list of list like [[item1,item2,item3],[item4,item5,item6]]
        output_id = [] # list of outfits id`s for correct remove button
        tmp_id = rows[0]['outfits_id']
        output_id.append(tmp_id)

        for i in range(1,len(rows)):
            if rows[i]['outfits_id'] == tmp_id: # make a list of one outfit (tshirt,sweater,pants)
                tmp.append(rows[i]['picture'])
            else: # outfit id changes so new outfit is processing
                output.append(tmp)
                tmp = []
                tmp.append(rows[i]['picture'])
                tmp_id = rows[i]['outfits_id']
                output_id.append(tmp_id)
        output.append(tmp)
        return render_template('outfit.html',rows=output,len=len(output),id=output_id)
    return render_template('outfit.html',rows=0,len=0,id=0)

@app.route('/outfits_delete',methods=['POST'])
@login_required
def outfits_delete():
    """Remove button for outfit """
    id = request.form.get('delete_item')
    if not id:
        flash('something went wrong')
        return redirect('/outfit')
    db.execute('DELETE FROM Outfits_Item WHERE Outfits_Item.outfits_id=?',id)
    db.execute('DELETE FROM Users_Outfits WHERE id=?',id)
    return redirect('/outfit')


@app.route('/generate',methods=['GET','POST'])
@login_required
def generate():
    """Generate outfits by temperature and a bit of luck """
    if request.method == 'POST':

        temperature = get_temperature(session['city_name'])
        if not temperature:
            flash('Something wrong with your city name. Try to log out and type another city')
            temperature = {'temp':0,'weather':'Error with city'}
        rows = db.execute('SELECT name,type,picture,Users_Item.id AS id,temperature,dominant_color FROM Users_Item JOIN Item ON item_id=Item.id WHERE user_id=? AND wish_list=0 ORDER BY type DESC,name DESC,temperature DESC',session['user_id'])
        if not rows:
            flash('Sorry,you dont have enough items.')
            return redirect('/')
        outlook = get_look(temperature,rows)
        if not outlook:
            flash('Sorry,you dont have enough items')
        return render_template('generate.html',rows=outlook,temperature=temperature['temp'],weather=temperature['weather'])
    else:
        return render_template('generate.html')

@app.route('/outfit_add',methods=['POST','GET'])
@login_required
def outfit_add_btn():
    """Button for adding outfit to favourite so it can be storaged in DB """
    if request.method == 'POST':
        if not request.form.get('outfit_add_input'):
            flash('Something went wrong :(')
            return redirect('/generate')

        rows = request.form.get('outfit_add_input') # get ids of items
        rows = list(rows.split(' ')) # spliting to form a list
        rows.remove('')
        outfit_add(rows)
        return redirect('/outfit')
    else:
        return redirect('/')

@app.route('/trend')
@login_required
def trend():
    """Render page with instagram """
    return render_template('trend.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user data
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("You forgot to enter username.")
            return redirect('/login')

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("You forgot to enter password.")
            return redirect('/login')

        elif not request.form.get("city"):
            flash("You forgot to enter your city.")
            return redirect('/login')
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Something wrong with your password")
            return redirect('/login')

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session['city_name'] = request.form.get('city') # get city from user
        # Redirect user to home page
        return redirect("/")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("You forgot to enter username.")
            return redirect('/register')

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("You forgot to enter password.")
            return redirect('/register')

        if len(request.form.get("password")) < 8:
            flash("Password must have at least 8 symbols")
            return redirect('/register')

        elif request.form.get("password") != request.form.get("confirmation"):
            flash("Your password and confirmation dont match. :(")
            return redirect('/register')
        # Query database for username
        rows = db.execute("SELECT * FROM Users WHERE username = ?", request.form.get("username"))

        # Ensure username is free
        if len(rows) != 0:
            flash("Username is already used.")
            return redirect('/register')

        lang = 'english'
        db.execute("INSERT INTO Users (username,hash,registration_date,language) VALUES (?,?,julianday('now'),?)",
                   request.form.get("username"), generate_password_hash(request.form.get("password")),lang)
        # Redirect user to login page
        return render_template("login.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/add",methods=["POST","GET"])
@login_required
def add():
    """Adds items to user"""
    if request.method == "POST":
        if not request.form.get('item_types_choice'):
            flash('No selected type')
            return redirect('/add')
        item = request.form.get('item_types_choice').rstrip().lstrip() # get item name
        item = item.capitalize()

        check = item_check(item) #checking if item is correct
        if not check:
            flash('Wrong item name :(')
            return redirect('/add')
        if not request.files['photo']:
            flash('Add image first.')
            return redirect('/add')
        file = request.files['photo'] # get img
        img = img_process(file) # removeBG, return path and primary color
        if img:
            db.execute('INSERT INTO Users_Item (user_id,picture,item_id,wish_list,dominant_color) VALUES (?,?,?,false,?)',session['user_id'],img['path'],request.form.get(item),img['color'])
            flash("Your item was added")
            return redirect('/add')
        else:
            flash('Something wrong with extension and/or filename. (png,jpeg,jpg)')
            return redirect('/add')
    else:
        item = db.execute('SELECT name,type,id FROM Item')
        #translator = Translator() Translate items(bad translate dont work as needed)
        #for i in item:
        #    i['name'] = translator.translate(i['name'],dest=session['language']).text
        return render_template("add.html",items=item)

@app.route('/wardrobe_add',methods=['POST'])
@login_required
def wardrobe_add():
    """Add item to wardrobe from wannabuy """
    path = request.form.get('item_link') # request img link
    item = request.form.get('item_types_choice') # request item name
    check = item_check(item) # check if item name correct
    if not check:
        flash('Pick type please')
        return redirect('/wannabuy')

    item_id = request.form.get(item) # request item id
    primaryColor = color(path)
    db.execute('UPDATE Users_Item SET wish_list=0,dominant_color=?,item_id=? WHERE picture = ?',primaryColor,item_id,path)
    return redirect('/wannabuy')

def img_process(file):
        filename = file.filename
        filename = secure_filename(filename)
        if allowed_file(filename):
            img = Image.open(file) # opening via PIL

            height, width = img.size

            if height < 400 or width < 400:
                flash('Something wrong with image shape')
                return 0

            if img:
                filename = random_name() # create random name for storing

                path = os.path.join(app.config['UPLOAD_FOLDER'], filename) # making path to img

                img = Image.fromarray(np.uint8(removeBg(img))) # removing bg
                img.thumbnail((420,420))
                img.save(path,optimize=True,quality=30)

                #primaryColor = color(path)

                answ = {'path':path,'color':'FFFFFF'}
                return answ
        else:
            return 0