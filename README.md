# Balanca

Selenium script to automate online grocery shopping at my favourite bulk food store.

## Setup

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Put your shop credentials in `.env`:

```sh
BALANCA_USERNAME=your-user
BALANCA_PASSWORD=your-password
```

Then edit `products.yaml` and run:

```sh
python main.py
```

Chrome will stay open on the cart page so you can review the order before closing it.
