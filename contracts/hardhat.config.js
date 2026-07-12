require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: "0.8.19",
  networks: {
    "xlayer-mainnet": {
      url: "https://rpc.xlayer.tech",
      chainId: 196,
      accounts: process.env.DEPLOYER_KEY ? [process.env.DEPLOYER_KEY] : []
    },
    "xlayer-testnet": {
      url: "https://testrpc.xlayer.tech",
      chainId: 195,
      accounts: process.env.DEPLOYER_KEY ? [process.env.DEPLOYER_KEY] : []
    }
  }
};
