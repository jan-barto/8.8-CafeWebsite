from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
from flask_bootstrap import Bootstrap5
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = "adasdadvsvbgh"
bootstrap = Bootstrap5(app)


# ---------------- SECTION DB ----------------
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self):
        dictionary = {}
        for column in self.__table__.columns:
            dictionary[column.name] = getattr(self, column.name)
        return dictionary


@app.route("/", methods=(["GET", "POST"]))
def home():
    result = db.session.execute(db.select(Cafe).order_by(Cafe.id))
    data = result.scalars().all()
    unique_locations_tuple = db.session.query(Cafe.location).group_by(Cafe.location).all()
    unique_locations = [location[0] for location in unique_locations_tuple]

    if request.method == "POST":
        print(request.form.getlist('location'))
        locations = request.form.getlist('location')
        has_toilet = request.form.get('has_toilet')
        has_wifi = request.form.get('has_wifi')
        has_sockets = request.form.get('has_sockets')
        can_take_calls = request.form.get('can_take_calls')

        form_setting = {
            'locations': [(item, 'checked' if item in locations else '') for item in unique_locations],
            'has_toilet': has_toilet,
            'has_wifi': has_wifi,
            'has_sockets': has_sockets,
            'can_take_calls': can_take_calls,
        }

        query = db.session.query(Cafe)

        if locations:
            query = query.filter(Cafe.location.in_(locations))
        if has_toilet:
            query = query.filter(Cafe.has_toilet == (has_toilet == 'True'))
        if has_wifi:
            query = query.filter(Cafe.has_wifi == (has_wifi == 'True'))
        if has_sockets:
            query = query.filter(Cafe.has_sockets == (has_sockets == 'True'))
        if can_take_calls:
            query = query.filter(Cafe.can_take_calls == (can_take_calls == 'True'))

        data = query.order_by(Cafe.id).all()

        return render_template("index.html", data=data, settings=form_setting)

    # default setting
    form_setting = {
        'locations': [(item, 'checked') for item in unique_locations],
        'has_toilet': '',
        'has_wifi': '',
        'has_sockets': '',
        'can_take_calls': '',
    }

    return render_template("index.html", data=data, settings=form_setting)


# HTTP GET - Read random record
@app.route("/random")
def get_random_cafe():
    result = db.session.execute(db.select(Cafe))
    all_cafes = result.scalars().all()
    random_cafe = random.choice(all_cafes)

    return jsonify(cafe=random_cafe.to_dict())


# HTTP GET - Read all records
@app.route("/all")
def get_all_cafes():
    result = db.session.execute(db.select(Cafe))
    all_cafes = result.scalars().all()
    all_cafes_list = [cafe.to_dict() for cafe in all_cafes]

    return jsonify(cafes=all_cafes_list)


# HTTP GET - Search record
@app.route("/search")
def search_a_cafe():
    location = request.args.get('loc')
    result = db.session.execute(db.select(Cafe).where(Cafe.location == location))
    cafes = result.scalars().all()
    if cafes:
        all_cafes_list = [cafe.to_dict() for cafe in cafes]
        return jsonify(cafes=all_cafes_list)
    else:
        error = {"error": {"Not found": "We did not find any of cafes in your location."}}
        return error


# HTTP POST - Create Record
@app.route("/add", methods=["POST"])
def add_a_cafe():
    # print(request.form.get("name"))
    # print(request.form.get("map_url"))
    # print(request.form.get("img_url"))
    # print(request.form.get("location"))
    # print(request.form.get("has_toilet"))
    # print(request.form.get("has_wifi"))
    # print(request.form.get("has_sockets"))
    # print(request.form.get("can_take_calls"))
    # print(request.form.get("coffee_price"))

    new_entry = Cafe(
        name=request.form.get("name"),
        map_url=request.form.get("map_url"),
        img_url=request.form.get("img_url"),
        location=request.form.get("location"),
        seats=request.form.get("seats"),
        has_toilet=True if request.form.get("has_toilet") == "True" else False,
        has_wifi=True if request.form.get("has_wifi") == "True" else False,
        has_sockets=True if request.form.get("has_sockets") == "True" else False,
        can_take_calls=True if request.form.get("can_take_calls") == "True" else False,
        coffee_price=request.form.get("coffee_price")
    )
    db.session.add(new_entry)
    db.session.commit()
    return jsonify(response={"success": "Successfully added the new cafe."})


# HTTP PUT/PATCH - Update Record
@app.route("/update-price/<cafe_id>", methods=["POST", "PATCH"])
def update_the_price(cafe_id):
    print(cafe_id)
    cafe_to_update = db.get_or_404(Cafe, cafe_id)
    if cafe_to_update:
        cafe_to_update.coffee_price = request.args.get('new_price')
        db.session.commit()
        return jsonify(response={"success": "Successfully updated chosen cafe."}), 200
    else:
        error = {"error": {"Not found": "We did not find any cafe with given ID."}}, 404
        return error


# HTTP DELETE - Delete Record
@app.route("/report-closed/<cafe_id>", methods=["DELETE"])
def delete_cafe(cafe_id):
    api_key = "TopSecretAPIKey"
    cafe_to_delete = db.session.execute(db.select(Cafe).where(Cafe.id == cafe_id)).scalar()
    if request.args.get('api_key') == api_key:
        if cafe_to_delete:
            db.session.delete(cafe_to_delete)
            db.session.commit()
            return jsonify(response={"success": "Successfully deleted selected cafe."}), 200
        else:
            error = {"error": {"Not found": "We did not find any cafe with given ID."}}, 404
            return error
    else:
        return jsonify(response={"error": "Not valid API key used."}), 403


if __name__ == '__main__':
    app.run(debug=True)
