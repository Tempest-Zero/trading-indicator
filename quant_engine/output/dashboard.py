"""
Dashboard Visualization Module

Creates interactive Plotly dashboards and terminal-based summaries
for market analysis results.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Any

from quant_engine.core.engine import MarketConditions, QuantEngine
from quant_engine.core.volume import volume_delta


def create_dashboard(ohlcv: pd.DataFrame,
                     conditions: MarketConditions,
                     engine: Optional[QuantEngine] = None,
                     show_volume_profile: bool = True) -> Any:
    """
    Create interactive Plotly dashboard.

    Args:
        ohlcv: OHLCV DataFrame
        conditions: MarketConditions from analysis
        engine: QuantEngine instance (for cached data)
        show_volume_profile: Whether to show volume profile on price chart

    Returns:
        Plotly figure object
    """
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        raise ImportError(
            "Plotly is required for visualization. Install with: pip install plotly"
        )

    # Get cached data from engine if available
    if engine is not None:
        cache = engine.get_cached_data()
        hurst_series = cache.get('hurst_series')
        kalman_result = cache.get('kalman_result')
        zscore_result = cache.get('zscore_result')
        vol_delta = cache.get('volume_delta')
        vol_profile = cache.get('volume_profile')
    else:
        # Recalculate if no cache
        from quant_engine.core.hurst import rolling_hurst
        from quant_engine.core.kalman import kalman_smooth
        from quant_engine.core.zscore import rolling_zscore
        from quant_engine.core.volume import volume_profile as vp

        prices = ohlcv['close'].values
        hurst_series = rolling_hurst(prices)
        kalman_result = kalman_smooth(prices)
        zscore_result = rolling_zscore(prices)
        vol_delta = volume_delta(ohlcv)
        vol_profile = vp(ohlcv)

    # Create subplot figure
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.45, 0.18, 0.18, 0.19],
        subplot_titles=[
            f'{conditions.symbol} - Regime: {conditions.regime} ({conditions.regime_confidence:.0%})',
            'Hurst Exponent (Regime Detection)',
            'Z-Score (Statistical Position)',
            'Volume Delta (Buy/Sell Pressure)'
        ]
    )

    # Row 1: Price Chart with Kalman Filter
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=ohlcv.index,
        open=ohlcv['open'],
        high=ohlcv['high'],
        low=ohlcv['low'],
        close=ohlcv['close'],
        name='Price',
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350'
    ), row=1, col=1)

    # Kalman filtered price
    fig.add_trace(go.Scatter(
        x=ohlcv.index,
        y=kalman_result['filtered_price'],
        name='Kalman Filter',
        line=dict(color='#ffd700', width=2)
    ), row=1, col=1)

    # Key levels from volume profile
    fig.add_hline(
        y=conditions.poc,
        line_dash="dash",
        line_color="purple",
        annotation_text="POC",
        annotation_position="right",
        row=1, col=1
    )
    fig.add_hline(
        y=conditions.value_area_high,
        line_dash="dot",
        line_color="green",
        annotation_text="VA High",
        annotation_position="right",
        row=1, col=1
    )
    fig.add_hline(
        y=conditions.value_area_low,
        line_dash="dot",
        line_color="red",
        annotation_text="VA Low",
        annotation_position="right",
        row=1, col=1
    )

    # Row 2: Hurst Exponent
    fig.add_trace(go.Scatter(
        x=ohlcv.index,
        y=hurst_series,
        name='Hurst',
        line=dict(color='#00bcd4', width=1.5),
        fill='tozeroy',
        fillcolor='rgba(0, 188, 212, 0.1)'
    ), row=2, col=1)

    # Hurst reference lines
    fig.add_hline(y=0.5, line_dash="solid", line_color="white",
                  line_width=1, row=2, col=1)
    fig.add_hrect(y0=0, y1=0.4, fillcolor="red", opacity=0.1,
                  annotation_text="Mean-Reverting", row=2, col=1)
    fig.add_hrect(y0=0.6, y1=1.0, fillcolor="green", opacity=0.1,
                  annotation_text="Trending", row=2, col=1)

    # Row 3: Z-Score
    zscore_values = zscore_result['zscore']
    fig.add_trace(go.Scatter(
        x=ohlcv.index,
        y=zscore_values,
        name='Z-Score',
        line=dict(color='#ff9800', width=1.5)
    ), row=3, col=1)

    # Z-Score reference lines
    fig.add_hline(y=2, line_dash="dash", line_color="red",
                  annotation_text="+2σ", row=3, col=1)
    fig.add_hline(y=-2, line_dash="dash", line_color="green",
                  annotation_text="-2σ", row=3, col=1)
    fig.add_hline(y=0, line_dash="solid", line_color="white",
                  line_width=0.5, row=3, col=1)

    # Shade extreme regions
    fig.add_hrect(y0=2, y1=5, fillcolor="red", opacity=0.1, row=3, col=1)
    fig.add_hrect(y0=-5, y1=-2, fillcolor="green", opacity=0.1, row=3, col=1)

    # Row 4: Volume Delta
    delta = vol_delta['delta']
    colors = ['#26a69a' if d > 0 else '#ef5350' for d in delta]

    fig.add_trace(go.Bar(
        x=ohlcv.index,
        y=delta,
        name='Volume Delta',
        marker_color=colors
    ), row=4, col=1)

    # Add cumulative delta line
    fig.add_trace(go.Scatter(
        x=ohlcv.index,
        y=vol_delta['cumulative_delta'] / np.max(np.abs(vol_delta['cumulative_delta'])) * np.max(np.abs(delta)),
        name='Cumulative Delta',
        line=dict(color='yellow', width=1.5),
        yaxis='y4'
    ), row=4, col=1)

    # Update layout
    bias_color = {
        'UP': '#26a69a',
        'DOWN': '#ef5350',
        'NEUTRAL': '#9e9e9e',
        'WAIT': '#ff9800'
    }.get(conditions.suggested_bias, '#9e9e9e')

    fig.update_layout(
        template='plotly_dark',
        height=900,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        title=dict(
            text=f"<b>{conditions.symbol}</b> | Bias: <span style='color:{bias_color}'>{conditions.suggested_bias}</span> | Confidence: {conditions.confidence:.0%}",
            x=0.5,
            font=dict(size=16)
        ),
        xaxis_rangeslider_visible=False
    )

    # Y-axis labels
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="H", row=2, col=1, range=[0, 1])
    fig.update_yaxes(title_text="Z", row=3, col=1, range=[-4, 4])
    fig.update_yaxes(title_text="Delta", row=4, col=1)

    return fig


def print_summary(conditions: MarketConditions) -> None:
    """
    Print formatted text summary of market conditions.

    Args:
        conditions: MarketConditions from analysis
    """
    # Use the __str__ method of MarketConditions
    print(str(conditions))


def print_quick_summary(conditions: MarketConditions) -> None:
    """
    Print compact one-line summary.

    Args:
        conditions: MarketConditions from analysis
    """
    regime_emoji = {
        'TRENDING': '^',
        'MEAN_REVERTING': '~',
        'RANDOM_WALK': '-',
        'UNKNOWN': '?'
    }.get(conditions.regime, '?')

    trend_emoji = {
        'UP': '+',
        'DOWN': '-',
        'NEUTRAL': '='
    }.get(conditions.trend_direction, '=')

    print(
        f"{conditions.symbol:12} | "
        f"Regime:{regime_emoji} H:{conditions.hurst_value:.2f} | "
        f"Trend:{trend_emoji} V:{conditions.kalman_velocity:+.3f} | "
        f"Z:{conditions.zscore:+.2f} | "
        f"Bias:{conditions.suggested_bias:7} ({conditions.confidence:.0%})"
    )


def create_regime_chart(hurst_series: np.ndarray,
                        dates: pd.DatetimeIndex) -> Any:
    """
    Create standalone regime visualization chart.

    Args:
        hurst_series: Array of Hurst values
        dates: Date index

    Returns:
        Plotly figure
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        raise ImportError("Plotly required. Install with: pip install plotly")

    fig = go.Figure()

    # Hurst line
    fig.add_trace(go.Scatter(
        x=dates,
        y=hurst_series,
        name='Hurst Exponent',
        line=dict(color='cyan', width=2)
    ))

    # Reference zones
    fig.add_hrect(y0=0, y1=0.4, fillcolor="red", opacity=0.15,
                  annotation_text="Mean-Reverting Zone")
    fig.add_hrect(y0=0.4, y1=0.6, fillcolor="gray", opacity=0.1,
                  annotation_text="Random Walk Zone")
    fig.add_hrect(y0=0.6, y1=1.0, fillcolor="green", opacity=0.15,
                  annotation_text="Trending Zone")

    fig.add_hline(y=0.5, line_dash="dash", line_color="white")

    fig.update_layout(
        template='plotly_dark',
        title='Market Regime Detection (Hurst Exponent)',
        yaxis_title='Hurst Exponent',
        yaxis_range=[0, 1],
        height=400
    )

    return fig


def create_zscore_chart(zscore_series: np.ndarray,
                        dates: pd.DatetimeIndex,
                        prices: np.ndarray) -> Any:
    """
    Create Z-Score visualization with price overlay.

    Args:
        zscore_series: Array of Z-Score values
        dates: Date index
        prices: Price array

    Returns:
        Plotly figure
    """
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        raise ImportError("Plotly required. Install with: pip install plotly")

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=[0.6, 0.4]
    )

    # Price
    fig.add_trace(go.Scatter(
        x=dates, y=prices, name='Price',
        line=dict(color='white', width=1)
    ), row=1, col=1)

    # Z-Score
    colors = ['green' if z < -2 else 'red' if z > 2 else 'orange'
              for z in zscore_series]

    fig.add_trace(go.Scatter(
        x=dates, y=zscore_series, name='Z-Score',
        line=dict(color='orange', width=1.5)
    ), row=2, col=1)

    # Reference lines
    fig.add_hline(y=2, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=-2, line_dash="dash", line_color="green", row=2, col=1)
    fig.add_hline(y=0, line_color="gray", row=2, col=1)

    fig.update_layout(
        template='plotly_dark',
        title='Statistical Position (Z-Score)',
        height=500
    )

    return fig


def generate_report(conditions: MarketConditions,
                    output_format: str = 'text') -> str:
    """
    Generate analysis report in various formats.

    Args:
        conditions: MarketConditions from analysis
        output_format: 'text', 'markdown', or 'json'

    Returns:
        Formatted report string
    """
    if output_format == 'json':
        import json
        return json.dumps(conditions.to_dict(), indent=2, default=str)

    elif output_format == 'markdown':
        return f"""# Market Analysis: {conditions.symbol}

**Timestamp:** {conditions.timestamp}

## Regime Analysis
- **Current Regime:** {conditions.regime}
- **Hurst Exponent:** {conditions.hurst_value:.3f}
- **Confidence:** {conditions.regime_confidence:.0%}
- **Description:** {conditions.regime_description}

## Trend Analysis
| Metric | Value |
|--------|-------|
| Current Price | {conditions.current_price:.2f} |
| Kalman Price | {conditions.kalman_price:.2f} |
| Velocity | {conditions.kalman_velocity:.4f} |
| Direction | {conditions.trend_direction} |

## Statistical Position
- **Z-Score:** {conditions.zscore:.2f}
- **Percentile:** {conditions.percentile:.0f}%
- **Condition:** {conditions.statistical_condition}

## Volume Analysis
- **Delta %:** {conditions.volume_delta_pct:.1f}%
- **Cumulative Trend:** {conditions.cumulative_delta_trend}
- **Relative Volume:** {conditions.relative_volume:.2f}x

## Key Levels
- **POC:** {conditions.poc:.2f}
- **Value Area:** {conditions.value_area_low:.2f} - {conditions.value_area_high:.2f}

## Actionable Insights
- **Suggested Bias:** {conditions.suggested_bias}
- **Confidence:** {conditions.confidence:.0%}
- **Pullback Probability:** {conditions.pullback_probability:.0%}
- **Continuation Probability:** {conditions.trend_continuation_probability:.0%}

### Notes
{chr(10).join('- ' + note for note in conditions.notes)}
"""

    else:  # text
        return str(conditions)


def save_dashboard(fig: Any,
                   filepath: str,
                   format: str = 'html') -> None:
    """
    Save dashboard to file.

    Args:
        fig: Plotly figure
        filepath: Output file path
        format: 'html', 'png', 'pdf', or 'svg'
    """
    if format == 'html':
        fig.write_html(filepath)
    else:
        fig.write_image(filepath)

    print(f"Dashboard saved to: {filepath}")
