from django.conf import settings

def save_user_to_mongodb(strategy, details, user=None, *args, **kwargs):
    # Never break login
    try:
        if user is None:
            return

        if settings.MONGO_DB is None:
            return

        email = details.get("email")
        if not email:
            return

        users = settings.MONGO_DB["users"]

        # DO NOT block auth if Mongo fails
        users.update_one(
            {"email": email},
            {"$setOnInsert": {
                "email": email,
                "name": details.get("fullname"),
                "provider": "google"
            }},
            upsert=True
        )

    except Exception as e:
        print("MongoDB error during login (ignored):", e)
