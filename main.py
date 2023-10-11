from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

app = FastAPI()

origins = ["*"]

# MySQL database connection configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "111111a",
    "database": "DecentralizedTradingSystem"
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/register/")
async def register_user(request: Request):
    data = await request.json()
    username = data['username']
    email = data['email']
    password = data['password']

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO Users (Username, Email, Password) VALUES (%s, %s, %s);",
            (username, email, password)
        )
        connection.commit()
    except mysql.connector.IntegrityError:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    finally:
        cursor.close()
        connection.close()
    return {"message": "User registered successfully"}

@app.post("/login/")
async def login(request: Request):
    data = await request.json()
    username = data['username']
    password = data['password']

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM Users WHERE Username = %s AND Password = %s;",
        (username, password)
    )
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if user:
        return {"message": "Login successful"}
    else:
        raise HTTPException(status_code=400, detail="Invalid credentials")

@app.post("/add_asset/")
async def add_asset(request: Request):
    data = await request.json()
    asset_name = data['asset_name']
    description = data['description']
    price = data['price']
    category_id = data['category_id']
    owner_id = data['owner_id']
    staked = data['staked']
    rewards = data['rewards']
    balance = data['balance']
    image = data['image']

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO DigitalAssets (AssetName, Description, Price, CategoryID, OwnerID, Staked, Rewards, Balance, Image) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);",
        (asset_name, description, price, category_id, owner_id, staked, rewards, balance, image)
    )
    connection.commit()
    cursor.close()
    connection.close()
    return {"message": "Asset added successfully"}

@app.get("/asset/")
async def view_asset():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM DigitalAssets")
    asset = cursor.fetchall()
    cursor.close()
    connection.close()
    if asset:
        return asset
    else:
        raise HTTPException(status_code=400, detail="Asset not found")

@app.post("/update_asset/{asset_id}/")
async def update_asset(request: Request, asset_id: int):
    data = await request.json()
    asset_name = data['asset_name']
    description = data['description']
    price = data['price']
    staked = data['staked']
    rewards = data['rewards']
    balance = data['balance']
    image = data['image']


    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE DigitalAssets SET AssetName = %s, Description = %s, Price = %s, Staked = %s, Rewards = %s, Balance = %s, Image = %s WHERE AssetID = %s;",
        (asset_name, description, price, staked, rewards, balance, image, asset_id)
    )
    connection.commit()
    cursor.close()
    connection.close()
    return {"message": "Asset updated successfully"}

@app.delete("/delete_asset/{asset_id}/")
async def delete_asset(asset_id: int):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM DigitalAssets WHERE AssetID = %s;", (asset_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return {"message": "Asset deleted successfully"}

@app.post("/make_transaction/")
async def make_transaction(request: Request):
    data = await request.json()
    buyer_id = data['buyer_id']
    seller_id = data['seller_id']
    asset_id = data['asset_id']
    transaction_status = data['transaction_status']
    transaction_type = data['transaction_type']

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO TransactionHistory (BuyerID, SellerID, AssetID, TransactionStatus, TransactionType) VALUES (%s, %s, %s, %s, %s);",
        (buyer_id, seller_id, asset_id, transaction_status, transaction_type)
    )
    connection.commit()
    cursor.close()
    connection.close()
    return {"message": "Transaction made successfully"}

@app.get("/transaction_history/{user_id}/")
async def view_transaction_history(user_id: int):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM TransactionHistory WHERE BuyerID = %s OR SellerID = %s;", (user_id, user_id))
    transactions = cursor.fetchall()
    cursor.close()
    connection.close()
    return transactions

# ... Additional routes for functionalities such as handling smart contracts, etc. ...
