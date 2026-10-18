"""
model.py — the outflow math. No Streamlit code in here, so it's easy to test
and easy to explain in an interview.

All money is in US dollars.
"""


def country_outflow(passive_aum_usd, indonesia_weight_pct, pct_sell, scenario_factor):
    """Dollars passive funds would sell out of Indonesia.

    outflow = passive AUM x Indonesia's weight x % that sell x scenario factor
    """
    return passive_aum_usd * (indonesia_weight_pct / 100) * (pct_sell / 100) * scenario_factor


def stock_outflow(country_outflow_usd, stock_weight):
    """Split the country outflow by the stock's share of Indonesia's index weight."""
    return country_outflow_usd * stock_weight


def days_of_forced_selling(outflow_usd, adv_usd, participation_pct):
    """How many trading days it takes to sell, if sellers stay under
    `participation_pct` of each day's traded value.

    Returns None when we don't have volume data.
    """
    daily_capacity = adv_usd * (participation_pct / 100)
    if not daily_capacity or daily_capacity <= 0:
        return None
    return outflow_usd / daily_capacity


def expected_value(outflow_usd, probability_pct):
    """Probability-weighted outflow."""
    return outflow_usd * (probability_pct / 100)


def daily_pressure_pct_of_adv(outflow_usd, adv_usd, days_to_exit):
    """If sellers spread the exit over `days_to_exit` days, what % of normal
    daily traded value does that selling represent?"""
    if not adv_usd or days_to_exit <= 0:
        return None
    return (outflow_usd / days_to_exit) / adv_usd * 100
