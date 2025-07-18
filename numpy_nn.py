# ==============================================================================
#  DISCLAIMER
#  ----------------------------------------------------------------------------
#  This script is for educational and research purposes only.
#  It is NOT intended for production use, financial decision-making, or medical
#  applications. The neural network implementation here is minimal, explanatory,
#  and intentionally leaves out many features and safeguards found in real-world
#  machine learning frameworks.
#
#  You are free to use, modify, or share this code at your own risk.
#  THERE ARE NO WARRANTIES OF ANY KIND—EXPRESS OR IMPLIED.
#  By using this script, you accept full responsibility for any consequences,
#  bugs, losses, or catastrophic quantum singularities that may result.
#
#  If you break it, you get to keep both pieces.
# ==============================================================================


"""
numpy_nn.py

A minimal neural network implementation using NumPy for regression on time series data (e.g., stock prices).
- Demonstrates synthetic data generation and real CSV data loading.
- Implements a simple feedforward neural network with one hidden layer.
- Includes manual normalization, training loop, early stopping, and prediction plotting.
- Useful for educational purposes, prototyping, and understanding neural network fundamentals without external ML libraries.

Typical use cases:
- Predicting next-day prices based on historical OHLC data.
- Experimenting with neural network training and inference using only NumPy.
- Visualizing model predictions and trends.

Requirements:
- numpy
- pandas
- matplotlib
"""

import datetime
import logging
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Configure verbose logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# --- Colored Logging Setup ---


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[94m",  # Blue
        logging.INFO: "\033[92m",  # Green
        logging.WARNING: "\033[93m",  # Yellow
        logging.ERROR: "\033[91m",  # Red
        logging.CRITICAL: "\033[95m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        message = super().format(record)
        return f"{color}{message}{self.RESET}"


# Replace default handler with colored formatter
for handler in logger.handlers:
    handler.setFormatter(ColorFormatter("%(asctime)s [%(levelname)s] %(message)s"))

# Ignore E731 warning
# flake8: noqa
# -*- coding: utf-8 -*-
# pylint: disable=C0116, W0621, W1203, C0103, C0301, W1201, W0511, E0401, E1101, E0606, E731

# --- Synthetic Data Generation for Testing ---
np.random.seed(42)  # For reproducibility


def generate_synthetic_data(n_samples):
    """
    Generate synthetic historical price data and targets for demonstration.
    Each sample consists of 5 noisy price points and a target (next day's price).
    """
    historical_prices = []
    target_prices = []
    for i in range(n_samples):
        base_price = 100 + i * 0.1  # Simulate an increasing trend
        noise = np.random.normal(0, 0.5, 5)  # Add random noise
        prices = base_price + noise
        target_price = base_price + 0.1 + np.random.normal(0, 0.5)  # Next day's price
        historical_prices.append(prices)
        target_prices.append(target_price)
    return np.array(historical_prices), np.array(target_prices)


n_samples = 100
historical_prices, target_prices = generate_synthetic_data(n_samples)

# --- Neural Network Layer Definition ---


class Layer:
    """
    Represents a fully connected neural network layer.
    """

    def __init__(self, input_size, output_size):
        # Xavier/Glorot uniform initialization for weights
        limit = np.sqrt(6 / (input_size + output_size))
        self.weights = np.random.uniform(-limit, limit, (output_size, input_size))
        self.biases = np.zeros((output_size, 1))
        logger.debug(
            f"Initialized Layer: weights shape {self.weights.shape}, biases shape {self.biases.shape}"
        )

    def forward(self, inputs):
        """
        Forward pass: compute weighted sum plus bias.
        """
        logger.debug(f"Layer forward: input shape {inputs.shape}")
        return np.matmul(self.weights, inputs) + self.biases

    def backward(self, previous_inputs, output_grad, learning_rate):
        """
        Backward pass: update weights and biases using gradients.
        """
        grad_w = np.matmul(output_grad, previous_inputs.T)
        grad_b = np.sum(output_grad, axis=1, keepdims=True)
        # Clip gradients to avoid exploding gradients
        grad_w = np.clip(grad_w, -1, 1)
        grad_b = np.clip(grad_b, -1, 1)
        self.weights -= learning_rate * grad_w
        self.biases -= learning_rate * grad_b
        logger.debug(f"Layer backward: updated weights and biases")
        # Return gradient for previous layer
        return np.matmul(self.weights.T, output_grad)


# --- Activation Functions ---


def relu(x):
    """ReLU activation (elementwise)."""
    return np.maximum(0, x)


def relu_derivative(x):
    """Derivative of ReLU."""
    return (x > 0).astype(float)


# --- Loss Functions ---


def mse_loss(pred, true):
    """Mean squared error loss."""
    return np.mean((pred - true) ** 2)


def mse_loss_derivative(pred, true):
    """Derivative of MSE loss."""
    return 2 * (pred - true) / true.size


# --- Utility Functions ---


def normalize(data):
    """Standard score normalization."""
    mean = np.mean(data, axis=0)
    std = np.std(data, axis=0)
    return (data - mean) / std, mean, std


def denormalize(data, mean, std):
    """Reverse normalization."""
    return data * std + mean


def custom_date_parser(date_str):
    """Parse custom date format from CSV."""
    return datetime.datetime.strptime(date_str, "%Y:%m:%d-%H:%M:%S")


def early_stopping(validation_losses, patience=10):
    """
    Early stopping: stop if validation loss hasn't improved for 'patience' epochs.
    """
    if len(validation_losses) > patience and all(
        validation_losses[-i] > validation_losses[-(i + 1)]
        for i in range(1, patience + 1)
    ):
        return True
    return False


def log_message(message):
    """Log a message at INFO level."""
    logger.info(message)


# --- Main Execution ---
if __name__ == "__main__":
    # --- Plain English Explanation for Students ---
    # This script demonstrates how to build, train, and evaluate a simple neural network using only NumPy.
    # It covers:
    # 1. Generating synthetic data to simulate a real-world regression problem.
    # 2. Defining a neural network layer from scratch.
    # 3. Implementing forward and backward passes (core of neural network training).
    # 4. Training the network on both synthetic and real data.
    # 5. Using validation data to monitor overfitting.
    # 6. Dynamically adjusting learning rate and restoring best weights (self-healing).
    # 7. Visualizing predictions and trends.
    logger.info("=== Neural Network Training Exercise ===")
    logger.info("Step 1: Generating synthetic data for demonstration.")
    # Prepare data for training (synthetic)
    inputs = historical_prices.T  # shape: (features, samples)
    y = target_prices.reshape(1, -1)  # shape: (1, samples)
    hidden_layer = Layer(inputs.shape[0], 10)
    output_layer = Layer(10, 1)
    learning_rate = 0.001

    # Training loop for synthetic data
    logger.info("Step 3: Training on synthetic data (observe loss every 100 epochs).")
    for epoch in range(1000):
        hidden_output = hidden_layer.forward(inputs)
        activation_output = relu(hidden_output)
        output = output_layer.forward(activation_output)
        loss = mse_loss(output, y)
        loss_grad = mse_loss_derivative(output, y)
        indirect_loss = output_layer.backward(
            activation_output, loss_grad, learning_rate
        )
        hidden_output_grad = indirect_loss * relu_derivative(hidden_output)
        hidden_layer.backward(inputs, hidden_output_grad, learning_rate)
        if epoch % 100 == 0:
            logger.info(f"[Synthetic] Epoch {epoch}, Loss: {loss:.4f}")

    logger.info("Step 4: Predicting on synthetic data and plotting results.")

    def predict(x):
        """Run forward pass for prediction."""
        return output_layer.forward(relu(hidden_layer.forward(x)))

    predictions = predict(inputs).flatten()

    # Plot actual vs predicted prices (synthetic)
    plt.figure(figsize=(10, 5))
    plt.plot(target_prices, label="Actual Prices", marker="o")
    plt.plot(predictions, label="Predicted Prices", marker="x")
    plt.xlabel("Sample")
    plt.ylabel("Price")
    plt.title("Actual vs Predicted Prices (Synthetic Data)")
    plt.legend()
    plt.show()

    # --- Real Data Section ---
    logger.info(
        "Step 5: Loading real data from CSV (make sure 'backtest_prices.csv' exists)."
    )
    try:
        data = pd.read_csv(
            "backtest_prices.csv",
            parse_dates=["snapshotTime"],
            date_parser=custom_date_parser,
        )
        logger.info("Successfully loaded real data.")
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        sys.exit(1)

    # Extract OHLC features and target (next day's close)
    historical_prices = data[["open", "high", "low", "close"]].values
    target_prices = data["close"].shift(-1).dropna().values
    historical_prices = historical_prices[:-1]  # Align lengths

    logger.info("Step 6: Extracting features and targets from real data.")

    # Normalize features and targets
    historical_prices_norm, mean_prices, std_prices = normalize(historical_prices)
    target_prices_norm, mean_target, std_target = normalize(
        target_prices.reshape(-1, 1)
    )

    logger.info("Step 7: Normalizing features and targets for stable training.")

    # Prepare data for training (real)
    inputs = historical_prices_norm.T
    y = target_prices_norm.T
    hidden_layer = Layer(inputs.shape[0], 10)
    output_layer = Layer(10, 1)
    learning_rate = 0.001
    min_learning_rate = 1e-6
    epochs = 70000
    patience = 10
    lr_patience = 5  # patience for learning rate reduction
    validation_split = 0.2
    validation_index = int(inputs.shape[1] * (1 - validation_split))
    train_inputs, val_inputs = (
        inputs[:, :validation_index],
        inputs[:, validation_index:],
    )
    train_y, val_y = y[:, :validation_index], y[:, validation_index:]
    validation_losses = []

    logger.info(
        "Step 9: Starting training on real data with self-healing feedback loop."
    )
    logger.info("  - The model will reduce learning rate if validation loss plateaus.")
    logger.info("  - Early stopping will occur if no improvement for several epochs.")
    logger.info("  - Best weights are restored at the end to avoid overfitting.")

    # --- Self-healing feedback loop variables ---
    best_val_loss = float("inf")
    best_weights = None
    best_biases = None
    best_output_weights = None
    best_output_biases = None
    epochs_since_improvement = 0
    epochs_since_lr_reduce = 0

    for epoch in range(epochs):
        # Forward pass
        hidden_output = hidden_layer.forward(train_inputs)
        activation_output = relu(hidden_output)
        output = output_layer.forward(activation_output)
        loss = mse_loss(output, train_y)
        # Backward pass
        loss_grad = mse_loss_derivative(output, train_y)
        indirect_loss = output_layer.backward(
            activation_output, loss_grad, learning_rate
        )
        hidden_output_grad = indirect_loss * relu_derivative(hidden_output)
        hidden_layer.backward(train_inputs, hidden_output_grad, learning_rate)
        # Validation loss
        val_hidden_output = hidden_layer.forward(val_inputs)
        val_activation_output = relu(val_hidden_output)
        val_output = output_layer.forward(val_activation_output)
        val_loss = mse_loss(val_output, val_y)
        validation_losses.append(val_loss)

        # --- Feedback loop: self-healing fine-tuning ---
        if val_loss < best_val_loss - 1e-6:  # Significant improvement
            best_val_loss = val_loss
            # Save best weights and biases
            best_weights = hidden_layer.weights.copy()
            best_biases = hidden_layer.biases.copy()
            best_output_weights = output_layer.weights.copy()
            best_output_biases = output_layer.biases.copy()
            epochs_since_improvement = 0
            epochs_since_lr_reduce = 0
        else:
            epochs_since_improvement += 1
            epochs_since_lr_reduce += 1

        # Reduce learning rate if no improvement for lr_patience epochs
        if epochs_since_lr_reduce >= lr_patience:
            old_lr = learning_rate
            learning_rate = max(learning_rate * 0.5, min_learning_rate)
            logger.info(
                f"Reducing learning rate from {old_lr:.6f} to {learning_rate:.6f} at epoch {epoch}"
            )
            epochs_since_lr_reduce = 0

        # Early stopping if no improvement for 'patience' epochs
        if epochs_since_improvement >= patience:
            logger.info(
                f"Early stopping at epoch {epoch} (no val improvement for {patience} epochs)"
            )
            break

        if epoch % 10 == 0:
            logger.debug(
                f"Epoch {epoch}: Training loss {loss:.6f}, Validation loss {val_loss:.6f}"
            )
        if epoch % 100 == 0:
            log_message(
                f"Epoch {epoch}, Loss: {loss:.4f}, Val Loss: {val_loss:.4f}, LR: {learning_rate:.6f}"
            )

    # Restore best weights (self-healing)
    if best_weights is not None:
        logger.info(
            "Restoring best model weights based on validation loss to avoid overfitting."
        )
        hidden_layer.weights = best_weights
        hidden_layer.biases = best_biases
        output_layer.weights = best_output_weights
        output_layer.biases = best_output_biases

    logger.info("Step 10: Predicting on all data and denormalizing predictions.")

    def predict(x):
        """Run forward pass for prediction."""
        return output_layer.forward(relu(hidden_layer.forward(x)))

    predictions_norm = predict(inputs).flatten()
    predictions = denormalize(predictions_norm, mean_target, std_target)

    logger.info("Step 11: Predicting the next few days based on the last known input.")
    # Predict next few days' prices based on last input
    next_days_predictions_norm = []
    num_days = 5
    last_input = historical_prices_norm[-1].reshape(-1, 1)
    for _ in range(num_days):
        next_day_prediction_norm = predict(last_input)
        next_days_predictions_norm.append(next_day_prediction_norm.mean())
        # Roll input and append prediction for next step
        last_input = np.roll(last_input, -1)
        last_input[-1] = next_day_prediction_norm.mean()

    next_days_predictions = denormalize(
        np.array(next_days_predictions_norm), mean_target, std_target
    ).flatten()
    next_days_means = np.array(next_days_predictions)
    next_days_stds = np.std(next_days_means)

    # Generate future dates for plotting
    last_date = pd.to_datetime(data["snapshotTime"].iloc[-1])
    future_dates = [last_date + datetime.timedelta(days=i + 1) for i in range(num_days)]

    logger.info(
        "Step 12: Plotting actual prices and predicted price range for the next few days."
    )
    # Plot actual prices and predicted next few days' price range
    plt.figure(figsize=(12, 6))
    plt.plot(
        pd.to_datetime(data["snapshotTime"][:-1]),
        target_prices,
        label="Actual Prices",
        marker="o",
        color="black",
    )
    for i in range(num_days):
        color = "green" if next_days_means[i] > target_prices[-1] else "red"
        plt.fill_between(
            [future_dates[i] - datetime.timedelta(days=1), future_dates[i]],
            next_days_means[i] - next_days_stds,
            next_days_means[i] + next_days_stds,
            color=color,
            alpha=0.3,
            label="Predicted Range" if i == 0 else "",
        )
        plt.plot(future_dates[i], next_days_means[i], "ro" if color == "red" else "go")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.title("Actual Prices and Predicted Next Few Days Price Range")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    logger.info(
        "Step 13: Printing a summary of the predicted trend for the next few days."
    )
    # Print a summary of the predicted trend for the next few days
    for i, price in enumerate(next_days_means):
        trend = "up" if price > target_prices[-1] else "down"
        logger.info(f"Day {i + 1}: Predicted mean price = {price:.2f} ({trend})")

    # --- End of Training Exercise ---
    logger.info("=== End of Neural Network Training Exercise ===")
