# py_folio
A small python application to return values of held cryptocurrencies from coinmarketcap.

This application does not offer logging or graphing or anything; it simply returns the value of your holdings according to the values on coinmarketcap, in whichever currency you choose (as long as it's supported on the site) and also in BTC and ETH. I wanted a quick script that I could run to check values in USD and the "big 2" - I find it especially useful to see how much ETH my various altcoins are worth, compared to how much ETH I originally invested in them (hint: mostly less).

See example entries in coin.ini. Coins can either be added via their names or their codes (BTC, ETH, LTC, etc). Various options are configured via config.ini. Decimal places can be set independently for fiat and crypto currencies, and the sort key/direction is also configurable.

