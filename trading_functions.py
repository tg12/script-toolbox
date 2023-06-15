""" def get_profit_loss(position):
    try:
        deal_size = float(position["position"]["dealSize"])
        if position["position"]["direction"] == "SELL":
            return (float(position["position"]["openLevel"]) -
                    float(position["market"]["offer"])) * deal_size
        else:
            return (float(position["market"]["bid"]) -
                    float(position["position"]["openLevel"])) * deal_size
    except Exception as e:
        logging.error("Error calculating profit/loss: %s", e)
        return None


def close_trade(base_url, position, delete_headers):
    try:
        deal_id = position["position"]["dealId"]
        deal_size = str(position["position"]["dealSize"])
        close_direction = "BUY" if position["position"]["direction"] == "SELL" else "SELL"
        base_url = base_url + "/positions/otc"
        data = {
            "dealId": deal_id,
            "size": deal_size,
            "orderType": "MARKET",
            "direction": close_direction,
        }
        response = requests.post(
            base_url,
            data=json.dumps(data),
            headers=delete_headers)
        if response.status_code != 200:
            logging.error(
                "Failed to close deal %s. Reason: %s",
                deal_id,
                response.text)
            return None
        return response.json()["dealReference"]
    except Exception as e:
        logging.error("Error closing trade: %s", e)
        return None


def close_all_trades(authenticated_headers, base_url, delete_headers):
    try:
        positions_url = "https://demo-api.ig.com/gateway/deal/positions"

        response = requests.get(positions_url, headers=authenticated_headers)
        positions = response.json()["positions"]
        for position in positions:
            profit_loss = get_profit_loss(position)
            # add guard close to check if trade is profitable, maybe??!!
            if profit_loss is None:
                continue
            logging.info(
                "Profit/Loss for deal %s is %s",
                position["position"]["dealId"],
                profit_loss)
            deal_ref = close_trade(base_url, position, delete_headers)
            if deal_ref is None:
                continue
            confirm_url = base_url + "/confirms/" + deal_ref
            confirm_response = requests.get(
                confirm_url, headers=authenticated_headers)
            confirm_status = confirm_response.json()
            logging.info("Closed deal %s with status: %s, reason: %s",
                         position["position"]["dealId"],
                         confirm_status["dealStatus"],
                         confirm_status["reason"])
    except Exception as e:
        logging.error("Error closing all trades: %s", e)
 """

# def rolling_correlation(drawdown, price, window):
#     """
#     Calculate the rolling correlation between the natural gas drawdown trend and the price over a given window.

#     drawdown: a sequence of natural gas drawdown values
#     price: a sequence of corresponding natural gas prices
#     window: the size of the window to use for calculating the rolling correlation

#     returns: a sequence of rolling correlations with the same length as the input sequences
#     """
#     corr = []
#     for i in range(len(drawdown)):
#         start = max(0, i - window + 1)  # start index for the window
#         end = i + 1  # end index for the window
#         d = drawdown[start:end]  # drawdown values in the window
#         p = price[start:end]  # prices in the window
#         # correlation coefficient between drawdown and price
#         r = np.corrcoef(d, p)[0, 1]
#         corr.append(r)
#     return corr

# def calculate_correlation(data):
#     """Calculate the relationship (correlation) between drawdown of natural gas and the price of natural gas.

#     Args:
#         data (Pandas DataFrame): The data to calculate the correlation for. The DataFrame should have columns
#             named 'price' and 'drawdown' containing the natural gas price and drawdown data, respectively.

#     Returns:
#         float: The Pearson correlation coefficient between the natural gas price and drawdown data.
#     """
#     # Extract the natural gas price and drawdown data
#     price = data['price']
#     drawdown = data['trend']

#     # Calculate the Pearson correlation coefficient
#     corr, _ = pearsonr(price, drawdown)

#     return corr

# def find_patterns_np(numbers):
#     patterns = []
#     # Convert list to NumPy array
#     numbers = np.array(numbers)
#     # Check for periodic trend
#     fft = np.fft.fft(numbers)
#     if np.abs(fft[1]) > 0.5:
#         # Compute the average value of the input numbers
#         avg = np.mean(numbers)
#         # Check if the periodic trend is upward or downward
#         if np.abs(fft[1]) / avg > 1:
#             direction = "upward"
#         else:
#             direction = "downward"
#         patterns.append(
#             ('periodic trend', f'The numbers show a {direction} periodic trend.'))
#     else:
#         # Check for linear trend
#         slope, intercept, r_value, p_value, std_err = stats.linregress(
#             range(len(numbers)), numbers)
#         if abs(slope) > 0.5:
#             if slope > 0:
#                 direction = "upward"
#             else:
#                 direction = "downward"
#             patterns.append(
#                 ('linear trend', f'The numbers show a {direction} linear trend.'))
#         # Check for outliers
#         else:
#             q75, q25 = np.percentile(numbers, [75, 25])
#             iqr = q75 - q25
#             cut_off = iqr * 1.5
#             lower, upper = q25 - cut_off, q75 + cut_off
#             outliers = [x for x in numbers if x < lower or x > upper]
#             if len(outliers) > 0:
#                 patterns.append(('outliers', 'The numbers contain outliers.'))
#     return patterns

# def find_trend_patterns(prices):
#   # First, we will use numpy's polyfit function to fit a polynomial curve to the prices
#   # This will allow us to find any underlying patterns in the data
#   coefficients = np.polyfit(range(len(prices)), prices, deg=2)
  
#   # The coefficients returned by polyfit represent the parameters of the polynomial curve
#   # We can use these coefficients to define a polynomial function
#   def polynomial(x):
#     return coefficients[0] * x**2 + coefficients[1] * x + coefficients[2]
  
#   # Now we can use the polynomial function to generate a list of predicted prices
#   # based on the trend pattern identified by the polynomial curve
#   predicted_prices = [polynomial(i) for i in range(len(prices))]
  
#   # Finally, we can return the list of predicted prices as the hidden trend pattern
#   return predicted_prices

# def hull_moving_average(data, window_size=14):
#     data['hull_moving_average'] = None
#     for i in range(len(data)):
#         if i < window_size:
#             data.loc[data.index[i],
#                      'hull_moving_average'] = data['price'][:i + 1].mean()
#         else:
#             data.loc[data.index[i], 'hull_moving_average'] = (
#                 2 * data['price'][i - window_size + 1:i + 1].mean() - data['price'][i - window_size:i + 1].mean())

#     # convert to a float and round to 2 decimal places

#         data['hull_moving_average'] = data['hull_moving_average'].astype(
#             float).round(2)

#     return data['hull_moving_average']

# def find_patterns(numbers):
#     from scipy.signal import detrend, periodogram
#     from scipy.stats import linregress, zscore

#     patterns = []

#     if len(numbers) < 2:
#         return patterns

#     # Check for periodic trend
#     f, Pxx_den = periodogram(numbers)
#     if Pxx_den[1] > 0.5:
#         direction = "upward" if Pxx_den[1] / np.mean(numbers) > 1 else "downward"
#         patterns.append(('periodic trend', f'The numbers show a {direction} periodic trend.'))

#     # Check for linear trend
#     detrended = detrend(numbers)
#     if not np.allclose(detrended, 0):
#         slope, intercept, r_value, p_value, std_err = linregress(range(len(numbers)), numbers)
#         direction = "upward" if slope > 0 else "downward"
#         patterns.append(('linear trend', f'The numbers show a {direction} linear trend.'))

#     detrended = detrend(numbers, type='linear')
#     if not np.allclose(detrended, 0):
#         direction = "upward" if np.polyfit(range(len(numbers)), numbers, 2)[0] > 0 else "downward"
#         patterns.append(('quadratic trend', f'The numbers show a {direction} quadratic trend.'))

#     # Check for outliers
#     z_scores = zscore(numbers)
#     outliers = [x for x in numbers if x < np.mean(numbers) - 3*np.std(numbers) or x > np.mean(numbers) + 3*np.std(numbers)]
#     if len(outliers) > 0:
#         patterns.append(('outliers', 'The numbers contain outliers.'))

#     return patterns
