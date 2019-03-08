# pycycles
Python HTTP client for finding and renting cycles from the docomo cycle service.

## Disclaimer
This is not officially associated with the docomo cycle service in any way. Use at your own discretion within the terms of use of the docomo cycle service.

## Usage

You'll need an account on the docomo cycle service.

Once you have one, to rent a bicycle you can do this:

```python
from pycycles import Client, ServiceArea
client = Client('username', 'password')
client.login()
cycleports = client.cycleports(ServiceArea.CHUO)
cycles = client.cycles(cycleports[0])
client.rent(cycles[0])
```

## Development

To set up in your environment locally:
```
pipenv install
```

To check typing:
```
mypy pycycles
```

## Contributing

Bug reports and pull requests are welcome on GitHub at https://github.com/dan-ess/pycycles

## License

The gem is available as open source under the terms of the [MIT License](https://opensource.org/licenses/MIT).
