from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

# ------------------ DATA ------------------
movies = [
    {"id": 1, "name": "Avengers", "price": 200, "genre": "Action", "available_seats": 50},
    {"id": 2, "name": "Titanic", "price": 150, "genre": "Romance", "available_seats": 40},
    {"id": 3, "name": "Inception", "price": 180, "genre": "Sci-Fi", "available_seats": 30}
]

bookings = []
cart = []
booking_id_counter = 1


# ------------------ MODELS ------------------
class BookingRequest(BaseModel):
    customer_name: str = Field(min_length=2)
    movie_id: int
    tickets: int = Field(gt=0, le=10)


class NewMovie(BaseModel):
    name: str
    price: int
    genre: str
    available_seats: int


# ------------------ HELPERS ------------------
def find_movie(movie_id):
    for movie in movies:
        if movie["id"] == movie_id:
            return movie
    return None


def calculate_total(price, tickets):
    return price * tickets


# ------------------ DAY 1 ------------------
@app.get("/")
def home():
    return {"message": "Welcome to Movie Ticket Booking App 🎬"}


@app.get("/movies")
def get_movies():
    return {"total": len(movies), "data": movies}


@app.get("/movies/summary")
def summary():
    total_seats = sum(m["available_seats"] for m in movies)
    genres = list(set(m["genre"] for m in movies))
    return {"total_movies": len(movies), "total_seats": total_seats, "genres": genres}


@app.get("/movies/{movie_id}")
def get_movie(movie_id: int):
    movie = find_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


# ------------------ DAY 2 & 3 ------------------
@app.post("/book")
def book_ticket(req: BookingRequest):
    global booking_id_counter

    movie = find_movie(req.movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    if movie["available_seats"] < req.tickets:
        raise HTTPException(status_code=400, detail="Not enough seats")

    total = calculate_total(movie["price"], req.tickets)
    movie["available_seats"] -= req.tickets

    booking = {
        "booking_id": booking_id_counter,
        "customer": req.customer_name,
        "movie": movie["name"],
        "tickets": req.tickets,
        "total": total
    }

    bookings.append(booking)
    booking_id_counter += 1

    return booking


@app.get("/movies/filter")
def filter_movies(
    genre: Optional[str] = None,
    max_price: Optional[int] = None
):
    result = movies

    if genre is not None:
        result = [m for m in result if m["genre"].lower() == genre.lower()]

    if max_price is not None:
        result = [m for m in result if m["price"] <= max_price]

    return {"count": len(result), "data": result}


# ------------------ DAY 4 CRUD ------------------
@app.post("/movies")
def add_movie(movie: NewMovie):
    new_id = len(movies) + 1
    new_movie = {"id": new_id, **movie.dict()}
    movies.append(new_movie)
    return new_movie


@app.put("/movies/{movie_id}")
def update_movie(movie_id: int, price: Optional[int] = None):
    movie = find_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Not found")

    if price is not None:
        movie["price"] = price

    return movie


@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int):
    movie = find_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Not found")

    movies.remove(movie)
    return {"message": "Deleted"}


# ------------------ DAY 5 CART ------------------
@app.post("/cart/add")
def add_to_cart(movie_id: int, tickets: int = 1):
    movie = find_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    cart.append({"movie": movie["name"], "tickets": tickets})
    return {"message": "Added to cart"}


@app.get("/cart")
def view_cart():
    return cart


@app.post("/cart/checkout")
def checkout():
    if not cart:
        raise HTTPException(status_code=400, detail="Cart empty")

    total = 0
    for item in cart:
        movie = next(m for m in movies if m["name"] == item["movie"])
        total += calculate_total(movie["price"], item["tickets"])

    cart.clear()
    return {"message": "Booking successful", "total": total}


# ------------------ DAY 6 ------------------
@app.get("/movies/search")
def search_movies(keyword: str):
    result = [m for m in movies if keyword.lower() in m["name"].lower()]
    return {"count": len(result), "data": result}


@app.get("/movies/sort")
def sort_movies(order: str = "asc"):
    sorted_movies = sorted(movies, key=lambda x: x["price"], reverse=(order == "desc"))
    return sorted_movies


@app.get("/movies/page")
def paginate(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    return movies[start:start + limit]
