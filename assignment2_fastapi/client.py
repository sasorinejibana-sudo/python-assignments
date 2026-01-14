import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any

import requests

BASE_URL = "http://127.0.0.1:8000"


def login(username: str, password: str) -> Dict[str, Any]:
    url = f"{BASE_URL}/api/auth/login"
    payload = {"username": username, "password": password}
    r = requests.post(url, json=payload, timeout=15)

    print(f"Login status: {r.status_code}")
    if r.status_code != 200:
        # FastAPI returns JSON detail for errors
        try:
            print("Login error body:", r.json())
        except Exception:
            print("Login error body (raw):", r.text)
        raise RuntimeError("Login failed")

    data = r.json()
    # Evidence-friendly output
    print("Login response:", json.dumps(data, indent=2))
    return data


def get_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def get_products(token: str) -> None:
    url = f"{BASE_URL}/api/products"
    r = requests.get(url, headers=get_headers(token), timeout=15)
    print(f"GetProducts status: {r.status_code}")

    try:
        body = r.json()
        print("Response:", json.dumps(body, indent=2))
    except Exception:
        print("Response (raw):", r.text)


def get_product(token: str, product_id: int) -> Optional[Dict[str, Any]]:
    url = f"{BASE_URL}/api/products/{product_id}"
    r = requests.get(url, headers=get_headers(token), timeout=15)
    print(f"GetProduct({product_id}) status: {r.status_code}")

    if r.status_code == 200:
        product = r.json()
        print("Product JSON:", json.dumps(product, indent=2))
        return product

    # Error case
    try:
        print("Error:", r.json())
    except Exception:
        print("Error (raw):", r.text)
    return None


def add_product(token: str, name: str, description: Optional[str], price: float) -> None:
    url = f"{BASE_URL}/api/products"
    payload = {"name": name, "description": description, "price": price}
    r = requests.post(url, headers=get_headers(token), json=payload, timeout=15)
    print(f"AddProduct status: {r.status_code}")

    # Print body for evidence
    if r.text:
        try:
            print("Response:", json.dumps(r.json(), indent=2))
        except Exception:
            print("Response (raw):", r.text)
    else:
        print("Response body is empty.")


def prompt_float(prompt: str) -> float:
    while True:
        s = input(prompt).strip()
        try:
            return float(s)
        except ValueError:
            print("Invalid number, try again.")


def main():
    print("=== ProductClient (Python CLI) ===")
    print(f"API Base URL: {BASE_URL}")

    last_product_json: Optional[Dict[str, Any]] = None
    token: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    expires_at: Optional[str] = None

    while True:
        # Login loop
        while token is None:
            u = input("\nUsername (admin/privuser) or 'exit': ").strip()
            if u.lower() == "exit":
                print("Exiting.")
                sys.exit(0)

            p = input("Password: ").strip()

            try:
                auth = login(u, p)
                token = auth["token"]
                username = auth["username"]
                role = auth["role"]
                expires_at = auth["expiresAt"]
                print(f"\nLogged in as {username} (role: {role}), token expires at: {expires_at} (UTC)")
            except Exception as e:
                print(f"Login failed: {e}")
                token = None

        # Menu loop
        print("\n=== Main Menu ===")
        print(f"Current user: {username} (role: {role})")
        print("1) GetProducts")
        print("2) GetProduct(id) and store JSON object")
        print("3) AddProduct (admin only; non-admin should get 403)")
        print("4) Show last stored product JSON")
        print("5) Save last stored product JSON to file")
        print("9) Logout")
        print("0) Exit")
        choice = input("Choose option: ").strip()

        if choice == "1":
            get_products(token)

        elif choice == "2":
            s = input("Enter Product ID: ").strip()
            if not s.isdigit():
                print("Invalid ID.")
                continue
            pid = int(s)
            last_product_json = get_product(token, pid)
            if last_product_json is not None:
                print("Stored product JSON object in memory.")

        elif choice == "3":
            name = input("Product name: ").strip()
            description = input("Description (optional): ").strip()
            description = description if description else None
            price = prompt_float("Price: ")
            add_product(token, name, description, price)

        elif choice == "4":
            if last_product_json is None:
                print("No product JSON stored yet.")
            else:
                print("Last stored product JSON:")
                print(json.dumps(last_product_json, indent=2))

        elif choice == "5":
            if last_product_json is None:
                print("No product JSON stored yet.")
                continue
            filename = f"product_{last_product_json.get('id', 'unknown')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(last_product_json, f, ensure_ascii=False, indent=2)
            print(f"Saved to file: {filename}")

        elif choice == "9":
            print("Logging out...")
            token = None
            username = None
            role = None
            expires_at = None
            last_product_json = None

        elif choice == "0":
            print("Exiting.")
            sys.exit(0)

        else:
            print("Unknown option.")


if __name__ == "__main__":
    main()
