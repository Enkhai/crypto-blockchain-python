// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.0;

contract DonateToCharity {

    // the address that deployed the contract
    address payable owner;
    // an array of payable addresses for the charities
    address payable[] private charities;
    // highest donation and top donor information
    address private topDonor;
    uint private highestDonation;
    // total amount gathered in donations
    uint public donationSum;

    // the constructor accepts a list of charity addresses and deploys the contract
    // by setting the owner to the address that deployed it,
    // the charity addresses provided as an argument,
    // and the highest donation amount and total donation sum to 0
    constructor(address payable[] memory _charities) {
        owner = payable(msg.sender);
        charities = _charities;
        highestDonation = 0;
        donationSum = 0;
    }

    // a modifier allowing only the person that deployed the contract to access certain methods
    // if an address other than the sender attempts this, the transaction is reverted with an
    // appropriate message
    modifier ownerOnly {
        require(msg.sender == owner, "Only the owner can use this.");
        _;
    }

    // a method for rendering the contract unusable
    function destroy() public ownerOnly {
        selfdestruct(owner);
    }

    // the event that will be emitted every time a donation is made
    event DonationMade(address addr, uint amount);

    // donation method variation no. 1
    // the method receives a 'to' address and the index of the charity for the donation to be made to
    // and returns the amount of the donation that was made
    function pay(address payable to, uint8 charityId) public payable returns (uint donation) {
        // cannot specify a charity that does not exist within the given options
        require(charityId < charities.length, "Incorrect charity ID.");
        // a donation of 10% will be made each time
        donation = msg.value / 10;

        // if the current donation is higher than the highest donation,
        // replace the highest donation info
        if (donation > highestDonation) {
            highestDonation = donation;
            topDonor = msg.sender;
        }

        // make the donation
        charities[charityId].transfer(donation);
        donationSum += donation;
        emit DonationMade(msg.sender, donation);

        // and transfer the remaining funds to the specified address
        to.transfer(msg.value - donation);
    }

    // donation method variation no. 2
    // the method receives a 'to' address, a donation amount
    // and the index of the charity for the donation to be made to
    function pay(address payable to, uint donation, uint8 charityId) public payable {
        // the donation should be between 1% and 50% of the sent amount
        require(donation >= msg.value / 100, "The donation should be higher than or equal to 1% of the paying amount.");
        require(donation <= msg.value / 2, "The donation should be lower than or equal to 50% of the paying amount.");
        // cannot specify a charity that does not exist within the given options
        require(charityId < charities.length, "Incorrect charity ID.");

        // if the current donation is higher than the highest donation,
        // replace the highest donation info
        if (donation > highestDonation) {
            highestDonation = donation;
            topDonor = msg.sender;
        }

        // make the donation
        charities[charityId].transfer(donation);
        donationSum += donation;
        emit DonationMade(msg.sender, donation);

        // and transfer the remaining funds to the specified address
        to.transfer(msg.value - donation);
    }

    // a method that returns the address of the top donor
    // and the amount of the highest donation the top donor made
    function getHighestDonation() public ownerOnly view returns (address, uint) {
        return (topDonor, highestDonation);
    }
}