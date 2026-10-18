"""Home tab: the full-screen countdown."""
import config
import data
from components import hero

fx = data.load_prices(config.FX_TICKER)
jci = data.load_prices(config.INDEX_TICKER)
hero(data.change_since(jci), None if fx.empty else fx["Close"].iloc[-1])
