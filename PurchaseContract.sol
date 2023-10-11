// SPDX-License-Identifier: MIT
pragma solidity ^0.6.0;

contract PurchaseContract {
    
    struct Purchase {
        string itemName;
        uint256 itemPrice;
        uint256 purchaseTime;
    }
    
    struct User {
        string name;
        string email;
        mapping(uint256 => Purchase) purchases; // Mapping purchase ID to Purchase struct
        uint256[] purchaseIds; // Array to store purchase IDs for iteration
    }
    
    mapping(address => User) public users; // Mapping user address to User struct
    
    event PurchaseAdded(address indexed user, uint256 purchaseId, string itemName, uint256 itemPrice, uint256 purchaseTime);

    function storeUser(string memory _name, string memory _email) public {
        User storage user = users[msg.sender];
        user.name = _name;
        user.email = _email;
    }

    function storePurchase(string memory _itemName, uint256 _itemPrice, uint256 _purchaseTime, uint256 _purchaseId) public {
        Purchase memory newPurchase = Purchase(_itemName, _itemPrice, _purchaseTime);
        users[msg.sender].purchases[_purchaseId] = newPurchase;
        users[msg.sender].purchaseIds.push(_purchaseId);
        
        emit PurchaseAdded(msg.sender, _purchaseId, _itemName, _itemPrice, _purchaseTime);
    }

    function getUser(address _userAddress) public view returns(string memory, string memory) {
        User memory user = users[_userAddress];
        return (user.name, user.email);
    }

    function getPurchase(address _userAddress, uint256 _purchaseId) public view returns(string memory, uint256, uint256) {
        Purchase memory purchase = users[_userAddress].purchases[_purchaseId];
        return (purchase.itemName, purchase.itemPrice, purchase.purchaseTime);
    }

    
}
