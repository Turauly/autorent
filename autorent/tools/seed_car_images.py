from app.database import SessionLocal
from app.models.car import Car
from app.models.car_photo import CarPhoto


IMAGE_MAP = {
    ("lada", "2107"): {
        "main": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1200&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1485291571150-772bcfc10da5?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    ("byd", "l"): {
        "main": "https://images.unsplash.com/photo-1553440569-bcc63803a83d?auto=format&fit=crop&w=1200&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1549924231-f129b911e442?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1511919884226-fd3cad34687c?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    ("bmw", "e40"): {
        "main": "https://images.unsplash.com/photo-1523983388277-336a66bf9bcd?auto=format&fit=crop&w=1200&q=80",
        "gallery": [
            "https://images.unsplash.com/photo-1494905998402-395d579af36f?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1502877338535-766e1452684a?auto=format&fit=crop&w=1200&q=80",
        ],
    },
}


def main() -> None:
    db = SessionLocal()
    try:
        cars = db.query(Car).all()
        updated = 0
        for car in cars:
            key = (car.brand.strip().lower(), car.model.strip().lower())
            image_set = IMAGE_MAP.get(key)
            if not image_set:
                continue

            car.main_image_url = image_set["main"]
            db.query(CarPhoto).filter(CarPhoto.car_id == car.id).delete()
            for url in image_set["gallery"]:
                db.add(CarPhoto(car_id=car.id, url=url))
            updated += 1

        db.commit()
        print(f"Updated images for {updated} cars")
    finally:
        db.close()


if __name__ == "__main__":
    main()
