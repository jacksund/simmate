# Ethereum

--------------------------------------------------------------------------------

## About

The `ethereum` app stores Ethereum wallets and their transactions in the Simmate database. Data is pulled from either the [Alchemy](https://www.alchemy.com/) or [Etherscan](https://etherscan.io/) API.

--------------------------------------------------------------------------------

## Installation

1. This app is installed by default. If you removed it, add it back with:
``` bash
simmate config add ethereum
```

2. Choose a backend (`alchemy` or `etherscan`) and set its API key:
``` bash
simmate config update "ethereum.backend=alchemy"
simmate config update "ethereum.alchemy.api_key=YOUR_KEY_HERE"
```

3. Update your database to include custom tables from the app:
``` shell
simmate database update
```

--------------------------------------------------------------------------------
