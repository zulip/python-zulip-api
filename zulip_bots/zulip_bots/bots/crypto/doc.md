# crypto bot

The crypto bot is a Zulip bot that can fetch the
current market price for a specified cryptocurrency in USD.
The crypto bot can also retrieve a market price for
a cryptocurrency from a given date in the form YYYY-MM-DD.

To get the current market price:
```
@crypto BTC
> The current market price for BTC is $40696.73
```

To get the price on a given date:
```
@crypto BTC 2022-04-16
> The market price for BTC on 2022-04-16 was $40554.6
```