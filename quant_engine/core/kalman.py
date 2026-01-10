"""
Kalman Filter Module

Applies Kalman filtering to price series for noise reduction and trend estimation.

Why Kalman beats EMA:
- EMA: Weighted average of past prices (reactive)
- Kalman: Predicts next state, then corrects based on observation (predictive)
- Result: ~40% less lag than equivalent EMA smoothing

The state-space model:
- State: [price, velocity]
- Observation: price only
- Transition: price(t+1) = price(t) + velocity(t)
              velocity(t+1) = velocity(t)
"""

import numpy as np
from typing import Dict, Optional, Tuple


def kalman_smooth(prices: np.ndarray,
                  transition_covariance: float = 0.01,
                  observation_covariance: float = 1.0,
                  use_pykalman: bool = True) -> Dict[str, np.ndarray]:
    """
    Apply Kalman filter to price series.

    Models price as having a velocity component:
    - State: [price, velocity]
    - Transition: price(t+1) = price(t) + velocity(t)

    Args:
        prices: Price array
        transition_covariance: Process noise (lower = smoother, more lag)
            Typical range: 0.001 to 0.1
        observation_covariance: Measurement noise (higher = more smoothing)
            Typical range: 0.5 to 2.0
        use_pykalman: If True, use pykalman library; else use pure numpy

    Returns:
        Dictionary with:
        - filtered_price: Smoothed price estimate
        - velocity: Estimated price velocity (trend direction/strength)
        - acceleration: Rate of velocity change
        - uncertainty: Estimation uncertainty (standard deviation)
    """
    if use_pykalman:
        try:
            return _kalman_pykalman(prices, transition_covariance, observation_covariance)
        except ImportError:
            pass  # Fall through to numpy implementation

    return _kalman_numpy(prices, transition_covariance, observation_covariance)


def _kalman_pykalman(prices: np.ndarray,
                     trans_cov: float,
                     obs_cov: float) -> Dict[str, np.ndarray]:
    """Kalman filter implementation using pykalman library."""
    from pykalman import KalmanFilter

    # State: [price, velocity]
    # Transition: price(t+1) = price(t) + velocity(t), velocity(t+1) = velocity(t)
    kf = KalmanFilter(
        transition_matrices=np.array([[1, 1], [0, 1]]),
        observation_matrices=np.array([[1, 0]]),
        initial_state_mean=np.array([prices[0], 0]),
        initial_state_covariance=np.array([[1, 0], [0, 1]]),
        transition_covariance=np.array([[trans_cov, 0], [0, trans_cov]]),
        observation_covariance=np.array([[obs_cov]])
    )

    # Run filter
    state_means, state_covariances = kf.filter(prices)

    filtered_price = state_means[:, 0]
    velocity = state_means[:, 1]
    acceleration = np.diff(velocity, prepend=velocity[0])
    uncertainty = np.sqrt(state_covariances[:, 0, 0])

    return {
        'filtered_price': filtered_price,
        'velocity': velocity,
        'acceleration': acceleration,
        'uncertainty': uncertainty
    }


def _kalman_numpy(prices: np.ndarray,
                  trans_cov: float,
                  obs_cov: float) -> Dict[str, np.ndarray]:
    """Pure numpy Kalman filter implementation (no external dependencies)."""
    n = len(prices)

    # State-space matrices
    F = np.array([[1, 1], [0, 1]])      # Transition matrix
    H = np.array([[1, 0]])               # Observation matrix
    Q = np.array([[trans_cov, 0],        # Process noise covariance
                  [0, trans_cov]])
    R = np.array([[obs_cov]])            # Observation noise covariance

    # Initialize
    x = np.array([prices[0], 0])         # State: [price, velocity]
    P = np.eye(2)                        # State covariance

    # Storage
    filtered_prices = np.zeros(n)
    velocities = np.zeros(n)
    uncertainties = np.zeros(n)

    for i in range(n):
        # Predict step
        x_pred = F @ x
        P_pred = F @ P @ F.T + Q

        # Update step
        y = prices[i] - H @ x_pred       # Innovation
        S = H @ P_pred @ H.T + R         # Innovation covariance
        K = P_pred @ H.T @ np.linalg.inv(S)  # Kalman gain

        x = x_pred + (K @ y).flatten()
        P = (np.eye(2) - K @ H) @ P_pred

        # Store results
        filtered_prices[i] = x[0]
        velocities[i] = x[1]
        uncertainties[i] = np.sqrt(P[0, 0])

    acceleration = np.diff(velocities, prepend=velocities[0])

    return {
        'filtered_price': filtered_prices,
        'velocity': velocities,
        'acceleration': acceleration,
        'uncertainty': uncertainties
    }


def adaptive_kalman(prices: np.ndarray,
                    volatility: np.ndarray,
                    base_obs_cov: float = 1.0,
                    base_trans_cov: float = 0.01) -> Dict[str, np.ndarray]:
    """
    Kalman filter with volatility-adaptive parameters.

    Adapts filter parameters based on market volatility:
    - High volatility = trust observations more (less smoothing)
    - Low volatility = trust model more (more smoothing)

    Args:
        prices: Price array
        volatility: Volatility array (same length as prices)
        base_obs_cov: Base observation covariance
        base_trans_cov: Base transition covariance

    Returns:
        Dictionary with filtered_price and velocity
    """
    n = len(prices)

    # Normalize volatility to [0.2, 2.0] range
    vol_min, vol_max = np.nanmin(volatility), np.nanmax(volatility)
    if vol_max - vol_min < 1e-10:
        vol_normalized = np.ones(n)
    else:
        vol_normalized = 0.2 + 1.8 * (volatility - vol_min) / (vol_max - vol_min + 1e-10)

    # Initialize
    F = np.array([[1, 1], [0, 1]])
    H = np.array([[1, 0]])
    Q = np.array([[base_trans_cov, 0], [0, base_trans_cov]])

    x = np.array([prices[0], 0])
    P = np.eye(2)

    filtered_prices = np.zeros(n)
    velocities = np.zeros(n)

    for i in range(n):
        # Adaptive observation noise based on volatility
        R = np.array([[base_obs_cov * vol_normalized[i]]])

        # Predict
        x_pred = F @ x
        P_pred = F @ P @ F.T + Q

        # Update
        y = prices[i] - H @ x_pred
        S = H @ P_pred @ H.T + R
        K = P_pred @ H.T @ np.linalg.inv(S)

        x = x_pred + (K @ y).flatten()
        P = (np.eye(2) - K @ H) @ P_pred

        filtered_prices[i] = x[0]
        velocities[i] = x[1]

    return {
        'filtered_price': filtered_prices,
        'velocity': velocities
    }


def kalman_bands(prices: np.ndarray,
                 multiplier: float = 2.0,
                 transition_covariance: float = 0.01,
                 observation_covariance: float = 1.0) -> Dict[str, np.ndarray]:
    """
    Calculate Kalman filter with uncertainty bands.

    Returns the filtered price with upper and lower bands based on
    the filter's uncertainty estimate.

    Args:
        prices: Price array
        multiplier: Band multiplier (default 2.0 for ~95% confidence)
        transition_covariance: Process noise
        observation_covariance: Measurement noise

    Returns:
        Dictionary with:
        - filtered_price: Center line
        - upper_band: Upper uncertainty band
        - lower_band: Lower uncertainty band
        - velocity: Trend velocity
    """
    result = kalman_smooth(prices, transition_covariance, observation_covariance)

    upper_band = result['filtered_price'] + multiplier * result['uncertainty']
    lower_band = result['filtered_price'] - multiplier * result['uncertainty']

    return {
        'filtered_price': result['filtered_price'],
        'upper_band': upper_band,
        'lower_band': lower_band,
        'velocity': result['velocity'],
        'uncertainty': result['uncertainty']
    }


def kalman_trend_signal(prices: np.ndarray,
                        velocity_threshold: float = 0.0,
                        transition_covariance: float = 0.01,
                        observation_covariance: float = 1.0) -> Dict[str, np.ndarray]:
    """
    Generate trend signals based on Kalman filter velocity.

    Args:
        prices: Price array
        velocity_threshold: Minimum velocity for trend signal (default 0)
        transition_covariance: Process noise
        observation_covariance: Measurement noise

    Returns:
        Dictionary with:
        - trend: +1 (up), -1 (down), 0 (neutral)
        - strength: Absolute velocity (trend strength)
        - velocity: Raw velocity
        - filtered_price: Smoothed price
    """
    result = kalman_smooth(prices, transition_covariance, observation_covariance)

    velocity = result['velocity']
    trend = np.zeros(len(prices))

    trend[velocity > velocity_threshold] = 1
    trend[velocity < -velocity_threshold] = -1

    return {
        'trend': trend,
        'strength': np.abs(velocity),
        'velocity': velocity,
        'filtered_price': result['filtered_price']
    }


def compare_kalman_ema(prices: np.ndarray,
                       ema_period: int = 20,
                       trans_cov: float = 0.01,
                       obs_cov: float = 1.0) -> Dict[str, np.ndarray]:
    """
    Compare Kalman filter to EMA for lag analysis.

    Returns both smoothing methods plus lag metrics.

    Args:
        prices: Price array
        ema_period: EMA period for comparison
        trans_cov: Kalman transition covariance
        obs_cov: Kalman observation covariance

    Returns:
        Dictionary with kalman, ema, and lag metrics
    """
    # Kalman filter
    kalman_result = kalman_smooth(prices, trans_cov, obs_cov)

    # EMA
    alpha = 2 / (ema_period + 1)
    ema = np.zeros(len(prices))
    ema[0] = prices[0]
    for i in range(1, len(prices)):
        ema[i] = alpha * prices[i] + (1 - alpha) * ema[i - 1]

    # Calculate lag (cross-correlation based)
    def estimate_lag(original: np.ndarray, smoothed: np.ndarray, max_lag: int = 20) -> int:
        """Estimate lag via cross-correlation."""
        diff = original - smoothed
        best_lag = 0
        best_corr = -np.inf

        for lag in range(max_lag):
            if lag >= len(diff):
                break
            shifted = np.roll(smoothed, -lag)
            valid = min(len(original), len(shifted) - lag)
            corr = np.corrcoef(original[:valid], shifted[:valid])[0, 1]
            if corr > best_corr:
                best_corr = corr
                best_lag = lag

        return best_lag

    kalman_lag = estimate_lag(prices, kalman_result['filtered_price'])
    ema_lag = estimate_lag(prices, ema)

    return {
        'kalman': kalman_result['filtered_price'],
        'ema': ema,
        'kalman_velocity': kalman_result['velocity'],
        'kalman_lag': kalman_lag,
        'ema_lag': ema_lag,
        'lag_reduction': (ema_lag - kalman_lag) / max(1, ema_lag) * 100
    }
