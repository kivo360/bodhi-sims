# Copyright 2019 The TensorTrade Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License

from typing import Any

# from instrument import Quantity
# from trading_pair import TradingPair
import operator

from typing import Union, Tuple, Callable, TypeVar
from numbers import Number
from decimal import Decimal, ROUND_DOWN
from functools import total_ordering

T = TypeVar("T")

registry = {}


@total_ordering
class Quantity:
    """A size of a financial instrument for use in trading.

    Parameters
    ----------
    instrument : `Instrument`
        The unit of the quantity.
    size : `Decimal`
        The number of units of the instrument.
    path_id : str, optional
        The path order_id that this quantity is allocated for and associated
        with.

    Raises
    ------
    InvalidNegativeQuantity
        Raised if the `size` of the quantity being created is negative.
    """

    def __init__(self,
                 instrument: 'Instrument',
                 size: Decimal,
                 path_id: str | None = None):
        if size < 0:
            if abs(size) > Decimal(10)**(-instrument.precision):
                raise ValueError(float(size))
            else:
                size = Decimal(0)

        self.instrument = instrument
        self.size = size if isinstance(size, Decimal) else Decimal(size)
        self.path_id = path_id

    @property
    def is_locked(self) -> bool:
        """If quantity is locked for an order. (bool, read-only)"""
        return bool(self.path_id)

    def lock_for(self, path_id: str) -> "Quantity":
        """Locks a quantity for an `Order` identified associated with `path_id`.

        Parameters
        ----------
        path_id : str
            The identification of the order path.

        Returns
        -------
        `Quantity`
            A locked quantity for an order path.
        """
        return Quantity(self.instrument, self.size, path_id)

    def convert(self, exchange_pair: "ExchangePair") -> "Quantity":
        """Converts the quantity into the value of another instrument based
        on its exchange rate from an exchange.

        Parameters
        ----------
        exchange_pair : `ExchangePair`
            The exchange pair to use for getting the quoted price to perform
            the conversion.

        Returns
        -------
        `Quantity`
            The value of the current quantity in terms of the quote instrument.
        """
        if self.instrument == exchange_pair.pair.base:
            instrument = exchange_pair.pair.quote
            converted_size = self.size / exchange_pair.price
        else:
            instrument = exchange_pair.pair.base
            converted_size = self.size * exchange_pair.price
        return Quantity(instrument, converted_size, self.path_id)

    def free(self) -> "Quantity":
        """Gets the free version of this quantity.

        Returns
        -------
        `Quantity`
            The free version of the quantity.
        """
        return Quantity(self.instrument, self.size)

    def quantize(self) -> "Quantity":
        """Computes the quantization of current quantity in terms of the instrument's
        precision.

        Returns
        -------
        `Quantity`
            The quantized quantity.
        """
        return Quantity(
            self.instrument,
            self.size.quantize(Decimal(10)**-self.instrument.precision),
            self.path_id)

    def as_float(self) -> float:
        """Gets the size as a `float`.

        Returns
        -------
        float
            The size as a floating point number.
        """
        return float(self.size)

    def contain(self, exchange_pair: "ExchangePair"):
        """Contains the size of the quantity to be compatible with the settings
        of a given exchange.

        Parameters
        ----------
        exchange_pair : `ExchangePair`
            The exchange pair containing the exchange the quantity must be
            compatible with.

        Returns
        -------
        `Quantity`
            A quantity compatible with the given exchange.
        """
        options = exchange_pair.exchange.options
        price = exchange_pair.price

        if exchange_pair.pair.base == self.instrument:
            size = self.size
            return Quantity(self.instrument, min(size, options.max_trade_size),
                            self.path_id)

        size = self.size * price
        if size < options.max_trade_size:
            return Quantity(self.instrument, self.size, self.path_id)

        max_trade_size = Decimal(options.max_trade_size)
        contained_size = max_trade_size / price
        contained_size = contained_size.quantize(
            Decimal(10)**-self.instrument.precision, rounding=ROUND_DOWN)
        return Quantity(self.instrument, contained_size, self.path_id)

    @staticmethod
    def validate(
            left: "Union[Quantity, Number]",
            right: "Union[Quantity, Number]") -> "Tuple[Quantity, Quantity]":
        """Validates the given left and right arguments of a numeric or boolean
        operation.

        Parameters
        ----------
        left : `Union[Quantity, Number]`
            The left argument of an operation.
        right : `Union[Quantity, Number]`
            The right argument of an operation.

        Returns
        -------
        `Tuple[Quantity, Quantity]`
            The validated quantity arguments to use in a numeric or boolean
            operation.

        Raises
        ------
        IncompatibleInstrumentOperation
            Raised if the instruments left and right quantities are not equal.
        QuantityOpPathMismatch
            Raised if
                - One argument is locked and the other argument is not.
                - Both arguments are locked quantities with unequal path_ids.
        InvalidNonNumericQuantity
            Raised if either argument is a non-numeric object.
        Exception
            If the operation is not valid.
        """
        if isinstance(left, Quantity) and isinstance(right, Quantity):
            if left.instrument != right.instrument:
                raise TypeError(left, right)

            if (left.path_id and
                    right.path_id) and (left.path_id != right.path_id):
                raise Exception("Path mismatch")

            elif left.path_id and not right.path_id:
                right.path_id = left.path_id

            elif not left.path_id and right.path_id:
                left.path_id = right.path_id

            return left, right

        elif isinstance(left, Number) and isinstance(right, Quantity):
            left = Quantity(right.instrument, left, right.path_id)
            return left, right

        elif isinstance(left, Quantity) and isinstance(right, Number):
            right = Quantity(left.instrument, right, left.path_id)
            return left, right

        elif isinstance(left, Quantity):
            raise ValueError(right)

        elif isinstance(right, Quantity):
            raise ValueError(left)

        raise Exception(
            f"Invalid quantity operation arguments: {left} and {right}")

    @staticmethod
    def _bool_op(left: "Union[Quantity, Number]",
                 right: "Union[Quantity,Number]",
                 op: "Callable[[T, T], bool]") -> bool:
        """Performs a generic boolean operation on two quantities.

        Parameters
        ----------
        left : `Union[Quantity, Number]`
            The left argument of the operation.
        right : `Union[Quantity, Number]`
            The right argument of the operation.
        op : `Callable[[T, T], bool]`
            The boolean operation to be used.

        Returns
        -------
        bool
            The result of performing `op` on with `left` and `right`.
        """
        left, right = Quantity.validate(left, right)
        boolean = op(left.size, right.size)  # type: ignore
        return boolean

    @staticmethod
    def _math_op(left: "Union[Quantity, Number]",
                 right: "Union[Quantity, Number]",
                 op: "Callable[[T, T], T]") -> "Quantity":
        """Performs a generic numeric operation on two quantities.

        Parameters
        ----------
        left : `Union[Quantity, Number]`
            The left argument of the operation.
        right : `Union[Quantity, Number]`
            The right argument of the operation.
        op : `Callable[[T, T], bool]`
            The numeric operation to be used.

        Returns
        -------
        `Quantity`
            The result of performing `op` on with `left` and `right`.
        """
        left, right = Quantity.validate(left, right)
        size = op(left.size, right.size)  # type: ignore
        return Quantity(left.instrument, size, left.path_id)  # type: ignore

    def __add__(self, other: "Quantity") -> "Quantity":
        return Quantity._math_op(self, other, operator.add)

    def __sub__(self, other: "Union[Quantity, Number]") -> "Quantity":
        return Quantity._math_op(self, other, operator.sub)

    def __iadd__(self, other: "Union[Quantity, Number]") -> "Quantity":
        return Quantity._math_op(self, other, operator.iadd)

    def __isub__(self, other: "Union[Quantity, Number]") -> "Quantity":
        return Quantity._math_op(self, other, operator.isub)

    def __mul__(self, other: "Union[Quantity, Number]") -> "Quantity":
        return Quantity._math_op(self, other, operator.mul)

    def __rmul__(self, other: "Union[Quantity, Number]") -> "Quantity":
        return Quantity.__mul__(self, other)

    def __lt__(self, other: "Union[Quantity, Number]") -> bool:
        return Quantity._bool_op(self, other, operator.lt)

    def __eq__(self, other: "Union[Quantity, Number]") -> bool:
        return Quantity._bool_op(self, other, operator.eq)

    def __ne__(self, other: "Union[Quantity, Number]") -> bool:
        return Quantity._bool_op(self, other, operator.ne)

    def __neg__(self) -> bool:
        return operator.neg(self.size)  # type: ignore

    def __str__(self) -> str:
        s = "{0:." + str(self.instrument.precision) + "f}" + " {1}"
        s = s.format(self.size, self.instrument.symbol)
        return s

    def __repr__(self) -> str:
        return str(self)


class TradingPair:
    """A pair of financial instruments to be traded on an exchange.

    Parameters
    ----------
    base : `Instrument`
        The base instrument of the trading pair.
    quote : `Instrument`
        The quote instrument of the trading pair.

    Raises
    ------
    InvalidTradingPair
        Raises if base and quote instrument are equal.
    """

    def __init__(self, base: "Instrument", quote: "Instrument") -> None:
        if base == quote:
            raise ValueError("Base and quote instruments cannot be equal.")
        self.base = base
        self.quote = quote

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other: "Any") -> bool:
        if isinstance(other, TradingPair):
            if str(self) == str(other):
                return True
        return False

    def __ne__(self, other: "Any") -> bool:
        return not self.__eq__(other)

    def __str__(self) -> str:
        return "{}/{}".format(self.base.symbol, self.quote.symbol)

    def __repr__(self) -> str:
        return str(self)


class Instrument:
    """A financial instrument for use in trading.

    Parameters
    ----------
    symbol : str
        The symbol used on an exchange for a particular instrument.
        (e.g. AAPL, BTC, TSLA)
    precision : int
        The precision the amount of the instrument is denoted with.
        (e.g. BTC=8, AAPL=1)
    name : str, optional
        The name of the instrument being created.
    """

    def __init__(self,
                 symbol: str,
                 precision: int,
                 name: str | None = None) -> None:
        self.symbol = symbol
        self.precision = precision
        self.name = name

        registry[symbol] = self

    def __eq__(self, other: "Any") -> bool:
        """Checks if two instruments are equal.

        Parameters
        ----------
        other : `Any`
            The instrument being compared.

        Returns
        -------
        bool
            Whether the instruments are equal.
        """
        if not isinstance(other, Instrument):
            return False
        c1 = self.symbol == other.symbol
        c2 = self.precision == other.precision
        c3 = self.name == other.name
        return c1 and c2 and c3

    def __ne__(self, other: "Any") -> bool:
        """Checks if two instruments are not equal.

        Parameters
        ----------
        other : `Any`
            The instrument being compared.

        Returns
        -------
        bool
            Whether the instruments are not equal.
        """
        return not self.__eq__(other)

    def __rmul__(self, other: float) -> "Quantity":
        """Enables reverse multiplication.

        Parameters
        ----------
        other : float
            The number used to create a quantity.

        Returns
        -------
        `Quantity`
            The quantity created by the number and the instrument involved with
            this operation.
        """
        return Quantity(instrument=self, size=Decimal(other))

    def __truediv__(self, other: "Instrument") -> "TradingPair":
        """Creates a trading pair through division.

        Parameters
        ----------
        other : `Instrument`
            The instrument that will be the quote of the pair.

        Returns
        -------
        `TradingPair`
            The trading pair created from the two instruments.

        Raises
        ------
        InvalidTradingPair
            Raised if `other` is the same instrument as `self`.
        Exception
            Raised if `other` is not an instrument.
        """
        if isinstance(other, Instrument):
            return TradingPair(self, other)
        raise Exception(
            f"Invalid trading pair: {other} is not a valid instrument.")

    def __hash__(self):
        return hash(self.symbol)

    def __str__(self):
        return f"Instrument(symbol={str(self.symbol)}, precision={self.precision}, name={str(self.name)})"

    def __repr__(self):
        return str(self)


# Crypto
BTC = Instrument('BTC', 8, 'Bitcoin')
ETH = Instrument('ETH', 8, 'Ethereum')
XRP = Instrument('XRP', 8, 'XRP')
NEO = Instrument('NEO', 8, 'NEO')
BCH = Instrument('BCH', 8, 'Bitcoin Cash')
LTC = Instrument('LTC', 8, 'Litecoin')
ETC = Instrument('ETC', 8, 'Ethereum Classic')
XLM = Instrument('XLM', 8, 'Stellar Lumens')
LINK = Instrument('LINK', 8, 'Chainlink')
ATOM = Instrument('ATOM', 8, 'Cosmos')
DAI = Instrument('DAI', 8, 'Dai')
USDT = Instrument('USDT', 8, 'Tether')

# FX
USD = Instrument('USD', 2, 'U.S. Dollar')
EUR = Instrument('EUR', 2, 'Euro')
JPY = Instrument('JPY', 2, 'Japanese Yen')
KWN = Instrument('KWN', 2, 'Korean Won')
AUD = Instrument('AUD', 2, 'Australian Dollar')

# Commodities
XAU = Instrument('XAU', 2, 'Gold futures')
XAG = Instrument('XAG', 2, 'Silver futures')

# Stocks

AAPL = Instrument('AAPL', 2, 'Apple stock')
MSFT = Instrument('MSFT', 2, 'Microsoft stock')
TSLA = Instrument('TSLA', 2, 'Tesla stock')
AMZN = Instrument('AMZN', 2, 'Amazon stock')

print(AAPL)
print(MSFT)
print(TSLA)