from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from solcx import compile_standard, install_solc
import json
import os
from web3 import Web3

app = FastAPI()

origins = ["*"]

# MySQL database connection configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "jkiller8",
    "database": "DecentralizedTradingSystem"
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# type your address here
w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))
# Default is 1337 or with the PORT in your Gaanche
chain_id = 1337

# Find in you account
my_address = "0x2aC3a79dc3Bf4Ff10FD3506c97948Be3396f6dE7"
# Find in you account
private_key = "0x4326a3d66b441dbdf3072f1ca64e2d34562dcda1d7d4f96f89dfbddf637bc4f0"

# Compile and deploy contract
with open("./PurchaseContract.sol", "r") as file:
    purchase_contract_file = file.read()

install_solc("0.6.0")
compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"PurchaseContract.sol": {"content": purchase_contract_file}},
        "settings": {
            "outputSelection": {
                "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
            }
        },
    },
    solc_version="0.6.0",
)

with open("compiled_code.json", "w") as file:
    json.dump(compiled_sol, file)

# Get bytecode and abi
bytecode = compiled_sol["contracts"]["PurchaseContract.sol"]["PurchaseContract"]["evm"]["bytecode"]["object"]
abi = compiled_sol["contracts"]["PurchaseContract.sol"]["PurchaseContract"]["abi"]

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
        return {"message": "Login successful", "success": true}
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
    image = data['image']

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO DigitalAssets (AssetName, Description, Price, CategoryID, OwnerID, Image) VALUES (%s, %s, %s, %s, %s, %s);",
        (asset_name, description, price, category_id, owner_id, image)
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
    image = data['image']


    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE DigitalAssets SET AssetName = %s, Description = %s, Price = %s, Image = %s WHERE AssetID = %s;",
        (asset_name, description, price, image, asset_id)
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
    asset_id = data['asset_id']
    item_name = data['item_name']
    item_price = data['item_price']
    purchase_time = data['purchase_time']
    purchase_id = data['purchase_id'] # Ensure this is unique for each transaction

    # Database operations
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    # get user information with buyer_id
    cursor.execute("SELECT * FROM Users WHERE UserID = %s", (buyer_id,))
    user = cursor.fetchone()
    user_name = user[1]

    user_email = user[2]


    PurchaseContract = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(my_address)

    try:

        # Construct and send transaction
        transaction = PurchaseContract.constructor().build_transaction(
            {
                "chainId": chain_id,
                "gasPrice": w3.eth.gas_price,
                "from": my_address,
                "nonce": nonce,
            }
        )
        transaction.pop('to')

        signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        purchase_contract = w3.eth.contract(address=tx_receipt['contractAddress'], abi=abi)

        # write in a file the contract address and abi
        with open("contract_address.txt", "w") as file:
            file.write(tx_receipt['contractAddress'])
            
        with open("contract_abi.txt", "w") as file:
            file.write(json.dumps(abi))


        cursor.execute(
            "INSERT INTO Contracts (ContractAddress, ABI, userid) VALUES (%s, %s, %s);",
            (tx_receipt['contractAddress'], json.dumps(abi), buyer_id)
        )
        connection.commit()
        

        # Store Purchase details
        store_transaction = purchase_contract.functions.storePurchase(
            item_name, item_price, purchase_time, purchase_id
        ).build_transaction(
            {
                "chainId": chain_id,
                "gasPrice": w3.eth.gas_price,
                "from": my_address,
                "nonce": nonce + 1,
            }
        )

        # Store User details
        store_user_transaction = purchase_contract.functions.storeUser(user_name, user_email).build_transaction(
            {
                "chainId": chain_id,
                "gasPrice": w3.eth.gas_price,
                "from": my_address,
                "nonce": nonce + 2,  # Increment nonce for the second transaction
            }
        )

        # Sign and send storeTransaction
        signed_store_txn = w3.eth.account.sign_transaction(store_transaction, private_key=private_key)
        send_store_tx = w3.eth.send_raw_transaction(signed_store_txn.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(send_store_tx)

        # Sign and send storeUser transaction
        signed_store_user_txn = w3.eth.account.sign_transaction(store_user_transaction, private_key=private_key)
        send_store_user_tx = w3.eth.send_raw_transaction(signed_store_user_txn.rawTransaction)
        tx_receipt_user = w3.eth.wait_for_transaction_receipt(send_store_user_tx)


    except Exception as e:
        # Logging the error and returning a 500 error response
        print("An error occurred: ", str(e))
        raise HTTPException(status_code=500, detail="An error occurred while processing the transaction.")


    # Commit to DB and close connection
    connection.commit()
    cursor.close()
    connection.close()

    return {"message": "Transaction made successfully"}


@app.get("/view_transaction/{buyer_id}/")
async def view_transaction(buyer_id: int):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Contracts WHERE userid=%s", (buyer_id,))
    contracts = cursor.fetchall()
    
    all_purchases = []

    for contract in contracts:
        contract_address = contract[1]
        contract_abi = contract[2]

        # Create a contract object
        contract_instance = w3.eth.contract(address=contract_address, abi=contract_abi)

        # Define an event filter
        event_filter = contract_instance.events.PurchaseAdded.create_filter(fromBlock=0)

        # Fetch all entries from the event log
        event_logs = event_filter.get_all_entries()

        # Iterate through the event logs and extract purchase information
        for event in event_logs:
            purchase_id = event['args']['purchaseId'] 
            user_name, user_email = contract_instance.functions.getUser(my_address).call()
            item_name, item_price, purchase_time = contract_instance.functions.getPurchase(my_address, purchase_id).call()

            purchase = {
                "contract_address": contract_address,
                "purchaseId": purchase_id,
                "itemName": item_name,
                "itemPrice": item_price,
                "purchaseTime": purchase_time,
                "userName": user_name,
                "userEmail": user_email
            }
            
            all_purchases.append(purchase)

    # Close cursor and connection
    cursor.close()
    connection.close()

    # Return the fetched purchases as JSON
    return {"purchases": all_purchases}
