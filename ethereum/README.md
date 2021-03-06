# Ethereum Solidity scripting: A charity donation Smart Contract example

## Installing prerequisites

- Solidity compiler
    - Linux, using apt:<br>
      `sudo add-apt-repository ppa:ethereum/ethereum`<br>
      `sudo apt-get update`<br>
      `sudo apt-get install solc`
    - Linux, using snap:<br>
      `sudo snap install solc`
    - Windows:<br>
        - Download the Solidity compiler (solc) executable from [here](https://github.com/ethereum/solidity/releases)
        - Alternatives
            - [Guide 1](https://medium.com/@m_mcclarty/setting-up-solidity-on-windows-10-993a1d2c615c) <br>
            - [Guide 2](https://www.geeksforgeeks.org/how-to-install-solidity-in-windows/)
    - MacOS:<br>
      `brew update`<br>
      `brew upgrade`<br>
      `brew tap ethereum/ethereum`<br>
      `brew install solidity`

- Node.js
    - Linux, using apt:<br>
      `curl -sL https://deb.nodesource.com/setup_<major version>.<minor version> | sudo -E bash -`<br>
      `sudo apt-get install -y nodejs`
    - Linux, using snap:<br>
      `sudo snap install node --classic`
    - Windows, MacOS:<br>
      [Installers](https://nodejs.org/en/download/)

- Truffle, using Node Package Manager (npm)<br>
  `npm install -g truffle`

- Ganache, using Node Package Manager (npm)<br>
  `npm install -g ganache-cli`

Alternatively, you can use the [Remix web IDE](https://remix.ethereum.org/) having all prerequisites installed.

## Ethereum setup

You will use three different terminals. In this task, your IDE may help you, since many IDEs provide a separate Terminal
tab.<br>
We notate terminals using (cmd &lt;terminal&gt;), where &lt;terminal&gt; is the terminal number. E.g., (cmd 1).

- (cmd 1) `ganache-cli -p 8545`
- (cmd 2) `truffle init`<br>
  Make sure that when typing this you are in your home directory. This should create a truffle-config.js file in your
  home directory.
- (cmd 2) `nano truffle-config.js` and uncomment
    ```
    development: {
    host: "127.0.0.1",     // Localhost (default: none)
    port: 8545,            // Standard Ethereum port (default: none)
    network_id: "*",       // Any network (default: none)
    },
    ```
- (cmd 2) `truffle console`

You are now all set and ready to proceed.

## DonateToCharity: the script

### Description

The script's functionality is very simple. An owner deploys the script as a Smart Contract using a number of charity
Ethereum addresses. Other addresses can select to transfer funds to a given address using the contract, with a part of
the funds being donated to a selected charity.

The contract provides two `pay` methods for that purpose.<br>
The first method receives a `to` address and a charity id, and 10% of the funds sent are transferred to the charity
address instead. The remaining 90% is transferred to the `to` address.<br>
The second method receives a `to` address, a donation amount and a charity id. The donation amount in this case should
be between 1% and 50% of the funds sent, with the remaining transferred to the `to` address.<br>

Each time a donation is made, an event is emitted with the address that made the donation and the amount of the
donation.

The address that deployed the contract can also render it unusable and check at any time the top donor address, along
with the highest donation amount.

All addresses can also check the total amount of donations made so far.

### Running the script

To deploy the contract and verify its usability, the following should be done. The procedure described continues from
[Ethereum setup](#ethereum-setup).

- (cmd 3) Run `solc --bin ethereum/DonateToCharity.sol` and copy the produced binary.
- (cmd 2) Create a new variable by running `contractBIN = '<binary>'` and pasting the binary.
- (cmd 3) Run `solc --abi ethereum/DonateToCharity.sol` and copy the produced ABI.
- (cmd 2) Create a new variable by running `contractABI = <ABI>` and pasting the ABI.
- (cmd 2) Create a contract object using the ABI<br>
  `myContract = new web3.eth.Contract(contractABI)`
- (cmd 2) Get your account addresses and store them into variables `myAccount` and `myAccounts`.<br>
  `web3.eth.getAccounts().then(a => myAccount = a[0])`<br>
  `web3.eth.getAccounts().then(a => myAccounts = a)`
- (cmd 2) Deploy the contract from your first address using your last 3 addresses as the charity addresses.<br>
  __*NOTE*__: Your addresses are addresses generated by ganache, and you can always check them by going to (cmd 1).<br>
  At the end of the deployment, a `contractAddress` variable will have also been created containing the address the
  contract was deployed to.
  ```
  myContract.deploy({data: contractBIN, arguments:[[myAccounts[7], myAccounts[8], myAccounts[9]]]})
  .send({from: myAccount, gas: 4000000, gasPrice:'20000000000'})
  .then((instance) => {contractAddress = instance.options.address; console.log(contractAddress);})
  ```
- (cmd 2) Create a deployed contract object using the `contractAddress`<br>
  `myDeployedContract = new web3.eth.Contract(contractABI, contractAddress)`
- (cmd 2) We will send 2 Ether to address number 2, donating 10% of the amount to charity 2<br>
  `amountToSend = web3.utils.toWei("2", "ether")`<br>
  `myDeployedContract.methods.pay(myAccounts[1], 1).send({from: myAccount, gasPrice:'20000000000', gas: 200000, value:amountToSend})`
- (cmd 2) We should be the top donor<br>
  `myDeployedContract.methods.getHighestDonation().call()`
- (cmd 2) We send another 2 Ether using the same parameters, but this time setting a donation amount of 25%<br>
  `myDeployedContract.methods.pay(myAccounts[1], (amountToSend / 4).toString(), 1).send({from: myAccount, gasPrice:'20000000000', gas: 200000, value:amountToSend})`
- (cmd 2) What is the total amount of donations made?<br>
  `myDeployedContract.methods.donationSum.call()`
- (cmd 2) If everything went as expected, the changes should be reflected in the balance of our addresses<br>
  `web3.eth.getBalance(myAccounts[0])`<br>
  `web3.eth.getBalance(myAccounts[1])`<br>
  `web3.eth.getBalance(myAccounts[7])`<br>
  `web3.eth.getBalance(myAccounts[8])`<br>
  `web3.eth.getBalance(myAccounts[9])`
  