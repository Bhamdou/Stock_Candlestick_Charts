import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import yfinance as yf
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Calculate RSI
def calculate_rsi(data, window):
    delta = data['Close'].diff()
    up_days = delta.copy()
    up_days[delta<=0]=0.0
    down_days = abs(delta.copy())
    down_days[delta>0]=0.0
    RS_up = up_days.rolling(window).mean()
    RS_down = down_days.rolling(window).mean()
    rsi= 100-100/(1+RS_up/RS_down)
    return rsi

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Input(id='my_ticker', type='text', value='AAPL'),
    dcc.Checklist(id="checklist",
                  options=[
                      {'label': x, 'value': x} 
                      for x in ['20', '50', '100', '200']
                  ],
                  value=['20', '50']
                  ),
    dcc.Checklist(id="rsi-check",
                  options=[{'label': 'Include RSI', 'value': 'RSI'}],
                  value=[]
                  ),
    dcc.DatePickerRange(
        id='my-date-picker-range',
        min_date_allowed='2000-01-01',
        max_date_allowed='2025-12-31',
        start_date='2020-01-01',
        end_date='2023-01-01'
    ),
    dcc.Graph(id='my_graph')
])

@app.callback(
    Output(component_id='my_graph', component_property='figure'),
    [Input(component_id='my_ticker', component_property='value'),
     Input(component_id='checklist', component_property='value'),
     Input(component_id='rsi-check', component_property='value'),
     Input(component_id='my-date-picker-range', component_property='start_date'),
     Input(component_id='my-date-picker-range', component_property='end_date')]
)
def update_graph(ticker, moving_averages, include_rsi, start_date, end_date):
    data = yf.download(ticker, start_date, end_date)

    # calculate selected moving averages
    for ma in moving_averages:
        data[f'MA{ma}'] = data['Close'].rolling(window=int(ma)).mean()

    include_rsi = 'RSI' in include_rsi
    if include_rsi:
        data['RSI'] = calculate_rsi(data, 14)

    # Create subplot with 2 rows
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                        subplot_titles=('Stock Price', 'Volume', 'RSI' if include_rsi else ''))

    # Add candlestick chart and moving averages
    fig.add_trace(go.Candlestick(x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close']), row=1, col=1)
    
    colors = ['blue', 'red', 'green', 'purple']
    for i, ma in enumerate(moving_averages):
        fig.add_trace(go.Scatter(x=data.index, y=data[f'MA{ma}'], line=dict(color=colors[i % 4], width=0.7), name=f'MA {ma}'), row=1, col=1)

    # Add volume bar chart
    fig.add_trace(go.Bar(x=data.index, y=data['Volume']), row=2, col=1)
    
    # Add RSI
    if include_rsi:
        fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], line=dict(color='black', width=0.7), name='RSI'), row=3, col=1)
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
